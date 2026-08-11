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


def _collect_fields(column_defs: list[dict]) -> list[str]:
    """columnDefsからfield名をフラットに収集する（childrenを再帰展開）"""
    fields = []
    for col in column_defs:
        if "children" in col:
            fields.extend(_collect_fields(col["children"]))
        elif "field" in col:
            fields.append(col["field"])
    return fields


def test_citation_changes_table_columns():
    """AG Gridの列が正しく定義されていることを確認"""
    layout = create_citation_changes_tab_layout()

    # layout.children[3] がAG Grid
    grid = layout.children[3]

    expected_fields = [
        "detected",
        "change_type",
        "citing",
        "cited",
        "citing_title",
        "cited_title",
        "count_before",
        "count_after",
    ]
    actual_fields = _collect_fields(grid.columnDefs)
    assert actual_fields == expected_fields


def test_citation_changes_table_multi_headers():
    """AG Gridのマルチヘッダー（カラムグルーピング）が正しく定義されていることを確認"""
    layout = create_citation_changes_tab_layout()

    # layout.children[3] がAG Grid
    grid = layout.children[3]

    # グループヘッダーを持つ列を確認
    group_headers = [col["headerName"] for col in grid.columnDefs if "children" in col]
    assert group_headers == ["PEP", "Title", "Count"]

    # PEPグループの子列を確認
    pep_group = [col for col in grid.columnDefs if col.get("headerName") == "PEP"][0]
    pep_child_names = [c["headerName"] for c in pep_group["children"]]
    assert pep_child_names == ["Citing", "Cited"]
