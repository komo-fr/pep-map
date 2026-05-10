"""グループ間ネットワークグラフ構築モジュール"""

import math

import networkx as nx

from src.dash_app.utils.constants import (
    TEXT_OUTLINE_COLOR,
    TEXT_OUTLINE_WIDTH,
    get_group_color,
)
from src.dash_app.utils.data_loader import (
    get_group_name_info,
    load_group_to_group_network,
    load_group_to_group_positions,
)


# モジュールレベルでキャッシュ
_group_to_group_cytoscape_elements_cache: list[dict] | None = None

# ノードサイズ計算用の定数（面積がpep_countに比例するため、サイズは√pep_countに比例）
_MIN_NODE_SIZE = 30.0
_MAX_NODE_SIZE = 100.0
_MIN_FONT_SIZE = 12.0
_MAX_FONT_SIZE = 25.0

# エッジスタイル用の定数
_MIN_EDGE_WIDTH = 1.0
_MAX_EDGE_WIDTH = 10.0


def _calculate_node_size(pep_count: int, min_count: int, max_count: int) -> float:
    """
    PEP数に基づいてノードサイズを計算する

    面積がpep_countに比例するように、サイズは√pep_countに比例させる。

    Args:
        pep_count: グループに含まれるPEP数
        min_count: 最小PEP数
        max_count: 最大PEP数

    Returns:
        float: ノードサイズ（ピクセル）
    """
    if max_count == min_count:
        return (_MIN_NODE_SIZE + _MAX_NODE_SIZE) / 2

    # 面積がpep_countに比例するように、サイズは√pep_countに比例させる
    sqrt_min = math.sqrt(min_count)
    sqrt_max = math.sqrt(max_count)
    sqrt_count = math.sqrt(pep_count)

    normalized = (sqrt_count - sqrt_min) / (sqrt_max - sqrt_min)
    return _MIN_NODE_SIZE + normalized * (_MAX_NODE_SIZE - _MIN_NODE_SIZE)


def _calculate_font_size(pep_count: int, min_count: int, max_count: int) -> float:
    """
    PEP数に基づいてフォントサイズを計算する

    ノードサイズに合わせて√pep_countに比例させる。

    Args:
        pep_count: グループに含まれるPEP数
        min_count: 最小PEP数
        max_count: 最大PEP数

    Returns:
        float: フォントサイズ（ピクセル）
    """
    if max_count == min_count:
        return (_MIN_FONT_SIZE + _MAX_FONT_SIZE) / 2

    sqrt_min = math.sqrt(min_count)
    sqrt_max = math.sqrt(max_count)
    sqrt_count = math.sqrt(pep_count)

    normalized = (sqrt_count - sqrt_min) / (sqrt_max - sqrt_min)
    return _MIN_FONT_SIZE + normalized * (_MAX_FONT_SIZE - _MIN_FONT_SIZE)


def _calculate_edge_width(weight: int, min_weight: int, max_weight: int) -> float:
    """
    エッジのweightに基づいてエッジ幅を計算する

    Args:
        weight: エッジのweight（引用数）
        min_weight: 最小weight
        max_weight: 最大weight

    Returns:
        float: エッジ幅（ピクセル）
    """
    if max_weight == min_weight:
        return (_MIN_EDGE_WIDTH + _MAX_EDGE_WIDTH) / 2

    normalized = (weight - min_weight) / (max_weight - min_weight)
    return _MIN_EDGE_WIDTH + normalized * (_MAX_EDGE_WIDTH - _MIN_EDGE_WIDTH)


def _calculate_adjacency_info(G: nx.DiGraph) -> dict[int, dict[str, list[str]]]:
    """
    グループ間ネットワークの各ノードの隣接情報を計算する

    Args:
        G: NetworkXグラフオブジェクト

    Returns:
        dict[int, dict[str, list[str]]]: グループIDをキー、隣接情報を値とする辞書
            隣接情報: {
                "adjacent_nodes": list[str],  # 隣接ノードのID一覧
                "incoming_edges": list[str],  # 入ってくるエッジのID一覧
                "outgoing_edges": list[str],  # 出ていくエッジのID一覧
            }
    """
    adjacency_info: dict[int, dict[str, list[str]]] = {}

    # 全ノードを初期化
    for node in G.nodes():
        adjacency_info[node] = {
            "adjacent_nodes": [],
            "incoming_edges": [],
            "outgoing_edges": [],
        }

    # エッジを走査して隣接情報を構築
    for source, target in G.edges():
        # 自己ループは除外
        if source == target:
            continue

        edge_id = f"edge_{source}_{target}"

        # source → target なので:
        # - sourceから見ると outgoing edge
        # - targetから見ると incoming edge
        if source in adjacency_info:
            adjacency_info[source]["outgoing_edges"].append(edge_id)
            adjacency_info[source]["adjacent_nodes"].append(f"group_{target}")

        if target in adjacency_info:
            adjacency_info[target]["incoming_edges"].append(edge_id)
            adjacency_info[target]["adjacent_nodes"].append(f"group_{source}")

    return adjacency_info


def build_group_to_group_cytoscape_elements() -> list[dict]:
    """
    グループ間ネットワークのCytoscape用elementsを構築する

    Returns:
        list[dict]: Cytoscape elementsのリスト(ノードとエッジ)
            ノードには以下のデータが含まれる:
            - id: グループID
            - label: グループID
            - group_id: グループID
            - group_name: グループ名
            - pep_count: PEP数
            - group_color: グループの色
            - size: ノードサイズ
            - font_size: フォントサイズ
            エッジには以下のデータが含まれる:
            - id: エッジID
            - source: 引用元グループID
            - target: 引用先グループID
            - weight: 引用数
            - edge_width: エッジ幅
    """
    global _group_to_group_cytoscape_elements_cache

    if _group_to_group_cytoscape_elements_cache is not None:
        return _group_to_group_cytoscape_elements_cache

    # グループ間ネットワークを読み込む
    G = load_group_to_group_network()

    # 事前計算された座標を読み込む
    positions = load_group_to_group_positions()

    # PEP数の最小値と最大値を取得
    pep_counts = [G.nodes[node].get("pep_count", 1) for node in G.nodes()]
    min_pep_count = min(pep_counts) if pep_counts else 1
    max_pep_count = max(pep_counts) if pep_counts else 1

    # エッジweightの最小値と最大値を取得
    weights = [G.edges[edge].get("weight", 1) for edge in G.edges()]
    min_weight = min(weights) if weights else 1
    max_weight = max(weights) if weights else 1

    # Cytoscapeのスケーリング用の係数（座標系を大きくする）
    scale_factor = 500

    # 隣接情報を計算
    adjacency_info = _calculate_adjacency_info(G)

    elements = []

    # ノードを生成
    for node in G.nodes():
        group_id = node
        node_data = G.nodes[node]
        group_name = get_group_name_info(group_id)["group_name"]
        pep_count = node_data.get("pep_count", 1)

        # 座標を取得（Cytoscapeはy軸が下向きなので反転）
        pos = positions.get(group_id, (0, 0))
        x = pos[0] * scale_factor
        y = -pos[1] * scale_factor  # Y軸を反転

        # サイズとフォントサイズを計算
        size = _calculate_node_size(pep_count, min_pep_count, max_pep_count)
        font_size = _calculate_font_size(pep_count, min_pep_count, max_pep_count)

        # グループ色を取得
        group_color = get_group_color(group_id)

        # 隣接情報を取得
        adj_info = adjacency_info.get(group_id, {})

        element = {
            "data": {
                "id": f"group_{group_id}",
                "label": f"Group\n{group_id}",
                "group_id": group_id,
                "group_name": group_name,
                "pep_count": pep_count,
                "group_color": group_color,
                "size": size,
                "font_size": font_size,
                "adjacent_nodes": adj_info.get("adjacent_nodes", []),
                "incoming_edges": adj_info.get("incoming_edges", []),
                "outgoing_edges": adj_info.get("outgoing_edges", []),
            },
            "position": {"x": x, "y": y},
        }
        elements.append(element)

    # エッジを生成
    for source, target in G.edges():
        # 自己ループは除外
        if source == target:
            continue

        edge_data = G.edges[source, target]
        weight = edge_data.get("weight", 1)
        edge_width = _calculate_edge_width(weight, min_weight, max_weight)

        element = {
            "data": {
                "id": f"edge_{source}_{target}",
                "source": f"group_{source}",
                "target": f"group_{target}",
                "weight": weight,
                "edge_width": edge_width,
            }
        }
        elements.append(element)

    _group_to_group_cytoscape_elements_cache = elements
    return elements


def get_group_to_group_base_stylesheet() -> list[dict]:
    """
    グループ間ネットワーク用の基本スタイルシートを取得する

    Returns:
        list[dict]: スタイルシート定義のリスト
    """
    return [
        # ノード基本スタイル
        {
            "selector": "node",
            "style": {
                "label": "data(label)",
                "background-color": "data(group_color)",
                "width": "data(size)",
                "height": "data(size)",
                "shape": "round-rectangle",
                "font-size": "data(font_size)",
                "text-valign": "center",
                "text-halign": "center",
                "text-wrap": "wrap",
                "border-width": 1,
                "border-color": "#666",
                "opacity": 0.9,
                "text-outline-width": TEXT_OUTLINE_WIDTH,
                "text-outline-color": TEXT_OUTLINE_COLOR,
            },
        },
        # エッジ基本スタイル
        {
            "selector": "edge",
            "style": {
                "width": "data(edge_width)",
                "line-color": "#999",
                "target-arrow-color": "#999",
                "target-arrow-shape": "triangle",
                "arrow-scale": 0.8,
                "curve-style": "bezier",
                "opacity": 0.5,
            },
        },
        # ノード選択時のスタイル
        {
            "selector": ":selected",
            "style": {
                "border-width": 5,
                "border-color": "#FF0000",
                "z-index": 9999,
                "opacity": 1,
            },
        },
        # 接続ノード
        {
            "selector": ".connected",
            "style": {
                "border-width": 2,
                "border-color": "#888",
                "opacity": 1,
                "text-outline-width": TEXT_OUTLINE_WIDTH,
                "text-outline-color": TEXT_OUTLINE_COLOR,
            },
        },
        # 入ってくるエッジ（オレンジ色）
        {
            "selector": ".incoming-edge",
            "style": {
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


def get_group_to_group_layout_options() -> dict:
    """
    グループ間ネットワーク用のレイアウトオプションを取得する

    Returns:
        dict: レイアウトオプション
    """
    return {
        "name": "preset",
        "fit": True,
        "padding": 30,
    }


def clear_cache() -> None:
    """
    キャッシュをクリアする（テスト用）
    """
    global _group_to_group_cytoscape_elements_cache
    _group_to_group_cytoscape_elements_cache = None
