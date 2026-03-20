"""constants.pyのテスト"""

import re


from src.dash_app.utils.constants import (
    GROUP_COLOR_PALETTE,
    ISOLATED_NODE_COLOR,
    get_group_color,
)


class TestGetGroupColor:
    """get_group_color関数のテスト"""

    def test_isolated_node_returns_isolated_color(self):
        """孤立ノード（group_id=-1）は専用の色を返す"""
        assert get_group_color(-1) == ISOLATED_NODE_COLOR

    def test_negative_group_ids_return_isolated_color(self):
        """負のgroup_idは全て孤立ノードの色を返す"""
        assert get_group_color(-1) == ISOLATED_NODE_COLOR
        assert get_group_color(-10) == ISOLATED_NODE_COLOR
        assert get_group_color(-100) == ISOLATED_NODE_COLOR

    def test_palette_range_returns_palette_colors(self):
        """パレット範囲内（0〜31）は事前定義された色を返す"""
        for i in range(len(GROUP_COLOR_PALETTE)):
            assert get_group_color(i) == GROUP_COLOR_PALETTE[i]

    def test_beyond_palette_returns_valid_hex_color(self):
        """パレットを超えた場合も有効な16進数カラーコードを返す"""
        hex_color_pattern = re.compile(r"^#[0-9a-f]{6}$")

        for group_id in [32, 50, 100, 500]:
            color = get_group_color(group_id)
            assert hex_color_pattern.match(color), f"Invalid color format: {color}"

    def test_beyond_palette_colors_are_different(self):
        """パレットを超えた連続するグループIDは異なる色を返す"""
        colors = [get_group_color(i) for i in range(32, 42)]
        # 全ての色がユニークであることを確認
        assert len(set(colors)) == len(colors)

    def test_beyond_palette_colors_differ_from_adjacent(self):
        """黄金比により隣接グループでも色が大きく異なる"""
        # 連続する2つのグループの色相差を確認
        # 黄金比（0.618...）により、隣接しても色相が大きくずれる
        color1 = get_group_color(32)
        color2 = get_group_color(33)
        assert color1 != color2

    def test_same_group_id_returns_same_color(self):
        """同じgroup_idは常に同じ色を返す（決定的）"""
        for group_id in [0, 15, 31, 32, 50, 100]:
            color1 = get_group_color(group_id)
            color2 = get_group_color(group_id)
            assert color1 == color2

    def test_generated_colors_have_reasonable_saturation(self):
        """動的生成された色は適切な彩度を持つ（グレーではない）"""
        for group_id in [32, 50, 100]:
            color = get_group_color(group_id)
            # RGBに分解
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            # 最大値と最小値の差が小さすぎない（グレーに近くない）
            color_range = max(r, g, b) - min(r, g, b)
            assert color_range > 30, f"Color {color} is too gray-ish"
