"""
ネットワークグラフのレイアウト計算モジュール

全体ネットワークおよびサブグラフの座標計算ロジックを提供する。
DashアプリとスクリプトCLIの両方から使用される共通モジュール。
"""

import math

import networkx as nx


def calculate_full_network_positions(
    G: nx.DiGraph,
) -> dict[int, tuple[float, float]]:
    """
    全体ネットワークのノード座標を計算する

    孤立ノード(引用関係がないPEP)は左端に3列でグリッド配置し、
    引用関係のあるノードは中央にspring_layoutで配置する。

    Args:
        G: NetworkXの有向グラフ（ノードはPEP番号）

    Returns:
        PEP番号をキー、(x, y)座標を値とする辞書
    """
    # 孤立ノードと引用関係のあるノードを分離
    isolated_nodes = [node for node in G.nodes() if G.degree(node) == 0]
    connected_nodes = [node for node in G.nodes() if G.degree(node) > 0]

    positions: dict[int, tuple[float, float]] = {}

    # 引用関係のあるノードをspring_layoutで配置
    if connected_nodes:
        subgraph = G.subgraph(connected_nodes)
        connected_positions = nx.spring_layout(
            subgraph,
            threshold=1e-6,
            k=500,  # ノード間の理想的な距離
            iterations=500,
            seed=42,
            scale=1000,
        )

        positions.update(
            {n: (float(p[0]), float(p[1])) for n, p in connected_positions.items()}
        )

        y_values = [positions[n][1] for n in connected_nodes]
        y_min = min(y_values)
        y_max = max(y_values)
    else:
        y_min = -500
        y_max = 500

    # 孤立ノードを左端に3列で配置
    if isolated_nodes:
        isolated_nodes_sorted = sorted(isolated_nodes)
        num_cols = 3
        col_spacing = 40

        if connected_nodes:
            connected_x_coords = [positions[n][0] for n in connected_nodes]
            min_connected_x = min(connected_x_coords)
            x_start = min_connected_x - 100
        else:
            x_start = -700

        num_nodes = len(isolated_nodes_sorted)
        nodes_per_col = (num_nodes + num_cols - 1) // num_cols

        y_range = y_max - y_min
        if nodes_per_col > 1:
            y_spacing = y_range / (nodes_per_col - 1)
        else:
            y_spacing = 0

        for i, node in enumerate(isolated_nodes_sorted):
            col = i // nodes_per_col
            row_index = i % nodes_per_col

            x = x_start + col * col_spacing
            y = y_max - row_index * y_spacing

            positions[node] = (float(x), float(y))

    return positions


def calculate_grid_layout(subgraph: nx.Graph) -> dict[int, tuple[float, float]]:
    """
    ノードを格子状に配置する（孤立点グループ用）

    Args:
        subgraph: NetworkX DiGraph

    Returns:
        dict[int, tuple[float, float]]: ノードをキー、(x, y)座標を値とする辞書
    """
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


def calculate_subgraph_positions(
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


def calculate_group_to_group_positions(
    G: nx.DiGraph,
) -> dict[int, tuple[float, float]]:
    """
    グループ間ネットワークのノード座標を計算する

    max_group_id（孤立PEPの集まり）は左上に配置し、
    それ以外のグループはspring_layoutで配置する。

    Args:
        G: グループ間ネットワークグラフ

    Returns:
        dict[int, tuple[float, float]]: グループIDをキー、(x, y)座標を値とする辞書
    """
    if len(G.nodes()) == 0:
        return {}

    # 最大グループID（孤立ノードの集まり）を取得
    max_group_id = max(G.nodes())

    # 通常どおりレイアウトを計算する
    raw_pos = nx.spring_layout(
        G,
        seed=42,
        weight=None,
        k=5,
        iterations=300,
    )

    # numpy配列をtupleに変換する
    pos: dict[int, tuple[float, float]] = {
        node: (float(xy[0]), float(xy[1])) for node, xy in raw_pos.items()
    }

    # max_group_idだけ左上に移動する
    # 他の孤立グループはspring_layoutの結果をそのまま使う
    other_positions = {node: xy for node, xy in pos.items() if node != max_group_id}

    if other_positions:
        x_values = [xy[0] for xy in other_positions.values()]
        y_values = [xy[1] for xy in other_positions.values()]

        x_min = min(x_values)
        y_max = max(y_values)

        pos[max_group_id] = (x_min, y_max)

    return pos
