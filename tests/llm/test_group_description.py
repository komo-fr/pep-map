"""Tests for src.llm.group_profile module."""

import base64
from pathlib import Path

import pandas as pd

from src.llm.group_profile import (
    format_peps_as_markdown,
    encode_image_as_data_url,
    GroupProfile,
)


class TestFormatPepsAsMarkdown:
    """format_peps_as_markdown() のテスト"""

    def test_returns_markdown_for_specified_group(self, tmp_path: Path):
        """指定したgroup_idの行のみがmarkdown形式で返される"""
        # Arrange
        csv_path = tmp_path / "pep_group_metrics.csv"
        df = pd.DataFrame(
            [
                {
                    "PEP": 1,
                    "title": "PEP Purpose",
                    "status": "Active",
                    "created": "2000-01-01",
                    "group_id": 0,
                    "pagerank_group": 0.5,
                    "in-degree_group": 2,
                    "out-degree_group": 1,
                },
                {
                    "PEP": 8,
                    "title": "Style Guide",
                    "status": "Active",
                    "created": "2001-01-01",
                    "group_id": 0,
                    "pagerank_group": 0.3,
                    "in-degree_group": 1,
                    "out-degree_group": 0,
                },
                {
                    "PEP": 20,
                    "title": "Zen of Python",
                    "status": "Active",
                    "created": "2004-01-01",
                    "group_id": 1,
                    "pagerank_group": 0.8,
                    "in-degree_group": 5,
                    "out-degree_group": 0,
                },
            ]
        )
        df.to_csv(csv_path, index=False)

        # Act
        result = format_peps_as_markdown(csv_path, group_id=0)

        # Assert
        assert "PEP Purpose" in result
        assert "Style Guide" in result
        assert "Zen of Python" not in result  # group_id=1 は含まれない

    def test_sorted_by_pagerank_descending(self, tmp_path: Path):
        """pagerank_group降順でソートされている"""
        # Arrange
        csv_path = tmp_path / "pep_group_metrics.csv"
        df = pd.DataFrame(
            [
                {
                    "PEP": 1,
                    "title": "Low PageRank",
                    "status": "Active",
                    "created": "2000-01-01",
                    "group_id": 0,
                    "pagerank_group": 0.1,
                    "in-degree_group": 1,
                    "out-degree_group": 0,
                },
                {
                    "PEP": 2,
                    "title": "High PageRank",
                    "status": "Active",
                    "created": "2000-01-01",
                    "group_id": 0,
                    "pagerank_group": 0.9,
                    "in-degree_group": 5,
                    "out-degree_group": 2,
                },
                {
                    "PEP": 3,
                    "title": "Mid PageRank",
                    "status": "Active",
                    "created": "2000-01-01",
                    "group_id": 0,
                    "pagerank_group": 0.5,
                    "in-degree_group": 3,
                    "out-degree_group": 1,
                },
            ]
        )
        df.to_csv(csv_path, index=False)

        # Act
        result = format_peps_as_markdown(csv_path, group_id=0)

        # Assert: High > Mid > Low の順で出現する
        high_pos = result.find("High PageRank")
        mid_pos = result.find("Mid PageRank")
        low_pos = result.find("Low PageRank")
        assert high_pos < mid_pos < low_pos


class TestEncodeImageAsDataUrl:
    """encode_image_as_data_url() のテスト"""

    def test_returns_base64_encoded_data_url(self, tmp_path: Path):
        """base64エンコードされたdata URLが返される"""
        # Arrange
        image_path = tmp_path / "test.png"
        # 1x1 の赤いPNG画像（最小限のPNGデータ）
        png_data = bytes(
            [
                0x89,
                0x50,
                0x4E,
                0x47,
                0x0D,
                0x0A,
                0x1A,
                0x0A,  # PNG signature
                0x00,
                0x00,
                0x00,
                0x0D,
                0x49,
                0x48,
                0x44,
                0x52,  # IHDR chunk
                0x00,
                0x00,
                0x00,
                0x01,
                0x00,
                0x00,
                0x00,
                0x01,
                0x08,
                0x02,
                0x00,
                0x00,
                0x00,
                0x90,
                0x77,
                0x53,
                0xDE,
                0x00,
                0x00,
                0x00,
                0x0C,
                0x49,
                0x44,
                0x41,
                0x54,
                0x08,
                0xD7,
                0x63,
                0xF8,
                0xFF,
                0xFF,
                0x3F,
                0x00,
                0x05,
                0xFE,
                0x02,
                0xFE,
                0xDC,
                0xCC,
                0x59,
                0xE7,
                0x00,
                0x00,
                0x00,
                0x00,
                0x49,
                0x45,
                0x4E,
                0x44,
                0xAE,
                0x42,
                0x60,
                0x82,
            ]
        )
        image_path.write_bytes(png_data)

        # Act
        result = encode_image_as_data_url(str(image_path))

        # Assert
        assert result.startswith("data:image/png;base64,")
        # base64部分をデコードして元のデータと一致することを確認
        base64_part = result.split(",")[1]
        decoded = base64.b64decode(base64_part)
        assert decoded == png_data


class TestGroupProfileStr:
    """GroupProfile.__str__() のテスト"""

    def test_returns_expected_format(self):
        """期待通りの文字列フォーマットで返される"""
        # Arrange
        output = GroupProfile(
            group_name="型ヒント",
            description="このグループは型ヒントに関するPEPを含みます。",
            group_name_2="型アノテーション",
            group_name_3="静的型付け",
        )

        # Act
        result = str(output)

        # Assert
        lines = result.split("\n")
        assert lines[0] == "型ヒント"
        assert lines[1] == "型アノテーション / 静的型付け"
        assert lines[2] == "説明:"
        assert lines[3] == "このグループは型ヒントに関するPEPを含みます。"
