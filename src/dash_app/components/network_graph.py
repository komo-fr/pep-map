"""ネットワークグラフ構築モジュール"""

import networkx as nx
import pandas as pd

from src.dash_app.utils.constants import DEFAULT_STATUS_COLOR, STATUS_COLOR_MAP
from src.dash_app.utils.data_loader import (
    load_citations,
    load_peps_metadata,
    load_node_metrics,
)


# モジュールレベル定数
PAGERANK_MULTIPLIER = 2000.0  # PageRankをノードサイズ・フォントサイズに変換する係数

# モジュールレベルでキャッシュ（アプリ起動時に一度だけ計算する）
_cytoscape_elements_cache: list[dict] | None = None
_valid_edges_cache: tuple[set[int], "pd.DataFrame"] | None = None


def _load_valid_edges_df() -> tuple[set[int], "pd.DataFrame"]:
    """
    PEPメタデータと引用データを読み込み、有効なエッジのDataFrameと存在するPEP番号のセットを返す。

    有効なエッジ: 自己ループでなく、citing/citedがともに存在するPEP番号であるもの。
    データ読み込み・有効エッジの計算を一箇所に集約し、重複と修正漏れを防ぐ。

    初回呼び出し時に計算し、以降はキャッシュを返す。

    Returns:
        tuple[set[int], pd.DataFrame]: (存在するPEP番号のセット, 有効なエッジのみのDataFrame)
    """
    global _valid_edges_cache

    if _valid_edges_cache is not None:
        return _valid_edges_cache

    peps_df = load_peps_metadata()
    citations_df = load_citations()
    existing_peps = set(peps_df["pep_number"].tolist())
    valid = (
        (citations_df["citing"] != citations_df["cited"])
        & citations_df["citing"].isin(existing_peps)
        & citations_df["cited"].isin(existing_peps)
    )
    edges_df = citations_df.loc[valid, ["citing", "cited"]]

    _valid_edges_cache = (existing_peps, edges_df)
    return _valid_edges_cache


def build_cytoscape_elements() -> list[dict]:
    """
    PEPメタデータと引用関係からCytoscape用のelementsを構築する

    初回呼び出し時に計算し、以降はキャッシュを返す。

    Returns:
        list[dict]: Cytoscape elementsのリスト(ノードとエッジ)
    """
    global _cytoscape_elements_cache

    if _cytoscape_elements_cache is not None:
        return _cytoscape_elements_cache

    elements = []

    # ノードを生成
    nodes = _build_nodes()
    elements.extend(nodes)

    # エッジを生成
    edges = _build_edges()
    elements.extend(edges)

    _cytoscape_elements_cache = elements
    return elements


def _calculate_node_positions() -> dict[int, tuple[float, float]]:
    """
    NetworkXを使用してノードの座標を計算する

    孤立ノード(引用関係がないPEP)は左上にグリッド配置し、
    引用関係のあるノードは中央にspring_layoutで配置する。

    Returns:
        dict[int, tuple[float, float]]: PEP番号をキー、(x, y)座標を値とする辞書
    """
    existing_peps, edges_df = _load_valid_edges_df()

    # エッジリストから有向グラフを構築 (from_pandas_edgelist で一括追加)
    G = nx.from_pandas_edgelist(
        edges_df,
        source="citing",
        target="cited",
        create_using=nx.DiGraph,
    )

    # 孤立点(エッジに現れないPEP)をノードとして追加
    G.add_nodes_from(existing_peps)

    # 孤立ノードと引用関係のあるノードを分離
    isolated_nodes = [node for node in G.nodes() if G.degree(node) == 0]
    connected_nodes = [node for node in G.nodes() if G.degree(node) > 0]

    positions = {}

    # 引用関係のあるノードをspring_layoutで配置（先に計算してY座標の範囲を取得）
    if connected_nodes:
        # 引用関係のあるノードのみのサブグラフを作成
        subgraph = G.subgraph(connected_nodes)

        # 座標を計算(spring_layout = Fruchterman-Reingold力指向アルゴリズム)
        connected_positions = nx.spring_layout(
            subgraph,
            threshold=1e-6,
            k=500,  # ノード間の理想的な距離(大きいほど広がる)
            iterations=500,  # イテレーション回数
            seed=42,  # 乱数シード(再現性のため)
            scale=1000,  # 座標のスケール
            method="energy",  # 未指定でもノード数が多いため"energy"が適用されるが、明瞭さのため明示
            gravity=20,  # 重力の強さ
        )

        # connected_positionsをpositionsに追加(タプルに統一して型を揃える)
        positions.update(
            {n: (float(p[0]), float(p[1])) for n, p in connected_positions.items()}
        )

        # Y座標の範囲を取得
        y_values = [positions[n][1] for n in connected_nodes]
        y_min = min(y_values)
        y_max = max(y_values)
    else:
        # 引用関係のあるノードがない場合のデフォルト範囲
        y_min = -500
        y_max = 500

    # 孤立ノードを左端に3列で配置
    if isolated_nodes:
        isolated_nodes_sorted = sorted(isolated_nodes)  # PEP番号順にソート
        num_cols = 3  # 列数
        col_spacing = 40  # 列間の間隔

        # 非孤立ノードのX座標最小値を取得（基準点）
        if connected_nodes:
            connected_x_coords = [positions[n][0] for n in connected_nodes]
            min_connected_x = min(connected_x_coords)
            # 孤立ノードを非孤立ノードより左側に配置（100ピクセル左に）
            x_start = min_connected_x - 100
        else:
            # 非孤立ノードがない場合はデフォルト値
            x_start = -700

        # 各列の行数を計算
        num_nodes = len(isolated_nodes_sorted)
        nodes_per_col = (num_nodes + num_cols - 1) // num_cols  # 切り上げ除算

        # Y座標の範囲内で均等に配置
        y_range = y_max - y_min
        if nodes_per_col > 1:
            y_spacing = y_range / (nodes_per_col - 1)
        else:
            y_spacing = 0

        for i, node in enumerate(isolated_nodes_sorted):
            col = i // nodes_per_col  # 列番号
            row_index = i % nodes_per_col  # その列内での行番号

            x = x_start + col * col_spacing
            y = y_max - row_index * y_spacing

            positions[node] = (float(x), float(y))

    return positions


def _calculate_adjacency_info() -> dict[int, dict[str, list[str]]]:
    """
    各PEPノードの隣接情報を計算する

    Returns:
        dict[int, dict[str, list[str]]]: PEP番号をキー、隣接情報を値とする辞書
            隣接情報: {
                "adjacent_nodes": list[str],  # 隣接ノードのID一覧
                "incoming_edges": list[str],  # 入ってくるエッジのID一覧
                "outgoing_edges": list[str],  # 出ていくエッジのID一覧
            }
    """
    existing_peps, edges_df = _load_valid_edges_df()

    # 重複を除外（同じPEP間の複数回引用は1カウント）
    unique_edges_df = edges_df.drop_duplicates()

    # 隣接情報を初期化
    adjacency_info: dict[int, dict[str, list[str]]] = {
        pep_num: {
            "adjacent_nodes": [],
            "incoming_edges": [],
            "outgoing_edges": [],
        }
        for pep_num in existing_peps
    }

    # エッジを走査して隣接情報を構築
    for _, row in unique_edges_df.iterrows():
        citing = int(row["citing"])
        cited = int(row["cited"])
        edge_id = f"edge_{citing}_{cited}"

        # citing側: 出ていくエッジと隣接ノードを追加
        adjacency_info[citing]["outgoing_edges"].append(edge_id)
        if f"pep_{cited}" not in adjacency_info[citing]["adjacent_nodes"]:
            adjacency_info[citing]["adjacent_nodes"].append(f"pep_{cited}")

        # cited側: 入ってくるエッジと隣接ノードを追加
        adjacency_info[cited]["incoming_edges"].append(edge_id)
        if f"pep_{citing}" not in adjacency_info[cited]["adjacent_nodes"]:
            adjacency_info[cited]["adjacent_nodes"].append(f"pep_{citing}")

    return adjacency_info


def _calculate_node_size(degree: int) -> float:
    """
    次数に基づいてノードサイズを計算する

    面積が次数に比例するように、サイズは√次数に比例する。
    次数0の場合は最小サイズ7pxを返す。

    Args:
        degree: ノードの次数

    Returns:
        float: ノードサイズ（ピクセル）
    """
    if degree == 0:
        return 10
    return 10.0 * (degree**0.5)


def _calculate_font_size(degree: int) -> float:
    """
    次数に基づいてフォントサイズを計算する

    次数^0.7に比例して増加するが、最小サイズ以上、最大サイズ以下に制限される。
    次数0の場合は最小サイズを返す。

    Args:
        degree: ノードの次数

    Returns:
        float: フォントサイズ（ピクセル）
    """
    min_font_size = 6.0
    max_font_size = 24.0
    if degree == 0:
        return min_font_size
    # 次数^0.7に基づいてフォントサイズを計算（面積と直径の中間的な成長率）
    font_size = min_font_size + 2.0 * (degree**0.7)
    return min(font_size, max_font_size)


def _calculate_node_size_pagerank(pagerank: float) -> float:
    """
    PageRankに基づいてノードサイズを計算する

    PageRankは0-1の値なので、PAGERANK_MULTIPLIERでスケール変換してから平方根を取る。
    PageRankが0以下の場合は最小サイズを返す。

    Args:
        pagerank: PageRank値（0-1）

    Returns:
        float: ノードサイズ（ピクセル）
    """
    if pagerank <= 0:
        return 10.0
    return 10.0 * ((pagerank * PAGERANK_MULTIPLIER) ** 0.5)


def _calculate_font_size_pagerank(pagerank: float) -> float:
    """
    PageRankに基づいてフォントサイズを計算する

    PageRankは0-1の値なので、PAGERANK_MULTIPLIERでスケール変換してから0.7乗を取る。
    最小サイズ以上、最大サイズ以下に制限される。

    Args:
        pagerank: PageRank値（0-1）

    Returns:
        float: フォントサイズ（ピクセル）
    """
    min_font_size = 6.0
    max_font_size = 24.0
    if pagerank <= 0:
        return min_font_size
    # PageRank * PAGERANK_MULTIPLIERの0.7乗に基づいてフォントサイズを計算
    scaled_value = pagerank * PAGERANK_MULTIPLIER
    font_size = min_font_size + 2.0 * (scaled_value**0.7)
    return min(font_size, max_font_size)


def _build_nodes() -> list[dict]:
    """
    PEPメタデータからノードを生成する

    NetworkXで計算した座標とnode_metrics.csvから読み込んだメトリクス情報をノードに付与する。
    各次数タイプ（入次数/出次数/次数/一定/PageRank）に対応したサイズを事前計算する。

    Returns:
        list[dict]: ノードのリスト
    """
    peps_df = load_peps_metadata()

    # 座標を計算
    positions = _calculate_node_positions()

    # 隣接情報を計算
    adjacency_info = _calculate_adjacency_info()

    # メトリクスデータを読み込む（次数とPageRank）
    metrics_df = load_node_metrics()
    pagerank_dict = dict(zip(metrics_df["pep_number"], metrics_df["pagerank"]))
    in_degree_dict = dict(zip(metrics_df["pep_number"], metrics_df["in_degree"]))
    out_degree_dict = dict(zip(metrics_df["pep_number"], metrics_df["out_degree"]))
    total_degree_dict = dict(zip(metrics_df["pep_number"], metrics_df["degree"]))

    nodes = []

    for _, row in peps_df.iterrows():
        pep_number = row["pep_number"]
        status = row["status"]
        color = STATUS_COLOR_MAP.get(status, DEFAULT_STATUS_COLOR)

        # 座標を取得(存在しない場合はデフォルト値)
        pos = positions.get(pep_number, (0, 0))

        # メトリクス情報を取得（存在しない場合はデフォルト値0）
        in_degree = in_degree_dict.get(pep_number, 0)
        out_degree = out_degree_dict.get(pep_number, 0)
        total_degree = total_degree_dict.get(pep_number, 0)
        pagerank = pagerank_dict.get(pep_number, 0.0)

        # 各次数タイプに対応したノードサイズを計算
        size_in_degree = _calculate_node_size(in_degree)
        size_out_degree = _calculate_node_size(out_degree)
        size_total_degree = _calculate_node_size(total_degree)
        size_constant = 20.0  # 一定サイズ
        size_pagerank = _calculate_node_size_pagerank(pagerank)

        # 各次数タイプに対応したフォントサイズを計算
        font_size_in_degree = _calculate_font_size(in_degree)
        font_size_out_degree = _calculate_font_size(out_degree)
        font_size_total_degree = _calculate_font_size(total_degree)
        font_size_constant = 8.0  # 一定サイズの場合は最小値
        font_size_pagerank = _calculate_font_size_pagerank(pagerank)

        # 隣接情報を取得（存在しない場合はデフォルト値）
        adj_info = adjacency_info.get(
            pep_number,
            {"adjacent_nodes": [], "incoming_edges": [], "outgoing_edges": []},
        )

        node = {
            "data": {
                "id": f"pep_{pep_number}",
                "label": str(pep_number),
                "pep_number": pep_number,
                "color": color,
                "status": status,
                "in_degree": in_degree,
                "out_degree": out_degree,
                "total_degree": total_degree,
                "pagerank": pagerank,
                "size_in_degree": size_in_degree,
                "size_out_degree": size_out_degree,
                "size_total_degree": size_total_degree,
                "size_constant": size_constant,
                "size_pagerank": size_pagerank,
                "font_size_in_degree": font_size_in_degree,
                "font_size_out_degree": font_size_out_degree,
                "font_size_total_degree": font_size_total_degree,
                "font_size_constant": font_size_constant,
                "font_size_pagerank": font_size_pagerank,
                # 隣接情報（clientside_callback用）
                "adjacent_nodes": adj_info["adjacent_nodes"],
                "incoming_edges": adj_info["incoming_edges"],
                "outgoing_edges": adj_info["outgoing_edges"],
            },
            "position": {
                "x": pos[0],
                "y": pos[1],
            },
        }
        nodes.append(node)

    return nodes


def _build_edges() -> list[dict]:
    """
    引用関係からエッジを生成する

    引用元(citing)→ 引用先(cited)の方向でエッジを作成する。
    同じPEP間の複数回引用は1本のエッジにまとめる(countは無視)。

    Returns:
        list[dict]: エッジのリスト
    """
    citations_df = load_citations()
    peps_df = load_peps_metadata()

    # 存在するPEP番号のセットを作成(エッジのフィルタリング用)
    existing_peps = set(peps_df["pep_number"].tolist())

    edges = []
    seen_edges = set()  # 重複エッジ防止用

    for _, row in citations_df.iterrows():
        citing = row["citing"]
        cited = row["cited"]

        # 自己ループを除外
        if citing == cited:
            continue

        # 存在しないPEPへのエッジを除外
        if citing not in existing_peps or cited not in existing_peps:
            continue

        # 重複エッジを除外
        edge_key = (citing, cited)
        if edge_key in seen_edges:
            continue
        seen_edges.add(edge_key)

        edge = {
            "data": {
                "id": f"edge_{citing}_{cited}",
                "source": f"pep_{citing}",
                "target": f"pep_{cited}",
            }
        }
        edges.append(edge)

    return edges


def get_base_stylesheet(size_type: str = "in_degree") -> list[dict]:
    """
    Cytoscapeグラフの基本スタイルシートを取得する

    ハイライト用のCSSクラススタイルも含む。
    ノードサイズとフォントサイズは指定されたサイズタイプに基づいて動的に設定される。

    Args:
        size_type: ノードサイズのタイプ ("in_degree", "out_degree", "total_degree", "pagerank", "constant")

    Returns:
        list[dict]: スタイルシート定義のリスト
    """
    # サイズタイプに応じたデータフィールドを選択
    size_field_map = {
        "in_degree": "size_in_degree",
        "out_degree": "size_out_degree",
        "total_degree": "size_total_degree",
        "pagerank": "size_pagerank",
        "constant": "size_constant",
    }
    font_size_field_map = {
        "in_degree": "font_size_in_degree",
        "out_degree": "font_size_out_degree",
        "total_degree": "font_size_total_degree",
        "pagerank": "font_size_pagerank",
        "constant": "font_size_constant",
    }
    size_field = size_field_map.get(size_type, "size_in_degree")
    font_size_field = font_size_field_map.get(size_type, "font_size_in_degree")
    dark_status_text_color = "#CCCCCC"

    return [
        # ノード基本スタイル
        {
            "selector": "node",
            "style": {
                "label": "data(label)",
                "background-color": "data(color)",
                "width": f"data({size_field})",
                "height": f"data({size_field})",
                "font-size": f"data({font_size_field})",
                "text-valign": "center",
                "text-halign": "center",
                "border-width": 1,
                "border-color": "#999",
                "opacity": 0.5,
            },
        },
        # エッジ基本スタイル
        {
            "selector": "edge",
            "style": {
                "width": 2,
                "line-color": "#999",
                "target-arrow-color": "#999",
                "target-arrow-shape": "triangle",
                "arrow-scale": 1,
                "curve-style": "bezier",
                "opacity": 0.5,
            },
        },
        # === ハイライト用スタイル ===
        # Cytoscape組み込み:selectedセレクター（即時フィードバック用）
        {
            "selector": ":selected",
            "style": {
                "border-width": 4,
                "border-color": "#FF0000",
                "z-index": 9999,
                "opacity": 1,
            },
        },
        # 選択中ノード（赤い太枠）
        {
            "selector": ".selected",
            "style": {
                "border-width": 4,
                "border-color": "#FF0000",
                "z-index": 9999,
                "opacity": 1,
                "color": "#000000",
            },
        },
        # 選択中ノード - 暗い背景色のStatusはグレー文字
        {
            "selector": '.selected[status = "Rejected"]',
            "style": {
                "color": dark_status_text_color,
            },
        },
        {
            "selector": '.selected[status = "Superseded"]',
            "style": {
                "color": dark_status_text_color,
            },
        },
        {
            "selector": '.selected[status = "Withdrawn"]',
            "style": {
                "color": dark_status_text_color,
            },
        },
        {
            "selector": '.selected[status = "Deferred"]',
            "style": {
                "color": dark_status_text_color,
            },
        },
        # 接続ノード（太枠）
        {
            "selector": ".connected",
            "style": {
                "color": "#000000",
                "border-width": 1,
                "border-color": "#888",
                "opacity": 1,
            },
        },
        # 接続ノード - 暗い背景色のStatusはグレー文字
        {
            "selector": '.connected[status = "Rejected"]',
            "style": {
                "color": dark_status_text_color,
            },
        },
        {
            "selector": '.connected[status = "Superseded"]',
            "style": {
                "color": dark_status_text_color,
            },
        },
        {
            "selector": '.connected[status = "Withdrawn"]',
            "style": {
                "color": dark_status_text_color,
            },
        },
        {
            "selector": '.connected[status = "Deferred"]',
            "style": {
                "color": dark_status_text_color,
            },
        },
        # 入ってくるエッジ（橙色）
        {
            "selector": ".incoming-edge",
            "style": {
                "width": 2,
                "line-color": "#FF8C00",
                "target-arrow-color": "#FF8C00",
                "opacity": 1,
                "z-index": 9998,
            },
        },
        # 出ていくエッジ（青色）
        {
            "selector": ".outgoing-edge",
            "style": {
                "width": 2,
                "line-color": "#1E90FF",
                "target-arrow-color": "#1E90FF",
                "opacity": 1,
                "z-index": 9998,
            },
        },
        # 非接続（減衰）
        {
            "selector": ".faded",
            "style": {
                "opacity": 0.15,
            },
        },
    ]


def get_preset_layout_options() -> dict:
    """
    presetレイアウトのオプションを取得する

    presetレイアウトは事前計算された座標を使用するため、
    ブラウザ側でのレイアウト計算が不要で高速に描画される。

    Returns:
        dict: レイアウトオプション
    """
    return {
        "name": "preset",
        "fit": True,  # グラフを画面に収める
        "padding": 30,  # 余白
    }
