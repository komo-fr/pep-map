"""timeline.pyレイアウトモジュールのテスト"""

from dash import dcc, html

from src.dash_app.layouts.timeline import _create_python_release_checkboxes
from src.dash_app.utils.constants import PYTHON_2_LINE_COLOR, PYTHON_3_LINE_COLOR


def _find_checklist(component) -> dcc.Checklist | None:
    """コンポーネントツリーを再帰的に探索してChecklistを返す"""
    if (
        isinstance(component, dcc.Checklist)
        and getattr(component, "id", None) == "python-release-checkboxes"
    ):
        return component
    children = getattr(component, "children", None)
    if isinstance(children, list):
        for child in children:
            result = _find_checklist(child)
            if result is not None:
                return result
    elif children is not None:
        return _find_checklist(children)
    return None


class TestCreatePythonReleaseCheckboxes:
    """_create_python_release_checkboxes関数のテスト"""

    def test_returns_div(self):
        """html.Divを返す"""
        result = _create_python_release_checkboxes()

        assert isinstance(result, html.Div)

    def test_contains_checklist(self):
        """id='python-release-checkboxes' のdcc.Checklistを含む"""
        result = _create_python_release_checkboxes()

        checklist = _find_checklist(result)
        assert checklist is not None

    def test_checklist_has_two_options(self):
        """Checklistに2つのオプションがある"""
        result = _create_python_release_checkboxes()

        checklist = _find_checklist(result)
        assert len(checklist.options) == 2

    def test_checklist_option_values(self):
        """オプションのvalueが正しい"""
        result = _create_python_release_checkboxes()

        checklist = _find_checklist(result)
        values = [opt["value"] for opt in checklist.options]
        assert "python2" in values
        assert "python3" in values

    def test_checklist_default_value_is_empty(self):
        """デフォルトでは何もチェックされていない"""
        result = _create_python_release_checkboxes()

        checklist = _find_checklist(result)
        assert checklist.value == []

    def test_checklist_is_inline(self):
        """チェックボックスがinline表示になっている"""
        result = _create_python_release_checkboxes()

        checklist = _find_checklist(result)
        assert checklist.inline is True

    def test_python2_option_label_color(self):
        """Python 2オプションのラベルにPython 2の色が使われている"""
        result = _create_python_release_checkboxes()

        checklist = _find_checklist(result)
        python2_opt = next(
            opt for opt in checklist.options if opt["value"] == "python2"
        )

        # ラベルはhtml.Spanで、最初の子要素が色付きの線
        label_span = python2_opt["label"]
        assert isinstance(label_span, html.Span)
        color_line = label_span.children[0]
        assert isinstance(color_line, html.Span)
        assert color_line.style["backgroundColor"] == PYTHON_2_LINE_COLOR

    def test_python3_option_label_color(self):
        """Python 3オプションのラベルにPython 3の色が使われている"""
        result = _create_python_release_checkboxes()

        checklist = _find_checklist(result)
        python3_opt = next(
            opt for opt in checklist.options if opt["value"] == "python3"
        )

        label_span = python3_opt["label"]
        assert isinstance(label_span, html.Span)
        color_line = label_span.children[0]
        assert isinstance(color_line, html.Span)
        assert color_line.style["backgroundColor"] == PYTHON_3_LINE_COLOR

    def test_python2_option_label_text(self):
        """Python 2オプションのラベルテキストが正しい"""
        result = _create_python_release_checkboxes()

        checklist = _find_checklist(result)
        python2_opt = next(
            opt for opt in checklist.options if opt["value"] == "python2"
        )

        label_span = python2_opt["label"]
        assert label_span.children[1] == "Show Python 2 release dates"

    def test_python3_option_label_text(self):
        """Python 3オプションのラベルテキストが正しい"""
        result = _create_python_release_checkboxes()

        checklist = _find_checklist(result)
        python3_opt = next(
            opt for opt in checklist.options if opt["value"] == "python3"
        )

        label_span = python3_opt["label"]
        assert label_span.children[1] == "Show Python 3 release dates"
