"""
コミュニティ検出モジュール

PEP引用ネットワークに対するLouvain法によるコミュニティ検出と分析機能を提供する。
"""

import json
import logging
import pickle
import shutil
from typing import Any, Mapping
from pathlib import Path
from typing import cast

import matplotlib

matplotlib.use("Agg")  # ヘッドレス環境用のバックエンド設定

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from networkx.algorithms import community

from src.dash_app.utils.constants import STATUS_COLOR_MAP, DEFAULT_STATUS_COLOR
from src.graph.layout import calculate_full_network_positions

logger = logging.getLogger(__name__)

# 全体ネットワークハイライト画像用の定数
HIGHLIGHT_COLOR = "#D32F2F"  # ハイライト対象グループのノード色（濃い赤）
HIGHLIGHT_EDGE_COLOR = "#1976D2"  # ハイライト対象グループのエッジ色（青）
NON_HIGHLIGHT_COLOR = "#CCCCCC"  # 他グループのノード色（灰色）
NON_HIGHLIGHT_EDGE_COLOR = "#E0E0E0"  # 他グループのエッジ色（薄いグレー）
PAGERANK_MULTIPLIER = 2000.0  # PageRankスケーリング係数


def save_full_network_positions(
    G: nx.DiGraph,
    output_path: Path,
) -> Path:
    """
    全体ネットワークのノード座標を計算してJSONで保存する

    Args:
        G: NetworkX DiGraph
        output_path: 出力先のJSONファイルパス

    Returns:
        保存したファイルのパス
    """
    logger.info(f"Calculating and saving full network positions to {output_path}")

    # 座標を計算
    positions = calculate_full_network_positions(G)

    # JSON形式に変換（キーを文字列に）
    positions_json = {str(node): list(pos) for node, pos in positions.items()}

    # 保存
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(positions_json, f, indent=2)

    logger.info(f"Saved {len(positions)} node positions")
    return output_path


def run_louvain_detection(
    G: nx.DiGraph, resolution: float = 4, seed: int = 42
) -> list[set]:
    """
    Louvain法によるコミュニティ検出を実行

    Args:
        G: NetworkX DiGraph
        resolution: 解像度パラメータ（大きいほど小さなコミュニティを検出）
        seed: 乱数シード

    Returns:
        コミュニティのリスト（サイズ降順でソート）
    """
    logger.info(f"Running Louvain detection with resolution={resolution}, seed={seed}")
    communities_result = community.louvain_communities(
        G, resolution=resolution, seed=seed
    )
    # サイズ降順でソート
    communities_sorted = sorted(communities_result, key=len, reverse=True)
    logger.info(f"Detected {len(communities_sorted)} communities")
    return communities_sorted


def create_pep_group_metrics(
    communities: list[set], G: nx.DiGraph, metadata_path: Path
) -> pd.DataFrame:
    """
    PEPごとのグループ情報とグループ内メトリクスを作成

    Args:
        communities: コミュニティのリスト
        G: NetworkX DiGraph
        metadata_path: peps_metadata.csvへのパス

    Returns:
        DataFrame with columns:
        - PEP, title, status, created, group_id
        - in-degree_group, out-degree_group, degree_group, pagerank_group
        孤立点（サイズ1のコミュニティ、グラフに存在しないPEP）は group_id=最大値のグループID+1
    """
    logger.info(f"Creating PEP group metrics from {metadata_path}")

    # メタデータを読み込み
    df_metadata = pd.read_csv(metadata_path)

    # グループ内メトリクスを計算
    pagerank_threshold = 2  # ローカルPageRank計算の最小グループサイズ
    results = []

    for group_id, comm in enumerate(communities):
        subgraph = cast(nx.DiGraph, G.subgraph(comm))
        is_isolated = len(comm) == 1

        # グループ内PageRankを計算（サイズ2以上のみ）
        local_pagerank: Mapping[str, float | None]
        if len(comm) >= pagerank_threshold:
            local_pagerank = nx.pagerank(subgraph)
        else:
            local_pagerank = {node: None for node in comm}

        for node in comm:
            results.append(
                {
                    "PEP": node,
                    "group_id": -1 if is_isolated else group_id,
                    "in-degree_group": subgraph.in_degree(node),
                    "out-degree_group": subgraph.out_degree(node),
                    "degree_group": subgraph.degree(node),
                    "pagerank_group": local_pagerank.get(node),
                }
            )

    df_metrics = pd.DataFrame(results)
    df_metrics["pagerank_cumsum"] = df_metrics.groupby("group_id")[
        "pagerank_group"
    ].cumsum()

    # メタデータとマージ
    df_metadata = df_metadata.rename(columns={"pep_number": "PEP"})
    df_merged = df_metadata[["PEP", "title", "status", "created"]].merge(
        df_metrics, on="PEP", how="left"
    )

    # group_idが-1のグループは最大値で置き換える
    isolated_peps_group_id = df_merged.group_id.max() + 1
    df_merged.loc[df_merged.group_id == -1, "group_id"] = isolated_peps_group_id
    df_merged["in-degree_group"] = df_merged["in-degree_group"].fillna(0).astype(int)
    df_merged["out-degree_group"] = df_merged["out-degree_group"].fillna(0).astype(int)
    df_merged["degree_group"] = df_merged["degree_group"].fillna(0).astype(int)

    # ソート: group_id順、その後pagerank_group降順
    df_merged = df_merged.sort_values(
        ["group_id", "pagerank_group"], ascending=[True, False]
    )

    logger.info(f"Created metrics for {len(df_merged)} PEPs")
    return df_merged


def create_group_metrics(communities: list[set], G: nx.DiGraph) -> pd.DataFrame:
    """
    グループごとのメトリクスを作成

    Args:
        communities: コミュニティのリスト
        G: NetworkX DiGraph

    Returns:
        DataFrame with columns: group_id, pep_count, density
        孤立点（サイズ1）は除外
    """
    logger.info("Creating group metrics")
    data_list = []

    for group_id, peps in enumerate(communities):
        if len(peps) == 1:
            continue  # 孤立点は除外
        subgraph = G.subgraph(peps)
        data_list.append(
            {
                "group_id": group_id,
                "pep_count": len(peps),
                "density": nx.density(subgraph),
            }
        )

    df = pd.DataFrame(data_list)
    logger.info(f"Created metrics for {len(df)} groups (excluding isolated nodes)")
    return df


def calculate_detection_stats(communities: list[set], G: nx.DiGraph) -> dict:
    """
    コミュニティ検出の統計情報を計算

    Args:
        communities: コミュニティのリスト
        G: NetworkX DiGraph

    Returns:
        統計情報の辞書:
        - modularity: モジュラリティ
        - total_communities: 総コミュニティ数
        - total_peps_in_communities: コミュニティに所属するPEP数（孤立点除く）
        - isolated_peps: 孤立点の数
        - max_community_size, min_community_size, avg_community_size
    """
    logger.info("Calculating detection stats")

    # モジュラリティを計算
    mod = community.modularity(G, communities)

    # サイズ統計
    sizes = [len(c) for c in communities]
    non_isolated_sizes = [s for s in sizes if s > 1]
    isolated_count = sum(1 for s in sizes if s == 1)

    stats = {
        "modularity": mod,
        "total_communities": len(communities),
        "total_peps_in_communities": sum(non_isolated_sizes),
        "isolated_peps": isolated_count,
        "max_community_size": max(non_isolated_sizes) if non_isolated_sizes else 0,
        "min_community_size": min(non_isolated_sizes) if non_isolated_sizes else 0,
        "avg_community_size": (
            sum(non_isolated_sizes) / len(non_isolated_sizes)
            if non_isolated_sizes
            else 0
        ),
    }

    logger.info(f"Stats: {stats}")
    return stats


def calculate_grid_layout(subgraph: nx.Graph) -> dict[int, tuple[float, float]]:
    """
    ノードを格子状に配置する（孤立点グループ用）

    Args:
        subgraph: NetworkX DiGraph

    Returns:
        dict[int, tuple[float, float]]: ノードをキー、(x, y)座標を値とする辞書
    """
    import math

    nodes = sorted(subgraph.nodes())  # PEP番号順にソート
    num_nodes = len(nodes)

    if num_nodes == 0:
        return {}

    # 列数を計算（正方形に近い形を目指す）
    num_cols = math.ceil(math.sqrt(num_nodes))

    positions = {}
    for i, node in enumerate(nodes):
        col = i % num_cols
        row = i // num_cols
        # 正規化された座標（0〜1の範囲）
        x = col / max(num_cols - 1, 1)
        y = row / max((num_nodes - 1) // num_cols, 1)
        positions[node] = (x, y)

    return positions


def _generate_subgraph_image(
    group_id: int, peps: set, G: nx.DiGraph, output_dir: Path
) -> Path:

    subgraph = G.subgraph(peps)
    # レイアウト計算（エッジがない場合は格子状に配置）
    pos: dict[Any, Any]
    if subgraph.number_of_edges() == 0:
        pos = calculate_grid_layout(subgraph)
    else:
        pos = nx.spring_layout(subgraph, threshold=1e-6, k=1, seed=42, scale=200)

    # ノードカラーを取得
    node_colors = []
    for n in subgraph.nodes():
        status = subgraph.nodes[n].get("status", "")
        color = STATUS_COLOR_MAP.get(status, DEFAULT_STATUS_COLOR)
        node_colors.append(color)

    # PageRankでノードサイズを計算
    pagerank = nx.pagerank(subgraph)
    node_sizes = [pagerank[node] * 20000 for node in subgraph.nodes()]

    # 描画
    plt.figure(figsize=(10, 10))
    nx.draw(
        subgraph,
        pos,
        with_labels=False,
        node_size=node_sizes,
        node_color=node_colors,
        font_size=10,
        connectionstyle="arc3,rad=0.1",
    )

    # ラベルを白フチ付きで描画
    labels = nx.draw_networkx_labels(subgraph, pos, font_size=10)
    for text in labels.values():
        text.set_path_effects([pe.withStroke(linewidth=3, foreground="white")])

    # 保存
    image_path = output_dir / f"group_{group_id}.png"
    plt.savefig(image_path, dpi=100, bbox_inches="tight")
    plt.close()
    logger.debug(f"Saved {image_path}")
    return image_path


def generate_subgraph_images(
    communities: list[set], G: nx.DiGraph, output_dir: Path
) -> list[Path]:
    """
    各コミュニティのサブグラフ画像を生成

    Args:
        communities: コミュニティのリスト
        G: NetworkX DiGraph（ノードにstatus属性が必要）
        output_dir: 出力ディレクトリ
        status_color_map: ステータスから色へのマッピング

    Returns:
        生成した画像ファイルのパスのリスト
        孤立点（サイズ1）のコミュニティは画像を生成しない
    """
    logger.info(f"Generating subgraph images to {output_dir}")

    # 既存のディレクトリを削除してから再作成（古いグループのファイルを残さないため）
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_paths = []
    isolated_peps = set[int]()
    count = 0
    for group_id, peps in enumerate(communities):
        if len(peps) == 1:
            isolated_peps = isolated_peps | peps
            continue

        image_path = _generate_subgraph_image(group_id, peps, G, output_dir)
        generated_paths.append(image_path)
        count += 1

    # 孤立点グループのIDは非孤立コミュニティの数（= count）とする
    # 注意: save_subgraphs() でも同一ロジックを使用しているため、変更時は両方を更新すること
    if isolated_peps:
        image_path = _generate_subgraph_image(count, isolated_peps, G, output_dir)
        generated_paths.append(image_path)

    logger.info(f"Generated {len(generated_paths)} images")
    return generated_paths


def save_subgraphs(
    communities: list[set],
    G: nx.DiGraph,
    output_dir: Path,
) -> list[Path]:
    """
    各コミュニティのサブグラフをpickle形式で保存

    Args:
        communities: コミュニティのリスト
        G: NetworkX DiGraph
        output_dir: 出力ディレクトリ

    Returns:
        保存したファイルのパスのリスト
        孤立点（サイズ1）のコミュニティは保存しない
    """
    logger.info(f"Saving subgraphs to {output_dir}")

    # 既存のディレクトリを削除してから再作成（古いグループのファイルを残さないため）
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    saved_paths = []
    isolated_peps = set[int]()
    count = 0
    for group_id, peps in enumerate(communities):
        if len(peps) == 1:
            isolated_peps = isolated_peps | peps
            continue

        subgraph = G.subgraph(peps).copy()  # コピーして独立したグラフにする

        # 保存
        graph_path = output_dir / f"subgraph_{group_id}.pkl"
        with open(graph_path, "wb") as f:
            pickle.dump(subgraph, f)

        saved_paths.append(graph_path)
        logger.debug(f"Saved {graph_path}")
        count += 1
    # 孤立点グループのIDは非孤立コミュニティの数（= count）とする
    # 注意: generate_subgraph_images() でも同一ロジックを使用しているため、変更時は両方を更新すること
    if isolated_peps:
        group_id = count
        subgraph = G.subgraph(isolated_peps).copy()
        # 保存
        graph_path = output_dir / f"subgraph_{group_id}.pkl"
        with open(graph_path, "wb") as f:
            pickle.dump(subgraph, f)

        saved_paths.append(graph_path)
        logger.debug(f"Saved {graph_path}")

    logger.info(f"Saved {len(saved_paths)} subgraphs")
    return saved_paths


def _calculate_subgraph_positions(
    subgraph: nx.Graph,
) -> dict[int, tuple[float, float]]:
    """
    サブグラフ内のノード座標を計算する

    Args:
        subgraph: NetworkX Graph

    Returns:
        dict[int, tuple[float, float]]: PEP番号をキー、(x, y)座標を値とする辞書
    """
    if len(subgraph.nodes()) == 0:
        return {}

    # エッジがない場合（孤立点のみ）は格子状に配置
    # 孤立点はエッジがないため広めの間隔で配置（scale=400）
    if subgraph.number_of_edges() == 0:
        return {
            node: (coords[0] * 400, coords[1] * 400)
            for node, coords in calculate_grid_layout(subgraph).items()
        }

    # spring_layoutで座標を計算
    pos = nx.spring_layout(
        subgraph,
        threshold=1e-6,
        k=1,
        seed=42,
        scale=200,
    )

    # 座標を変換（NetworkXは{node: array([x, y])}形式）
    return {node: (float(coords[0]), float(coords[1])) for node, coords in pos.items()}


def save_subgraph_positions(
    communities: list[set],
    G: nx.DiGraph,
    output_dir: Path,
) -> list[Path]:
    """
    各コミュニティのサブグラフ座標をJSON形式で保存する

    Args:
        communities: コミュニティのリスト
        G: NetworkX DiGraph
        output_dir: 出力ディレクトリ

    Returns:
        保存したファイルのパスのリスト
    """
    logger.info(f"Saving subgraph positions to {output_dir}")

    # 既存のディレクトリを削除してから再作成
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    saved_paths = []
    isolated_peps: set[int] = set()
    count = 0

    for group_id, peps in enumerate(communities):
        if len(peps) == 1:
            isolated_peps = isolated_peps | peps
            continue

        subgraph = G.subgraph(peps)
        positions = _calculate_subgraph_positions(subgraph)

        # JSON形式に変換（キーを文字列に）
        positions_json = {str(node): list(pos) for node, pos in positions.items()}

        # 保存
        json_path = output_dir / f"group_{group_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(positions_json, f, indent=2)

        saved_paths.append(json_path)
        logger.debug(f"Saved {json_path}")
        count += 1

    # 孤立点グループ
    if isolated_peps:
        group_id = count
        subgraph = G.subgraph(isolated_peps)
        positions = _calculate_subgraph_positions(subgraph)

        positions_json = {str(node): list(pos) for node, pos in positions.items()}

        json_path = output_dir / f"group_{group_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(positions_json, f, indent=2)

        saved_paths.append(json_path)
        logger.debug(f"Saved {json_path}")

    logger.info(f"Saved {len(saved_paths)} subgraph position files")
    return saved_paths


def save_group_csvs(
    pep_group_df: pd.DataFrame,
    output_dir: Path,
) -> list[Path]:
    """
    グループごとのPEP情報をCSV形式で保存

    Args:
        pep_group_df: create_pep_group_metricsで作成したDataFrame
        output_dir: 出力ディレクトリ

    Returns:
        保存したファイルのパスのリスト
    """
    logger.info(f"Saving group CSVs to {output_dir}")

    # 既存のディレクトリを削除してから再作成（古いグループのファイルを残さないため）
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    saved_paths = []

    for group_id in pep_group_df["group_id"].unique():
        group_df = pep_group_df[pep_group_df["group_id"] == group_id]
        csv_path = output_dir / f"group_{group_id}.csv"
        group_df.to_csv(csv_path, index=False)

        saved_paths.append(csv_path)
        logger.debug(f"Saved {csv_path}")

    logger.info(f"Saved {len(saved_paths)} group CSVs")
    return saved_paths


def _calculate_node_size_pagerank_matplotlib(
    pagerank: float, scale: float = 0.5
) -> float:
    """
    PageRankに基づいてmatplotlib用ノードサイズを計算する

    matplotlibのnode_sizeは面積（平方ポイント）として解釈されるため、
    Cytoscapeのサイズ（直径）とは異なるスケーリングを適用する。

    Args:
        pagerank: PageRank値（0-1）
        scale: スケール係数（デフォルト0.5、figsize=(20,20)用）
               figsize=(10,10)の場合は0.125を指定

    Returns:
        matplotlib用ノードサイズ（面積）
    """
    base_min_size = 100.0
    if pagerank <= 0:
        return base_min_size * (scale / 0.5)  # スケールに応じて最小サイズも調整
    # Cytoscapeサイズ: 10.0 * ((pagerank * 2000.0) ** 0.5)
    # matplotlib用: そのサイズを面積として扱う
    cytoscape_size = 10.0 * ((pagerank * PAGERANK_MULTIPLIER) ** 0.5)
    # matplotlibではnode_sizeは面積なので、直径を2乗してスケール調整
    return cytoscape_size**2 * scale


def _generate_full_network_highlight_image(
    group_id: int,
    highlight_peps: set[int],
    G: nx.DiGraph,
    positions: dict[int, tuple[float, float]],
    pagerank: dict[int, float],
    output_dir: Path,
) -> Path:
    """
    全体ネットワーク図で指定グループをハイライトした画像を生成する

    ハイライト対象のノード/エッジを最前面に描画するため、
    描画順序を制御している（後に描画したものが前面に表示される）。

    Args:
        group_id: グループID
        highlight_peps: ハイライト対象のPEP番号の集合
        G: 全体のNetworkXグラフ
        positions: 全ノードの座標（事前計算済み）
        pagerank: 全ノードのPageRank値（事前計算済み）
        output_dir: 出力ディレクトリ

    Returns:
        生成された画像ファイルのパス
    """
    # ノードを分類
    non_highlight_nodes = [n for n in G.nodes() if n not in highlight_peps]
    highlight_nodes = [n for n in G.nodes() if n in highlight_peps]

    # エッジを分類（両端がハイライト対象の場合のみハイライトエッジ）
    non_highlight_edges = [
        (u, v)
        for u, v in G.edges()
        if not (u in highlight_peps and v in highlight_peps)
    ]
    highlight_edges = [
        (u, v) for u, v in G.edges() if u in highlight_peps and v in highlight_peps
    ]

    # ノードサイズを計算（figsize=(10,10)用にscale=0.125を指定）
    node_size_scale = 0.125
    non_highlight_sizes = [
        _calculate_node_size_pagerank_matplotlib(
            pagerank.get(n, 0), scale=node_size_scale
        )
        for n in non_highlight_nodes
    ]
    highlight_sizes = [
        _calculate_node_size_pagerank_matplotlib(
            pagerank.get(n, 0), scale=node_size_scale
        )
        for n in highlight_nodes
    ]

    # 描画（zorderで明示的にレイヤーを制御）
    # zorder: 大きいほど前面に表示
    ZORDER_NON_HIGHLIGHT_EDGE = 1
    ZORDER_NON_HIGHLIGHT_NODE = 2
    ZORDER_HIGHLIGHT_EDGE = 3
    ZORDER_HIGHLIGHT_NODE = 4
    ZORDER_LABEL = 5

    plt.figure(figsize=(10, 10))

    # 1. 非ハイライトエッジ（薄いグレー）- 最背面
    if non_highlight_edges:
        edge_collection = nx.draw_networkx_edges(
            G,
            positions,
            edgelist=non_highlight_edges,
            edge_color=NON_HIGHLIGHT_EDGE_COLOR,
            arrows=True,
            arrowsize=5,
            connectionstyle="arc3,rad=0.1",
        )
        if edge_collection is not None:
            for patch in edge_collection:
                patch.set_zorder(ZORDER_NON_HIGHLIGHT_EDGE)

    # 2. 非ハイライトノード（灰色）
    if non_highlight_nodes:
        node_collection = nx.draw_networkx_nodes(
            G,
            positions,
            nodelist=non_highlight_nodes,
            node_size=non_highlight_sizes,
            node_color=NON_HIGHLIGHT_COLOR,
        )
        if node_collection is not None:
            node_collection.set_zorder(ZORDER_NON_HIGHLIGHT_NODE)

    # 3. ハイライトエッジ（青色）- 非ハイライトノードより前面
    if highlight_edges:
        edge_collection = nx.draw_networkx_edges(
            G,
            positions,
            edgelist=highlight_edges,
            edge_color=HIGHLIGHT_EDGE_COLOR,
            arrows=True,
            arrowsize=5,
            connectionstyle="arc3,rad=0.1",
        )
        if edge_collection is not None:
            for patch in edge_collection:
                patch.set_zorder(ZORDER_HIGHLIGHT_EDGE)

    # 4. ハイライトノード（赤色）- 最前面
    if highlight_nodes:
        node_collection = nx.draw_networkx_nodes(
            G,
            positions,
            nodelist=highlight_nodes,
            node_size=highlight_sizes,
            node_color=HIGHLIGHT_COLOR,
        )
        if node_collection is not None:
            node_collection.set_zorder(ZORDER_HIGHLIGHT_NODE)

    # 5. ハイライト対象のみラベルを描画（白フチ付き）
    highlight_labels = {node: str(node) for node in highlight_peps}
    highlight_positions = {
        node: positions[node] for node in highlight_peps if node in positions
    }
    labels = nx.draw_networkx_labels(
        G,
        highlight_positions,
        labels=highlight_labels,
        font_size=6,
    )
    for text in labels.values():
        text.set_path_effects([pe.withStroke(linewidth=1, foreground="white")])
        text.set_zorder(ZORDER_LABEL)

    # 軸を非表示
    plt.axis("off")

    # 保存
    image_path = output_dir / f"full_group_{group_id}.png"
    plt.savefig(image_path, dpi=100, bbox_inches="tight")
    plt.close()
    logger.debug(f"Saved {image_path}")
    return image_path


def generate_full_network_highlight_images(
    communities: list[set],
    G: nx.DiGraph,
    output_dir: Path,
) -> list[Path]:
    """
    全体ネットワーク図で各グループをハイライトした画像を生成する

    Args:
        communities: コミュニティのリスト（サイズ降順）
        G: 全体のNetworkXグラフ
        output_dir: 出力ディレクトリ

    Returns:
        生成された画像ファイルのパスのリスト
    """
    logger.info(f"Generating full network highlight images to {output_dir}")

    # 既存のディレクトリを削除してから再作成
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 座標とPageRankを事前計算（全グループで共通）
    positions = calculate_full_network_positions(G)
    pagerank = nx.pagerank(G)

    generated_paths = []
    isolated_peps: set[int] = set()
    count = 0

    for group_id, peps in enumerate(communities):
        if len(peps) == 1:
            # 孤立点は後でまとめて処理
            isolated_peps = isolated_peps | peps
            continue

        image_path = _generate_full_network_highlight_image(
            group_id, peps, G, positions, pagerank, output_dir
        )
        generated_paths.append(image_path)
        count += 1

    # 孤立点グループ
    if isolated_peps:
        image_path = _generate_full_network_highlight_image(
            count, isolated_peps, G, positions, pagerank, output_dir
        )
        generated_paths.append(image_path)

    logger.info(f"Generated {len(generated_paths)} full network highlight images")
    return generated_paths
