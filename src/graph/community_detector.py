"""
コミュニティ検出モジュール

PEP引用ネットワークに対するLouvain法によるコミュニティ検出と分析機能を提供する。
"""

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

logger = logging.getLogger(__name__)


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
