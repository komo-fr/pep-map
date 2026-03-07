"""citation_changes_tab.pyレイアウトモジュールのテスト"""

import pytest
from dash import html

from src.dash_app.layouts.citation_changes_tab import create_citation_changes_tab_layout
from src.dash_app.utils import constants, data_loader


@pytest.fixture(autouse=True)
def setup(mock_data_files, monkeypatch):
    """各テストの前にキャッシュをクリアし、モックデータを使用"""
    # キャッシュをクリア
    data_loader.clear_cache()

    # DATA_DIRをモックデータディレクトリに変更
    monkeypatch.setattr(constants, "DATA_DIR", mock_data_files)


def test_citation_changes_tab_layout_returns_div():
    """create_citation_changes_tab_layoutがhtml.Divを返すことを確認"""
    layout = create_citation_changes_tab_layout()
    assert isinstance(layout, html.Div)


def test_citation_changes_table_columns():
    """DataTableの列が正しく定義されていることを確認"""
    layout = create_citation_changes_tab_layout()

    # layout.children[3] がDataTable
    datatable = layout.children[3]

    expected_column_ids = [
        "detected",
        "change_type",
        "citing",
        "cited",
        "citing_title",
        "cited_title",
        "count_before",
        "count_after",
    ]
    actual_column_ids = [col["id"] for col in datatable.columns]
    assert actual_column_ids == expected_column_ids


def test_citation_changes_table_multi_headers():
    """DataTableのマルチヘッダーが正しく定義されていることを確認"""
    layout = create_citation_changes_tab_layout()

    # layout.children[3] がDataTable
    datatable = layout.children[3]

    # merge_duplicate_headersが設定されていることを確認
    assert datatable.merge_duplicate_headers is True

    # 各列のヘッダー構造を確認
    expected_headers = [
        ["", "Detected"],
        ["", "Change"],
        ["PEP", "Citing"],
        ["PEP", "Cited"],
        ["Title", "Citing"],
        ["Title", "Cited"],
        ["Count", "Before"],
        ["Count", "After"],
    ]
    actual_headers = [col["name"] for col in datatable.columns]
    assert actual_headers == expected_headers
