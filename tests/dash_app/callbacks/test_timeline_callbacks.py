"""timeline_callbacksモジュールのテスト"""

from src.dash_app.callbacks.timeline_callbacks import (
    _compute_table_titles,
    _parse_pep_number,
)


class TestParsePepNumber:
    """_parse_pep_number関数のテスト"""

    def test_none_input(self):
        """Noneを渡すとNoneを返す"""
        assert _parse_pep_number(None) is None

    def test_empty_string(self):
        """空文字を渡すとNoneを返す"""
        assert _parse_pep_number("") is None

    def test_integer_string(self):
        """数値文字列を整数に変換する"""
        assert _parse_pep_number("484") == 484

    def test_integer(self):
        """整数をそのまま返す"""
        assert _parse_pep_number(8) == 8

    def test_invalid_string(self):
        """数値に変換できない文字列はNoneを返す"""
        assert _parse_pep_number("abc") is None


class TestComputeTableTitles:
    """_compute_table_titles関数のテスト"""

    def test_none_input(self, mock_data_files, monkeypatch):
        """入力がNoneの場合はデフォルトのタイトルを返す"""
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)

        citing_title, cited_title = _compute_table_titles(None)

        assert citing_title == "PEP N is linked from..."
        assert cited_title == "PEP N links to..."

    def test_empty_string(self, mock_data_files, monkeypatch):
        """入力が空文字の場合はデフォルトのタイトルを返す"""
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)

        citing_title, cited_title = _compute_table_titles("")

        assert citing_title == "PEP N is linked from..."
        assert cited_title == "PEP N links to..."

    def test_existing_pep(self, mock_data_files, monkeypatch):
        """存在するPEP番号の場合はPEP番号入りのタイトルを返す"""
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)
        from src.dash_app.utils import data_loader

        data_loader.clear_cache()

        citing_title, cited_title = _compute_table_titles(484)

        assert citing_title == "PEP 484 is linked from..."
        assert cited_title == "PEP 484 links to..."

    def test_nonexistent_pep(self, mock_data_files, monkeypatch):
        """存在しないPEP番号の場合はデフォルトのタイトルを返す"""
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)
        from src.dash_app.utils import data_loader

        data_loader.clear_cache()

        citing_title, cited_title = _compute_table_titles(9999)

        assert citing_title == "PEP N is linked from..."
        assert cited_title == "PEP N links to..."
