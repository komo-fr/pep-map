"""src/graph/layout.py のテスト"""

import networkx as nx
import pytest

from src.graph.layout import calculate_full_network_positions


@pytest.fixture
def sample_graph():
    """テスト用のサンプルグラフ"""
    G = nx.DiGraph()
    # 接続されたノード
    G.add_edge(1, 8)
    G.add_edge(8, 20)
    G.add_edge(20, 1)
    # 孤立ノード
    G.add_node(100)
    G.add_node(200)
    G.add_node(300)
    return G


class TestCalculateFullNetworkPositions:
    """calculate_full_network_positions関数のテスト"""

    def test_all_nodes_have_positions(self, sample_graph):
        """すべてのノードに座標が割り当てられる"""
        positions = calculate_full_network_positions(sample_graph)

        assert set(positions.keys()) == set(sample_graph.nodes())

    def test_isolated_nodes_are_left_of_connected_nodes(self, sample_graph):
        """孤立ノードは接続ノードより左に配置される"""
        positions = calculate_full_network_positions(sample_graph)

        isolated_x = [positions[n][0] for n in [100, 200, 300]]
        connected_x = [positions[n][0] for n in [1, 8, 20]]

        assert max(isolated_x) < min(connected_x)

    def test_reproducible_with_same_seed(self, sample_graph):
        """同じシードで再現性がある"""
        positions1 = calculate_full_network_positions(sample_graph)
        positions2 = calculate_full_network_positions(sample_graph)

        assert positions1 == positions2
