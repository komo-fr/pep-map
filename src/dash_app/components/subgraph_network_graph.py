"""サブグラフネットワークグラフ構築モジュール"""

import networkx as nx

from src.dash_app.utils.constants import (
    DEFAULT_STATUS_COLOR,
    STATUS_COLOR_MAP,
    TEXT_OUTLINE_COLOR,
    TEXT_OUTLINE_WIDTH,
)
from src.dash_app.utils.data_loader import (
    load_subgraph,
    load_subgraph_metrics,
)


# モジュールレベル定数（network_graph.pyと同じ値）
PAGERANK_MULTIPLIER = 2000.0


def _calculate_node_size_pagerank(pagerank: float) -> float:
    """
    PageRankに基づいてノードサイズを計算する

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

    Args:
        pagerank: PageRank値（0-1）

    Returns:
        float: フォントサイズ（ピクセル）
    """
    min_font_size = 6.0
    max_font_size = 24.0
    if pagerank <= 0:
        return min_font_size
    scaled_value = pagerank * PAGERANK_MULTIPLIER
    font_size = min_font_size + 2.0 * (scaled_value**0.7)
    return min(font_size, max_font_size)


def _calculate_node_positions(subgraph: nx.DiGraph) -> dict[int, tuple[float, float]]:
    """
    サブグラフ内のノード座標を計算する

    Args:
        subgraph: NetworkX DiGraph

    Returns:
        dict[int, tuple[float, float]]: PEP番号をキー、(x, y)座標を値とする辞書
    """
    if len(subgraph.nodes()) == 0:
        return {}

    # spring_layoutで座標を計算
    pos = nx.spring_layout(
        subgraph,
        threshold=1e-6,
        k=1,  # ノード間の理想的な距離
        seed=42,  # 再現性のため
        scale=500,  # 座標のスケール
    )

    # 座標を変換（NetworkXは{node: array([x, y])}形式）
    positions = {}
    for node, coords in pos.items():
        positions[node] = (float(coords[0]), float(coords[1]))

    return positions


def build_subgraph_cytoscape_elements(group_id: int) -> list[dict] | None:
    """
    指定されたグループIDのサブグラフからCytoscape用elementsを構築する

    Args:
        group_id: グループID

    Returns:
        list[dict]: Cytoscape elementsのリスト(ノードとエッジ)、
                    データが存在しない場合はNone
    """
    # サブグラフを読み込む
    subgraph = load_subgraph(group_id)
    if subgraph is None:
        return None

    # メトリクスを読み込む
    metrics_df = load_subgraph_metrics(group_id)
    if metrics_df is None:
        return None

    # PageRankの辞書を作成
    pagerank_dict = dict(zip(metrics_df["PEP"], metrics_df["pagerank_group"]))

    # ステータスの辞書を作成
    status_dict = dict(zip(metrics_df["PEP"], metrics_df["status"]))

    # 座標を計算
    positions = _calculate_node_positions(subgraph)

    elements = []

    # ノードを生成
    for node in subgraph.nodes():
        pep_number = node
        pagerank = pagerank_dict.get(pep_number, 0.0)
        if pagerank is None:
            pagerank = 0.0

        # ステータスと色を取得
        status = status_dict.get(pep_number, "")
        if status is None:
            status = ""
        color = STATUS_COLOR_MAP.get(status, DEFAULT_STATUS_COLOR)

        # 座標を取得
        pos = positions.get(pep_number, (0, 0))

        # サイズを計算
        size_pagerank = _calculate_node_size_pagerank(pagerank)
        font_size_pagerank = _calculate_font_size_pagerank(pagerank)

        node_data = {
            "data": {
                "id": f"pep_{pep_number}",
                "label": str(pep_number),
                "pep_number": pep_number,
                "color": color,
                "status": status,
                "pagerank": pagerank,
                "size_pagerank": size_pagerank,
                "font_size_pagerank": font_size_pagerank,
            },
            "position": {"x": pos[0], "y": pos[1]},
        }
        elements.append(node_data)

    # エッジを生成
    for source, target in subgraph.edges():
        # 自己ループは除外
        if source == target:
            continue

        edge_data = {
            "data": {
                "id": f"edge_{source}_{target}",
                "source": f"pep_{source}",
                "target": f"pep_{target}",
            }
        }
        elements.append(edge_data)

    return elements


def get_subgraph_base_stylesheet() -> list[dict]:
    """
    サブグラフ用の基本スタイルシートを返す

    Returns:
        list[dict]: Cytoscapeスタイルシート
    """
    return [
        # ノード基本スタイル
        {
            "selector": "node",
            "style": {
                "label": "data(label)",
                "background-color": "data(color)",
                "width": "data(size_pagerank)",
                "height": "data(size_pagerank)",
                "font-size": "data(font_size_pagerank)",
                "text-valign": "center",
                "text-halign": "center",
                "border-width": 1,
                "border-color": "#999",
                "opacity": 0.9,
                "text-outline-width": TEXT_OUTLINE_WIDTH,
                "text-outline-color": TEXT_OUTLINE_COLOR,
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
                "opacity": 0.6,
            },
        },
        # ノード選択時のスタイル
        {
            "selector": ":selected",
            "style": {
                "border-width": 4,
                "border-color": "#FF0000",
                "z-index": 9999,
                "opacity": 1,
            },
        },
    ]


def get_subgraph_layout_options() -> dict:
    """
    サブグラフ用のレイアウト設定を返す

    Returns:
        dict: Cytoscapeレイアウト設定
    """
    return {
        "name": "preset",  # 事前計算済み座標を使用
        "fit": True,  # グラフを画面に収める
        "padding": 30,  # 余白
    }
