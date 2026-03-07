"""Citation Changesデータローダーのテスト"""

import pytest

from src.dash_app.utils import data_loader


@pytest.fixture(autouse=True)
def setup(mock_data_files, monkeypatch):
    """各テストの前にキャッシュをクリアし、モックデータを使用"""
    # キャッシュをクリア
    data_loader.clear_cache()

    # DATA_DIRをモックデータディレクトリに変更
    from src.dash_app.utils import constants

    monkeypatch.setattr(constants, "DATA_DIR", mock_data_files)


def test_load_citation_changes_detected_format():
    """detected列がYYYY-MM-DD形式の文字列であることを確認"""
    df = data_loader.load_citation_changes()
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    assert df["detected"].str.match(pattern).all()


def test_load_citation_changes_count_empty_values():
    """count_before/count_afterの空値が'-'に変換されることを確認"""
    df = data_loader.load_citation_changes()
    assert df["count_before"].isna().sum() == 0
    assert df["count_after"].isna().sum() == 0


def test_load_citation_changes_count_integer_format():
    """数値が整数表記（小数点なし）であることを確認"""
    df = data_loader.load_citation_changes()

    before_numeric = df.loc[df["count_before"] != "-", "count_before"]
    after_numeric = df.loc[df["count_after"] != "-", "count_after"]

    assert before_numeric.str.isdigit().all()
    assert after_numeric.str.isdigit().all()


def test_load_citation_changes_titles_joined():
    """cited_title/citing_titleがpeps_metadataから正しく結合されることを確認"""
    df = data_loader.load_citation_changes()
    peps_df = data_loader.load_peps_metadata()

    row = df.iloc[0]
    expected = peps_df.loc[peps_df["pep_number"] == row["cited"], "title"]
    assert row["cited_title"] == expected.iloc[0]
