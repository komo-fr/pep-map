"""data_loaderモジュールのテスト"""

import pandas as pd
import pytest

from src.dash_app.utils import data_loader


class TestLoadFunctions:
    """データ読み込み関数のテスト"""

    def test_load_peps_metadata(self, mock_data_files, monkeypatch):
        """PEPメタデータを正常に読み込める"""
        # キャッシュをクリア
        data_loader.clear_cache()

        # DATA_DIRをモック
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)

        df = data_loader.load_peps_metadata()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "pep_number" in df.columns
        assert df["pep_number"].tolist() == [8, 484, 3107]

    def test_load_peps_metadata_cache(self, mock_data_files, monkeypatch):
        """キャッシュが機能する"""
        data_loader.clear_cache()
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)

        # 1回目の読み込み
        df1 = data_loader.load_peps_metadata()
        # 2回目の読み込み（キャッシュから）
        df2 = data_loader.load_peps_metadata()

        # 同じオブジェクトであることを確認
        assert df1 is df2

    def test_load_citations(self, mock_data_files, monkeypatch):
        """引用関係データを正常に読み込める"""
        data_loader.clear_cache()
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)

        df = data_loader.load_citations()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "citing" in df.columns
        assert "cited" in df.columns
        assert "count" in df.columns

    def test_load_citations_cache(self, mock_data_files, monkeypatch):
        """引用関係データのキャッシュが機能する"""
        data_loader.clear_cache()
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)

        # 1回目の読み込み
        df1 = data_loader.load_citations()
        # 2回目の読み込み（キャッシュから）
        df2 = data_loader.load_citations()

        # 同じオブジェクトであることを確認
        assert df1 is df2

    def test_load_metadata(self, mock_data_files, monkeypatch):
        """メタデータを正常に読み込める"""
        data_loader.clear_cache()
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)

        metadata = data_loader.load_metadata()

        assert isinstance(metadata, dict)
        assert "fetched_at" in metadata
        assert "source_url" in metadata

    def test_load_metadata_date_format(self, mock_data_files, monkeypatch):
        """メタデータの日付フォーマットが正しい"""
        data_loader.clear_cache()
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)

        metadata = data_loader.load_metadata()

        # YYYY-MM-DD形式であることを確認
        assert metadata["fetched_at"] == "2026-02-14 00:00 (UTC)"
        # ISO形式の日付がパースされていることを確認
        import re

        assert re.match(r"\d{4}-\d{2}-\d{2}", metadata["fetched_at"])


class TestGetPepByNumber:
    """get_pep_by_number関数のテスト"""

    def test_get_pep_by_number_exists(self, mock_data_files, monkeypatch):
        """存在するPEPを取得できる"""
        data_loader.clear_cache()
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)

        pep = data_loader.get_pep_by_number(484)

        assert pep is not None
        assert pep["pep_number"] == 484
        assert pep["title"] == "Type Hints"

    def test_get_pep_by_number_not_exists(self, mock_data_files, monkeypatch):
        """存在しないPEPはNoneを返す"""
        data_loader.clear_cache()
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)

        pep = data_loader.get_pep_by_number(9999)

        assert pep is None


class TestCitationFunctions:
    """引用関係取得関数のテスト"""

    def test_get_citing_peps(self, mock_data_files, monkeypatch):
        """引用元PEPを取得できる"""
        data_loader.clear_cache()
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)

        # PEP 3107を引用しているPEPを取得
        citing = data_loader.get_citing_peps(3107)

        assert len(citing) == 1
        assert citing.iloc[0]["pep_number"] == 484

    def test_get_citing_peps_empty(self, mock_data_files, monkeypatch):
        """引用元がない場合は空のDataFrameを返す"""
        data_loader.clear_cache()
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)

        citing = data_loader.get_citing_peps(9999)

        assert len(citing) == 0

    def test_get_cited_peps(self, mock_data_files, monkeypatch):
        """引用先PEPを取得できる"""
        data_loader.clear_cache()
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)

        # PEP 484が引用しているPEPを取得
        cited = data_loader.get_cited_peps(484)

        assert len(cited) == 2
        # 作成日で昇順ソートされていることを確認
        assert cited.iloc[0]["pep_number"] == 3107  # 2000-01-01（最も古い）
        assert cited.iloc[1]["pep_number"] == 8  # 2001-07-05

    def test_get_cited_peps_empty(self, mock_data_files, monkeypatch):
        """引用先がない場合は空のDataFrameを返す"""
        data_loader.clear_cache()
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)

        cited = data_loader.get_cited_peps(9999)

        assert len(cited) == 0


class TestGeneratePepUrl:
    """generate_pep_url関数のテスト"""

    @pytest.mark.parametrize(
        "pep_number,expected",
        [
            (8, "https://peps.python.org/pep-0008/"),
            (484, "https://peps.python.org/pep-0484/"),
            (3107, "https://peps.python.org/pep-3107/"),
        ],
    )
    def test_generate_pep_url(self, pep_number, expected):
        """正しいURLを生成する"""
        url = data_loader.generate_pep_url(pep_number)
        assert url == expected


class TestLoadPythonReleases:
    """load_python_releases関数のテスト"""

    def test_returns_dataframe(self, mock_data_files, monkeypatch):
        """DataFrameを返す"""
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)
        data_loader.clear_cache()

        df = data_loader.load_python_releases()

        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self, mock_data_files, monkeypatch):
        """必要な列が存在する"""
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)
        data_loader.clear_cache()

        df = data_loader.load_python_releases()

        assert "version" in df.columns
        assert "release_date" in df.columns
        assert "major_version" in df.columns

    def test_release_date_is_datetime(self, mock_data_files, monkeypatch):
        """release_date列がdatetime型"""
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)
        data_loader.clear_cache()

        df = data_loader.load_python_releases()

        assert pd.api.types.is_datetime64_any_dtype(df["release_date"])

    def test_major_version_is_int(self, mock_data_files, monkeypatch):
        """major_version列がint型"""
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)
        data_loader.clear_cache()

        df = data_loader.load_python_releases()

        assert pd.api.types.is_integer_dtype(df["major_version"])

    def test_python_releases_cache(self, mock_data_files, monkeypatch):
        """キャッシュが機能する"""
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)
        data_loader.clear_cache()

        # 1回目の読み込み
        df1 = data_loader.load_python_releases()
        # 2回目の読み込み（キャッシュから）
        df2 = data_loader.load_python_releases()

        # 同じオブジェクトであることを確認
        assert df1 is df2


class TestGetPythonReleasesByMajorVersion:
    """get_python_releases_by_major_version関数のテスト"""

    def test_filter_python2(self, mock_data_files, monkeypatch):
        """Python 2系のみフィルタリング"""
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)
        data_loader.clear_cache()

        df = data_loader.get_python_releases_by_major_version(2)

        assert all(df["major_version"] == 2)

    def test_filter_python3(self, mock_data_files, monkeypatch):
        """Python 3系のみフィルタリング"""
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)
        data_loader.clear_cache()

        df = data_loader.get_python_releases_by_major_version(3)

        assert all(df["major_version"] == 3)

    def test_returns_copy(self, mock_data_files, monkeypatch):
        """返すDataFrameは独立したコピー"""
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)
        data_loader.clear_cache()

        df1 = data_loader.get_python_releases_by_major_version(2)
        df2 = data_loader.get_python_releases_by_major_version(2)

        # 異なるオブジェクトであることを確認
        assert df1 is not df2
        # しかしデータは同じであることを確認
        assert df1.equals(df2)


class TestClearCache:
    """clear_cache関数のテスト"""

    def test_clear_cache(self, mock_data_files, monkeypatch):
        """キャッシュがクリアされる"""
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)

        # キャッシュをクリア
        data_loader.clear_cache()

        # データを読み込む（キャッシュに保存）
        df1 = data_loader.load_peps_metadata()
        citations1 = data_loader.load_citations()
        metadata1 = data_loader.load_metadata()
        releases1 = data_loader.load_python_releases()

        # キャッシュをクリア
        data_loader.clear_cache()

        # 再度読み込む（新しいオブジェクトが作成される）
        df2 = data_loader.load_peps_metadata()
        citations2 = data_loader.load_citations()
        metadata2 = data_loader.load_metadata()
        releases2 = data_loader.load_python_releases()

        # 異なるオブジェクトであることを確認（キャッシュがクリアされた）
        assert df1 is not df2
        assert citations1 is not citations2
        assert metadata1 is not metadata2
        assert releases1 is not releases2
