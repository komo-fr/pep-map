"""network_graph.pyのテスト"""

import pytest

from src.dash_app.components.network_graph import get_base_stylesheet


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
