"""network_graph.pyのテスト"""

import pytest

from src.dash_app.components.network_graph import (
    get_base_stylesheet,
    build_cytoscape_elements,
)


class TestGetBaseStylesheet:
    """get_base_stylesheet関数のテスト"""

    def test_contains_selected_selector(self):
        """スタイルシートに:selectedセレクターが含まれることを確認"""
        stylesheet = get_base_stylesheet()

        selectors = [style["selector"] for style in stylesheet]
        assert ":selected" in selectors

    def test_selected_selector_has_border_style(self):
        """`:selected`セレクターに赤い太枠のスタイルが定義されていることを確認"""
        stylesheet = get_base_stylesheet()

        selected_style = None
        for style in stylesheet:
            if style["selector"] == ":selected":
                selected_style = style["style"]
                break

        assert selected_style is not None
        assert selected_style.get("border-width") == 4
        assert selected_style.get("border-color") == "#FF0000"

    def test_selected_selector_has_high_z_index(self):
        """`:selected`セレクターに高いz-indexが設定されていることを確認"""
        stylesheet = get_base_stylesheet()

        selected_style = None
        for style in stylesheet:
            if style["selector"] == ":selected":
                selected_style = style["style"]
                break

        assert selected_style is not None
        assert selected_style.get("z-index") == 9999

    def test_selected_selector_has_full_opacity(self):
        """`:selected`セレクターにopacity: 1が設定されていることを確認"""
        stylesheet = get_base_stylesheet()

        selected_style = None
        for style in stylesheet:
            if style["selector"] == ":selected":
                selected_style = style["style"]
                break

        assert selected_style is not None
        assert selected_style.get("opacity") == 1

    @pytest.mark.parametrize(
        "size_type", ["in_degree", "out_degree", "total_degree", "constant"]
    )
    def test_contains_selected_selector_for_all_size_types(self, size_type):
        """全てのsize_typeで:selectedセレクターが含まれることを確認"""
        stylesheet = get_base_stylesheet(size_type)

        selectors = [style["selector"] for style in stylesheet]
        assert ":selected" in selectors


class TestBuildCytoscapeElements:
    """build_cytoscape_elements関数のテスト"""

    @pytest.fixture(autouse=True)
    def setup(self, mock_data_files, monkeypatch):
        """各テストの前にキャッシュをクリアし、モックデータを使用"""
        from src.dash_app.components import network_graph
        from src.dash_app.utils import data_loader

        # キャッシュをクリア
        data_loader.clear_cache()
        network_graph._cytoscape_elements_cache = None

        # DATA_DIRをモックデータディレクトリに変更
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)

    def test_nodes_have_adjacent_nodes_field(self):
        """ノードにadjacent_nodesフィールドが含まれることを確認"""
        elements = build_cytoscape_elements()
        nodes = [e for e in elements if "source" not in e["data"]]

        for node in nodes:
            assert "adjacent_nodes" in node["data"], (
                f"Node {node['data']['id']} missing adjacent_nodes field"
            )
            assert isinstance(node["data"]["adjacent_nodes"], list)

    def test_nodes_have_incoming_edges_field(self):
        """ノードにincoming_edgesフィールドが含まれることを確認"""
        elements = build_cytoscape_elements()
        nodes = [e for e in elements if "source" not in e["data"]]

        for node in nodes:
            assert "incoming_edges" in node["data"], (
                f"Node {node['data']['id']} missing incoming_edges field"
            )
            assert isinstance(node["data"]["incoming_edges"], list)

    def test_nodes_have_outgoing_edges_field(self):
        """ノードにoutgoing_edgesフィールドが含まれることを確認"""
        elements = build_cytoscape_elements()
        nodes = [e for e in elements if "source" not in e["data"]]

        for node in nodes:
            assert "outgoing_edges" in node["data"], (
                f"Node {node['data']['id']} missing outgoing_edges field"
            )
            assert isinstance(node["data"]["outgoing_edges"], list)

    def test_adjacent_nodes_contains_correct_ids(self):
        """adjacent_nodesに正しいノードIDが含まれることを確認"""
        elements = build_cytoscape_elements()

        # PEP 484のノードを探す
        pep_484_node = None
        for e in elements:
            if e["data"].get("pep_number") == 484:
                pep_484_node = e
                break

        assert pep_484_node is not None
        adjacent_nodes = pep_484_node["data"]["adjacent_nodes"]

        # sample_citationsによると:
        # - PEP 484 → PEP 3107 (citing)
        # - PEP 8 → PEP 484 (cited)
        # - PEP 484 → PEP 8 (citing)
        # したがって、PEP 484の隣接ノードは: PEP 3107, PEP 8
        assert "pep_3107" in adjacent_nodes
        assert "pep_8" in adjacent_nodes

    def test_incoming_edges_contains_correct_ids(self):
        """incoming_edgesに正しいエッジIDが含まれることを確認"""
        elements = build_cytoscape_elements()

        # PEP 484のノードを探す
        pep_484_node = None
        for e in elements:
            if e["data"].get("pep_number") == 484:
                pep_484_node = e
                break

        assert pep_484_node is not None
        incoming_edges = pep_484_node["data"]["incoming_edges"]

        # PEP 8 → PEP 484 のエッジが含まれる
        assert "edge_8_484" in incoming_edges

    def test_outgoing_edges_contains_correct_ids(self):
        """outgoing_edgesに正しいエッジIDが含まれることを確認"""
        elements = build_cytoscape_elements()

        # PEP 484のノードを探す
        pep_484_node = None
        for e in elements:
            if e["data"].get("pep_number") == 484:
                pep_484_node = e
                break

        assert pep_484_node is not None
        outgoing_edges = pep_484_node["data"]["outgoing_edges"]

        # PEP 484 → PEP 3107, PEP 484 → PEP 8 のエッジが含まれる
        assert "edge_484_3107" in outgoing_edges
        assert "edge_484_8" in outgoing_edges

    def test_nodes_have_degree_fields(self):
        """ノードに次数フィールド（in_degree, out_degree, total_degree）が含まれることを確認"""
        elements = build_cytoscape_elements()
        nodes = [e for e in elements if "source" not in e["data"]]

        for node in nodes:
            assert "in_degree" in node["data"], (
                f"Node {node['data']['id']} missing in_degree field"
            )
            assert "out_degree" in node["data"], (
                f"Node {node['data']['id']} missing out_degree field"
            )
            assert "total_degree" in node["data"], (
                f"Node {node['data']['id']} missing total_degree field"
            )
            assert isinstance(node["data"]["in_degree"], int)
            assert isinstance(node["data"]["out_degree"], int)
            assert isinstance(node["data"]["total_degree"], int)

    def test_nodes_have_pagerank_field(self):
        """ノードにPageRankフィールドが含まれることを確認"""
        elements = build_cytoscape_elements()
        nodes = [e for e in elements if "source" not in e["data"]]

        for node in nodes:
            assert "pagerank" in node["data"], (
                f"Node {node['data']['id']} missing pagerank field"
            )
            assert isinstance(node["data"]["pagerank"], float)

    def test_degree_values_match_csv_data(self):
        """ノードの次数データがnode_metrics.csvから読み込まれた値と一致することを確認"""
        elements = build_cytoscape_elements()

        # PEP 484のノードを探す
        pep_484_node = None
        for e in elements:
            if e["data"].get("pep_number") == 484:
                pep_484_node = e
                break

        assert pep_484_node is not None

        # sample_node_metricsによると、PEP 484の値は:
        # in_degree: 1, out_degree: 2, degree: 3, pagerank: 0.50
        assert pep_484_node["data"]["in_degree"] == 1
        assert pep_484_node["data"]["out_degree"] == 2
        assert pep_484_node["data"]["total_degree"] == 3
        assert pep_484_node["data"]["pagerank"] == 0.50

    def test_degree_values_for_pep_8(self):
        """PEP 8のノードの次数データがCSVの値と一致することを確認"""
        elements = build_cytoscape_elements()

        # PEP 8のノードを探す
        pep_8_node = None
        for e in elements:
            if e["data"].get("pep_number") == 8:
                pep_8_node = e
                break

        assert pep_8_node is not None

        # sample_node_metricsによると、PEP 8の値は:
        # in_degree: 1, out_degree: 1, degree: 2, pagerank: 0.25
        assert pep_8_node["data"]["in_degree"] == 1
        assert pep_8_node["data"]["out_degree"] == 1
        assert pep_8_node["data"]["total_degree"] == 2
        assert pep_8_node["data"]["pagerank"] == 0.25

    def test_degree_values_for_pep_3107(self):
        """PEP 3107のノードの次数データがCSVの値と一致することを確認"""
        elements = build_cytoscape_elements()

        # PEP 3107のノードを探す
        pep_3107_node = None
        for e in elements:
            if e["data"].get("pep_number") == 3107:
                pep_3107_node = e
                break

        assert pep_3107_node is not None

        # sample_node_metricsによると、PEP 3107の値は:
        # in_degree: 1, out_degree: 0, degree: 1, pagerank: 0.25
        assert pep_3107_node["data"]["in_degree"] == 1
        assert pep_3107_node["data"]["out_degree"] == 0
        assert pep_3107_node["data"]["total_degree"] == 1
        assert pep_3107_node["data"]["pagerank"] == 0.25
