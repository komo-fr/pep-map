"""
ネットワークグラフのレイアウト計算モジュール

全体ネットワークの座標計算ロジックを提供する。
DashアプリとスクリプトCLIの両方から使用される共通モジュール。
"""

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
