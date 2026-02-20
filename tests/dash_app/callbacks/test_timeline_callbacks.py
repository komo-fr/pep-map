"""timeline_callbacksモジュールのテスト"""

import plotly.graph_objects as go

from src.dash_app.callbacks.timeline_callbacks import (
    _add_python_release_lines,
    _add_release_lines_for_major_version,
    _compute_table_titles,
    _parse_pep_number,
)
from src.dash_app.utils import data_loader
from src.dash_app.utils.constants import (
    PYTHON_2_LINE_COLOR,
    PYTHON_3_LINE_COLOR,
    TIMELINE_Y_PYTHON2_LABEL,
    TIMELINE_Y_PYTHON3_LABEL,
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

        assert citing_title == "PEP N is cited by..."
        assert cited_title == "PEP N cites..."

    def test_empty_string(self, mock_data_files, monkeypatch):
        """入力が空文字の場合はデフォルトのタイトルを返す"""
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)

        citing_title, cited_title = _compute_table_titles("")

        assert citing_title == "PEP N is cited by..."
        assert cited_title == "PEP N cites..."

    def test_existing_pep(self, mock_data_files, monkeypatch):
        """存在するPEP番号の場合はPEP番号入りのタイトルを返す"""
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)

        data_loader.clear_cache()

        citing_title, cited_title = _compute_table_titles(484)

        assert citing_title == "PEP 484 is cited by..."
        assert cited_title == "PEP 484 cites..."

    def test_nonexistent_pep(self, mock_data_files, monkeypatch):
        """存在しないPEP番号の場合はデフォルトのタイトルを返す"""
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)

        data_loader.clear_cache()

        citing_title, cited_title = _compute_table_titles(9999)

        assert citing_title == "PEP N is cited by..."
        assert cited_title == "PEP N cites..."


class TestAddPythonReleaseLines:
    """_add_python_release_lines関数のテスト"""

    def test_no_options_adds_no_shapes(
        self, mock_data_files, mock_static_dir, monkeypatch
    ):
        """オプションが空の場合はshapesを追加しない"""
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)
        monkeypatch.setattr(
            "src.dash_app.utils.data_loader.STATIC_DIR", mock_static_dir
        )
        data_loader.clear_cache()

        fig = go.Figure()
        _add_python_release_lines(fig, [])

        assert len(fig.layout.shapes) == 0
        assert len(fig.layout.annotations) == 0

    def test_python2_option_adds_shapes(
        self, mock_data_files, mock_static_dir, monkeypatch
    ):
        """python2オプションでshapesが追加される"""
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)
        monkeypatch.setattr(
            "src.dash_app.utils.data_loader.STATIC_DIR", mock_static_dir
        )
        data_loader.clear_cache()

        fig = go.Figure()
        _add_python_release_lines(fig, ["python2"])

        # Python 2系のリリース数（モックデータは2.7の1件）だけshapesが追加される
        assert len(fig.layout.shapes) == 1
        assert len(fig.layout.annotations) == 1

    def test_python3_option_adds_shapes(
        self, mock_data_files, mock_static_dir, monkeypatch
    ):
        """python3オプションでshapesが追加される"""
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)
        monkeypatch.setattr(
            "src.dash_app.utils.data_loader.STATIC_DIR", mock_static_dir
        )
        data_loader.clear_cache()

        fig = go.Figure()
        _add_python_release_lines(fig, ["python3"])

        # Python 3系のリリース数（モックデータは3.0, 3.10の2件）だけshapesが追加される
        assert len(fig.layout.shapes) == 2
        assert len(fig.layout.annotations) == 2

    def test_both_options_adds_all_shapes(
        self, mock_data_files, mock_static_dir, monkeypatch
    ):
        """両方のオプションでPython 2/3合計のshapesが追加される"""
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)
        monkeypatch.setattr(
            "src.dash_app.utils.data_loader.STATIC_DIR", mock_static_dir
        )
        data_loader.clear_cache()

        fig = go.Figure()
        _add_python_release_lines(fig, ["python2", "python3"])

        # Python 2（1件）+ Python 3（2件）= 3件
        assert len(fig.layout.shapes) == 3
        assert len(fig.layout.annotations) == 3


class TestAddReleaseLinesForMajorVersion:
    """_add_release_lines_for_major_version関数のテスト"""

    def test_python2_line_color_is_correct(self, mock_static_dir, monkeypatch):
        """Python 2縦線の色が正しい"""
        monkeypatch.setattr(
            "src.dash_app.utils.data_loader.STATIC_DIR", mock_static_dir
        )
        data_loader.clear_cache()

        fig = go.Figure()
        _add_release_lines_for_major_version(
            fig, 2, PYTHON_2_LINE_COLOR, TIMELINE_Y_PYTHON2_LABEL
        )

        # 追加されたshapeの色を確認
        assert len(fig.layout.shapes) > 0
        for shape in fig.layout.shapes:
            assert shape.line.color == PYTHON_2_LINE_COLOR

    def test_python3_line_color_is_correct(self, mock_static_dir, monkeypatch):
        """Python 3縦線の色が正しい"""
        monkeypatch.setattr(
            "src.dash_app.utils.data_loader.STATIC_DIR", mock_static_dir
        )
        data_loader.clear_cache()

        fig = go.Figure()
        _add_release_lines_for_major_version(
            fig, 3, PYTHON_3_LINE_COLOR, TIMELINE_Y_PYTHON3_LABEL
        )

        assert len(fig.layout.shapes) > 0
        for shape in fig.layout.shapes:
            assert shape.line.color == PYTHON_3_LINE_COLOR

    def test_annotation_count_matches_releases(self, mock_static_dir, monkeypatch):
        """追加されるアノテーション数がリリース数と一致する"""
        monkeypatch.setattr(
            "src.dash_app.utils.data_loader.STATIC_DIR", mock_static_dir
        )
        data_loader.clear_cache()

        fig = go.Figure()
        _add_release_lines_for_major_version(
            fig, 3, PYTHON_3_LINE_COLOR, TIMELINE_Y_PYTHON3_LABEL
        )

        # モックデータのPython 3系は3.0, 3.10の2件
        assert len(fig.layout.annotations) == 2

    def test_annotation_contains_version_text(self, mock_static_dir, monkeypatch):
        """アノテーションにバージョン番号が含まれる"""
        monkeypatch.setattr(
            "src.dash_app.utils.data_loader.STATIC_DIR", mock_static_dir
        )
        data_loader.clear_cache()

        fig = go.Figure()
        _add_release_lines_for_major_version(
            fig, 2, PYTHON_2_LINE_COLOR, TIMELINE_Y_PYTHON2_LABEL
        )

        # モックデータのPython 2系は2.7の1件
        annotation_texts = [ann.text for ann in fig.layout.annotations]
        assert "2.7" in annotation_texts
