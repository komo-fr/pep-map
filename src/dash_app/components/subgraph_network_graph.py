"""サブグラフネットワークグラフ構築モジュール"""

from src.dash_app.utils.constants import (
    DEFAULT_STATUS_COLOR,
    STATUS_COLOR_MAP,
    TEXT_OUTLINE_COLOR,
    TEXT_OUTLINE_OPACITY,
    TEXT_OUTLINE_WIDTH,
)
from src.dash_app.utils.data_loader import (
    load_subgraph,
    load_subgraph_metrics,
    load_subgraph_positions,
)


# モジュールレベルでキャッシュ
_subgraph_elements_cache: dict[int, list[dict]] = {}

# モジュールレベル定数
# グループ内PageRankは全体グラフより約50倍大きいため、専用の係数を使用
# 全体グラフ: pagerank 0.0004〜0.018、グループ内: pagerank_group 0.009〜0.65
PAGERANK_MULTIPLIER_GROUP = 35.0
_PAGERANK_EXPONENT = 0.7  # 指数を小さくして大小の差を縮める
_MIN_NODE_SIZE = 10.0


def _calculate_node_size_pagerank(pagerank: float) -> float:
    """
    グループ内PageRankに基づいてノードサイズを計算する

    指数を小さくして大小の差を縮め、最小サイズを保証することで
    小さいノードも見やすくする。

    Args:
        pagerank: グループ内PageRank値（0-1）

    Returns:
        float: ノードサイズ（ピクセル）
    """
    if pagerank <= 0:
        return _MIN_NODE_SIZE
    size = 10.0 * ((pagerank * PAGERANK_MULTIPLIER_GROUP) ** _PAGERANK_EXPONENT)
    return max(_MIN_NODE_SIZE, size)


def _calculate_font_size_pagerank(pagerank: float) -> float:
    """
    グループ内PageRankに基づいてフォントサイズを計算する

    Args:
        pagerank: グループ内PageRank値（0-1）

    Returns:
        float: フォントサイズ（ピクセル）
    """
    min_font_size = 6.0
    max_font_size = 24.0
    if pagerank <= 0:
        return min_font_size
    scaled_value = pagerank * PAGERANK_MULTIPLIER_GROUP
    font_size = min_font_size + 2.0 * (scaled_value**0.7)
    return min(font_size, max_font_size)


def _load_node_positions(group_id: int) -> dict[int, tuple[float, float]]:
    """
    事前計算されたサブグラフ座標を読み込む

    定期スクリプトで計算・保存された座標を読み込む。
    Cytoscape.jsはY軸が下向き正、Matplotlibは上向き正のため、Y座標を反転する。

    Args:
        group_id: グループID

    Returns:
        dict[int, tuple[float, float]]: PEP番号をキー、(x, y)座標を値とする辞書
    """
    positions = load_subgraph_positions(group_id)
    if positions is None:
        return {}

    # Cytoscape.jsはY軸が下向き正、Matplotlibは上向き正のため、Y座標を反転
    return {node: (x, -y) for node, (x, y) in positions.items()}


def _calculate_adjacency_info(subgraph) -> dict[int, dict[str, list[str]]]:
    """
    サブグラフの各ノードの隣接情報を計算する

    Args:
        subgraph: NetworkXグラフオブジェクト

    Returns:
        dict[int, dict[str, list[str]]]: PEP番号をキー、隣接情報を値とする辞書
            隣接情報: {
                "adjacent_nodes": list[str],  # 隣接ノードのID一覧
                "incoming_edges": list[str],  # 入ってくるエッジのID一覧
                "outgoing_edges": list[str],  # 出ていくエッジのID一覧
            }
    """
    adjacency_info: dict[int, dict[str, list[str]]] = {}

    # 全ノードを初期化
    for node in subgraph.nodes():
        adjacency_info[node] = {
            "adjacent_nodes": [],
            "incoming_edges": [],
            "outgoing_edges": [],
        }

    # エッジを走査して隣接情報を構築
    for source, target in subgraph.edges():
        # 自己ループは除外
        if source == target:
            continue

        edge_id = f"edge_{source}_{target}"

        # source → target なので:
        # - sourceから見ると outgoing edge
        # - targetから見ると incoming edge
        if source in adjacency_info:
            adjacency_info[source]["outgoing_edges"].append(edge_id)
            adjacency_info[source]["adjacent_nodes"].append(f"pep_{target}")

        if target in adjacency_info:
            adjacency_info[target]["incoming_edges"].append(edge_id)
            adjacency_info[target]["adjacent_nodes"].append(f"pep_{source}")

    return adjacency_info


def build_subgraph_cytoscape_elements(group_id: int) -> list[dict] | None:
    """
    指定されたグループIDのサブグラフからCytoscape用elementsを構築する

    Args:
        group_id: グループID

    Returns:
        list[dict]: Cytoscape elementsのリスト(ノードとエッジ)、
                    データが存在しない場合はNone
    """
    global _subgraph_elements_cache

    # キャッシュをチェック
    if group_id in _subgraph_elements_cache:
        return _subgraph_elements_cache[group_id]

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

    # 事前計算された座標を読み込む
    positions = _load_node_positions(group_id)

    # 隣接情報を計算
    adjacency_info = _calculate_adjacency_info(subgraph)

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

        # 隣接情報を取得
        adj_info = adjacency_info.get(pep_number, {})

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
                "adjacent_nodes": adj_info.get("adjacent_nodes", []),
                "incoming_edges": adj_info.get("incoming_edges", []),
                "outgoing_edges": adj_info.get("outgoing_edges", []),
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

    # キャッシュに保存
    _subgraph_elements_cache[group_id] = elements
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
                "text-outline-opacity": TEXT_OUTLINE_OPACITY,
            },
        },
        # エッジ基本スタイル
        {
            "selector": "edge",
            "style": {
                "width": 1,
                "line-color": "#999",
                "target-arrow-color": "#999",
                "target-arrow-shape": "triangle",
                "arrow-scale": 0.8,
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
        # 接続ノード
        {
            "selector": ".connected",
            "style": {
                "border-width": 1,
                "border-color": "#888",
                "opacity": 1,
                "text-outline-width": TEXT_OUTLINE_WIDTH,
                "text-outline-color": TEXT_OUTLINE_COLOR,
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
        # 出ていくエッジ（水色）
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
                "text-outline-width": TEXT_OUTLINE_WIDTH,
                "text-outline-color": TEXT_OUTLINE_COLOR,
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


def clear_cache() -> None:
    """
    キャッシュをクリアする（テスト用）
    """
    global _subgraph_elements_cache
    _subgraph_elements_cache = {}


def preload_all_subgraph_elements() -> None:
    """
    全グループのサブグラフ要素を事前計算してキャッシュをウォームアップする

    起動時に呼び出すことで、グループ選択時のレスポンスを高速化する。
    """
    from src.dash_app.utils.data_loader import load_group_data

    df = load_group_data()
    group_ids = df["group_id"].unique().tolist()

    for group_id in group_ids:
        if group_id < 0:
            continue
        build_subgraph_cytoscape_elements(group_id)
