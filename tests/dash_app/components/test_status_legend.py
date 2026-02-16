"""status_legendコンポーネントのテスト"""

from dash import html

from src.dash_app.components.status_legend import create_status_legend
from src.dash_app.utils.constants import STATUS_COLOR_MAP


class TestCreateStatusLegend:
    """create_status_legend関数のテスト"""

    def test_create_status_legend_structure(self):
        """正しいHTML構造を生成する"""
        legend = create_status_legend()

        assert isinstance(legend, html.Div)
        # 凡例には2つの子要素がある: 説明文とアイテムコンテナ
        assert len(legend.children) == 2
        assert isinstance(legend.children[0], html.P)  # 説明文
        assert isinstance(legend.children[1], html.Div)  # アイテムコンテナ

    def test_create_status_legend_description(self):
        """説明文が正しく表示される"""
        legend = create_status_legend()

        description = legend.children[0]
        assert description.children == "Color means the status of PEPs"
        assert "fontSize" in description.style
        assert description.style["fontSize"] == "12px"

    def test_create_status_legend_all_statuses(self):
        """全ステータスが含まれる"""
        legend = create_status_legend()

        # アイテムコンテナを取得
        items_container = legend.children[1]
        legend_items = items_container.children

        # STATUS_COLOR_MAPと同じ数のアイテムが含まれている
        assert len(legend_items) == len(STATUS_COLOR_MAP)

        # 各ステータスが含まれていることを確認
        status_labels = []
        for item in legend_items:
            # 各アイテムはSpanで、その中に[color_box, status_text]が含まれる
            status_text = item.children[1].children
            status_labels.append(status_text)

        for status in STATUS_COLOR_MAP.keys():
            assert status in status_labels

    def test_create_status_legend_colors(self):
        """各ステータスに正しい色が設定される"""
        legend = create_status_legend()

        # アイテムコンテナを取得
        items_container = legend.children[1]
        legend_items = items_container.children

        for i, (status, color) in enumerate(STATUS_COLOR_MAP.items()):
            legend_item = legend_items[i]

            # 各アイテムの最初の子要素が色付き四角
            color_box = legend_item.children[0]

            # style属性にbackgroundColorが含まれることを確認
            assert "backgroundColor" in color_box.style
            assert color_box.style["backgroundColor"] == color

            # 2番目の子要素がステータステキスト
            status_text = legend_item.children[1]
            assert status_text.children == status

    def test_create_status_legend_item_styles(self):
        """各アイテムのスタイルが正しく設定される"""
        legend = create_status_legend()

        items_container = legend.children[1]
        legend_items = items_container.children

        # 最初のアイテムをチェック
        first_item = legend_items[0]

        # アイテム自体のスタイル
        assert "display" in first_item.style
        assert first_item.style["display"] == "inline-block"
        assert "marginRight" in first_item.style

        # 色付き四角のスタイル
        color_box = first_item.children[0]
        assert color_box.style["width"] == "12px"
        assert color_box.style["height"] == "12px"
        assert color_box.style["display"] == "inline-block"

        # ステータステキストのスタイル
        status_text = first_item.children[1]
        assert "fontSize" in status_text.style
        assert status_text.style["fontSize"] == "12px"
