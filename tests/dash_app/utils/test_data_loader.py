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

    def test_load_node_metrics(self, mock_data_files, monkeypatch):
        """node_metrics.csvが正しく読み込まれるか"""
        # キャッシュをクリア
        data_loader.clear_cache()

        # DATA_DIRをモック
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)

        df = data_loader.load_node_metrics()

        assert isinstance(df, pd.DataFrame)
        assert "pep_number" in df.columns
        assert "in_degree" in df.columns
        assert "out_degree" in df.columns
        assert "degree" in df.columns
        assert "pagerank" in df.columns

    def test_load_node_metrics_caching(self, mock_data_files, monkeypatch):
        """2回目以降はキャッシュから読み込まれるか"""
        # キャッシュをクリア
        data_loader.clear_cache()

        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)

        # 1回目の読み込み
        df1 = data_loader.load_node_metrics()
        # 2回目の読み込み（キャッシュから）
        df2 = data_loader.load_node_metrics()

        # 同じオブジェクトであることを確認
        assert df1 is df2

    def test_load_node_metrics_file_not_found(self, tmp_path, monkeypatch):
        """node_metrics.csvが存在しない場合は空のDataFrameを返す"""
        # キャッシュをクリア
        data_loader.clear_cache()

        # 空のディレクトリを使用
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", empty_dir)

        df = data_loader.load_node_metrics()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert list(df.columns) == [
            "pep_number",
            "in_degree",
            "out_degree",
            "degree",
            "pagerank",
        ]


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

    def test_returns_dataframe(self, mock_static_dir, monkeypatch):
        """DataFrameを返す"""
        monkeypatch.setattr(
            "src.dash_app.utils.data_loader.STATIC_DIR", mock_static_dir
        )
        data_loader.clear_cache()

        df = data_loader.load_python_releases()

        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self, mock_static_dir, monkeypatch):
        """必要な列が存在する"""
        monkeypatch.setattr(
            "src.dash_app.utils.data_loader.STATIC_DIR", mock_static_dir
        )
        data_loader.clear_cache()

        df = data_loader.load_python_releases()

        assert "version" in df.columns
        assert "release_date" in df.columns
        assert "major_version" in df.columns

    def test_release_date_is_datetime(self, mock_static_dir, monkeypatch):
        """release_date列がdatetime型"""
        monkeypatch.setattr(
            "src.dash_app.utils.data_loader.STATIC_DIR", mock_static_dir
        )
        data_loader.clear_cache()

        df = data_loader.load_python_releases()

        assert pd.api.types.is_datetime64_any_dtype(df["release_date"])

    def test_major_version_is_int(self, mock_static_dir, monkeypatch):
        """major_version列がint型"""
        monkeypatch.setattr(
            "src.dash_app.utils.data_loader.STATIC_DIR", mock_static_dir
        )
        data_loader.clear_cache()

        df = data_loader.load_python_releases()

        assert pd.api.types.is_integer_dtype(df["major_version"])

    def test_python_releases_cache(self, mock_static_dir, monkeypatch):
        """キャッシュが機能する"""
        monkeypatch.setattr(
            "src.dash_app.utils.data_loader.STATIC_DIR", mock_static_dir
        )
        data_loader.clear_cache()

        # 1回目の読み込み
        df1 = data_loader.load_python_releases()
        # 2回目の読み込み（キャッシュから）
        df2 = data_loader.load_python_releases()

        # 同じオブジェクトであることを確認
        assert df1 is df2


class TestGetPythonReleasesByMajorVersion:
    """get_python_releases_by_major_version関数のテスト"""

    def test_filter_python2(self, mock_static_dir, monkeypatch):
        """Python 2系のみフィルタリング"""
        monkeypatch.setattr(
            "src.dash_app.utils.data_loader.STATIC_DIR", mock_static_dir
        )
        data_loader.clear_cache()

        df = data_loader.get_python_releases_by_major_version(2)

        assert all(df["major_version"] == 2)

    def test_filter_python3(self, mock_static_dir, monkeypatch):
        """Python 3系のみフィルタリング"""
        monkeypatch.setattr(
            "src.dash_app.utils.data_loader.STATIC_DIR", mock_static_dir
        )
        data_loader.clear_cache()

        df = data_loader.get_python_releases_by_major_version(3)

        assert all(df["major_version"] == 3)

    def test_returns_copy(self, mock_static_dir, monkeypatch):
        """返すDataFrameは独立したコピー"""
        monkeypatch.setattr(
            "src.dash_app.utils.data_loader.STATIC_DIR", mock_static_dir
        )
        data_loader.clear_cache()

        df1 = data_loader.get_python_releases_by_major_version(2)
        df2 = data_loader.get_python_releases_by_major_version(2)

        # 異なるオブジェクトであることを確認
        assert df1 is not df2
        # しかしデータは同じであることを確認
        assert df1.equals(df2)


class TestGetPythonReleasesForStore:
    """get_python_releases_for_store関数のテスト"""

    def test_returns_dict(self, mock_static_dir, monkeypatch):
        """dict型を返す"""
        monkeypatch.setattr(
            "src.dash_app.utils.data_loader.STATIC_DIR", mock_static_dir
        )
        data_loader.clear_cache()

        result = data_loader.get_python_releases_for_store()

        assert isinstance(result, dict)

    def test_has_python2_and_python3_keys(self, mock_static_dir, monkeypatch):
        """python2とpython3キーが存在する"""
        monkeypatch.setattr(
            "src.dash_app.utils.data_loader.STATIC_DIR", mock_static_dir
        )
        data_loader.clear_cache()

        result = data_loader.get_python_releases_for_store()

        assert "python2" in result
        assert "python3" in result

    def test_values_are_lists(self, mock_static_dir, monkeypatch):
        """各キーの値がリスト"""
        monkeypatch.setattr(
            "src.dash_app.utils.data_loader.STATIC_DIR", mock_static_dir
        )
        data_loader.clear_cache()

        result = data_loader.get_python_releases_for_store()

        assert isinstance(result["python2"], list)
        assert isinstance(result["python3"], list)

    def test_python2_list_structure(self, mock_static_dir, monkeypatch):
        """python2リストの要素が正しい構造"""
        monkeypatch.setattr(
            "src.dash_app.utils.data_loader.STATIC_DIR", mock_static_dir
        )
        data_loader.clear_cache()

        result = data_loader.get_python_releases_for_store()
        python2_data = result["python2"]

        # モックデータには2.7が1件含まれる
        assert len(python2_data) == 1
        assert "version" in python2_data[0]
        assert "release_date" in python2_data[0]

    def test_python3_list_structure(self, mock_static_dir, monkeypatch):
        """python3リストの要素が正しい構造"""
        monkeypatch.setattr(
            "src.dash_app.utils.data_loader.STATIC_DIR", mock_static_dir
        )
        data_loader.clear_cache()

        result = data_loader.get_python_releases_for_store()
        python3_data = result["python3"]

        # モックデータには3.0と3.10の2件が含まれる
        assert len(python3_data) == 2
        for item in python3_data:
            assert "version" in item
            assert "release_date" in item

    def test_release_date_format(self, mock_static_dir, monkeypatch):
        """release_dateが文字列でISO形式（YYYY-MM-DD）"""
        monkeypatch.setattr(
            "src.dash_app.utils.data_loader.STATIC_DIR", mock_static_dir
        )
        data_loader.clear_cache()

        result = data_loader.get_python_releases_for_store()

        # Python 2のrelease_dateをチェック
        for item in result["python2"]:
            assert isinstance(item["release_date"], str)
            # YYYY-MM-DD形式であることを確認
            import re

            assert re.match(r"\d{4}-\d{2}-\d{2}", item["release_date"])

        # Python 3のrelease_dateをチェック
        for item in result["python3"]:
            assert isinstance(item["release_date"], str)
            import re

            assert re.match(r"\d{4}-\d{2}-\d{2}", item["release_date"])

    def test_version_is_string(self, mock_static_dir, monkeypatch):
        """versionが文字列"""
        monkeypatch.setattr(
            "src.dash_app.utils.data_loader.STATIC_DIR", mock_static_dir
        )
        data_loader.clear_cache()

        result = data_loader.get_python_releases_for_store()

        for item in result["python2"] + result["python3"]:
            assert isinstance(item["version"], str)


class TestLoadPepsWithMetrics:
    """load_peps_with_metrics関数のテスト"""

    def test_load_peps_with_metrics(self, mock_data_files, monkeypatch):
        """PEP基本情報とメトリクスが統合されるか"""
        # キャッシュをクリア
        data_loader.clear_cache()

        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)

        df = data_loader.load_peps_with_metrics()

        # peps_metadata.csvの列
        assert "pep_number" in df.columns
        assert "title" in df.columns
        assert "status" in df.columns

        # node_metrics.csvの列
        assert "in_degree" in df.columns
        assert "out_degree" in df.columns
        assert "degree" in df.columns
        assert "pagerank" in df.columns

    def test_load_peps_with_metrics_left_join(self, tmp_path, monkeypatch):
        """メトリクスがないPEPも含まれるか（left join）"""
        # キャッシュをクリア
        data_loader.clear_cache()

        # テストデータを作成
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        # peps_metadata.csv（PEP 1, 2, 3）
        peps_csv = data_dir / "peps_metadata.csv"
        peps_csv.write_text(
            "pep_number,title,status,type,created,authors,topic,requires,replaces\n"
            "1,Test PEP 1,Active,Process,01-Jan-2000,Author 1,,,\n"
            "2,Test PEP 2,Draft,Standards Track,02-Jan-2000,Author 2,,,\n"
            "3,Test PEP 3,Final,Standards Track,03-Jan-2000,Author 3,,,\n"
        )

        # node_metrics.csv（PEP 1, 2のみ。PEP 3はなし）
        metrics_csv = data_dir / "node_metrics.csv"
        metrics_csv.write_text(
            "pep_number,in_degree,out_degree,degree,pagerank\n"
            "1,0,2,2,0.3\n"
            "2,1,1,2,0.7\n"
        )

        # citations.csv（ダミー）
        citations_csv = data_dir / "citations.csv"
        citations_csv.write_text("citing,cited,count\n")

        # metadata.json（ダミー）
        metadata_json = data_dir / "metadata.json"
        metadata_json.write_text('{"fetched_at": "2026-01-01T00:00:00+00:00"}')

        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", data_dir)

        df = data_loader.load_peps_with_metrics()

        # 全PEPが含まれていることを確認
        assert len(df) == 3
        assert set(df["pep_number"]) == {1, 2, 3}

        # PEP 3のメトリクスがNaNであることを確認
        pep3 = df[df["pep_number"] == 3].iloc[0]
        assert pd.isna(pep3["pagerank"])


class TestClearCache:
    """clear_cache関数のテスト"""

    def test_clear_cache(self, mock_data_files, mock_static_dir, monkeypatch):
        """キャッシュがクリアされる"""
        monkeypatch.setattr("src.dash_app.utils.data_loader.DATA_DIR", mock_data_files)
        monkeypatch.setattr(
            "src.dash_app.utils.data_loader.STATIC_DIR", mock_static_dir
        )

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
