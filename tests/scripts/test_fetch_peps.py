"""Tests for fetch_peps.py script."""

import csv
import shutil
import tempfile
import zipfile
from pathlib import Path

import pytest

from scripts.fetch_peps import (
    main,
    parse_arguments,
)


class TestFetchPepsHelpers:
    """Test cases for fetch_peps.py helper functions."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_parse_arguments_defaults(self):
        """Test parse_arguments with default values."""
        args = parse_arguments([])

        assert args.output_dir == "data/processed"
        assert args.keep_raw is False
        assert args.verbose is False

    def test_parse_arguments_custom_values(self):
        """Test parse_arguments with custom values."""
        args = parse_arguments(
            ["--output-dir", "custom/output", "--keep-raw", "--verbose"]
        )

        assert args.output_dir == "custom/output"
        assert args.keep_raw is True
        assert args.verbose is True


class TestFetchPepsIntegration:
    """Integration tests for fetch_peps.py main workflow."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_pep_files(self, temp_dir):
        """Create sample PEP RST files for testing."""
        pep_dir = temp_dir / "peps"
        pep_dir.mkdir()

        # PEP 1
        (pep_dir / "pep-0001.rst").write_text(
            """PEP: 1
Title: Test PEP 1
Status: Active
Type: Process
Created: 2000-01-01
Author: Author One

This is a test PEP that cites :pep:`8`.
""",
            encoding="utf-8",
        )

        # PEP 8
        (pep_dir / "pep-0008.rst").write_text(
            """PEP: 8
Title: Test PEP 8
Status: Active
Type: Process
Created: 2001-01-01
Author: Author Two, Author Three

This is a test PEP.
""",
            encoding="utf-8",
        )

        return pep_dir

    def test_main_output_files_created(self, temp_dir, sample_pep_files, monkeypatch):
        """Test that main() creates all three output files."""
        # モックのzipファイルを作成
        zip_path = temp_dir / "mock_peps.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for pep_file in sample_pep_files.glob("*.rst"):
                arcname = f"peps-main/peps/{pep_file.name}"
                zf.write(pep_file, arcname)

        output_dir = temp_dir / "output"

        # PEPFetcherのメソッドをモック
        def mock_download_repo(self, url, output_path, timeout=60):
            # モックのzipファイルをコピー
            shutil.copy(zip_path, output_path)
            return output_path

        # main()をテスト用引数で実行
        monkeypatch.setattr(
            "src.data_acquisition.github_fetcher.PEPFetcher.download_repo",
            mock_download_repo,
        )
        monkeypatch.setattr(
            "sys.argv",
            ["fetch_peps.py", "--output-dir", str(output_dir), "--keep-raw"],
        )

        # main()を実行
        exit_code = main()

        # 初回実行なので終了コード2（データ変更あり）を確認
        assert exit_code == 2

        # 3つの出力ファイルが作成されたか確認
        assert (output_dir / "peps_metadata.csv").exists()
        assert (output_dir / "citations.csv").exists()
        assert (output_dir / "metadata.json").exists()

    def test_main_citations_csv_has_correct_format(
        self, temp_dir, sample_pep_files, monkeypatch
    ):
        """Test that citations.csv has the correct format."""
        # モックのzipファイルを作成
        zip_path = temp_dir / "mock_peps.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for pep_file in sample_pep_files.glob("*.rst"):
                arcname = f"peps-main/peps/{pep_file.name}"
                zf.write(pep_file, arcname)

        output_dir = temp_dir / "output"

        # PEPFetcherのメソッドをモック
        def mock_download_repo(self, url, output_path, timeout=60):
            shutil.copy(zip_path, output_path)
            return output_path

        monkeypatch.setattr(
            "src.data_acquisition.github_fetcher.PEPFetcher.download_repo",
            mock_download_repo,
        )
        monkeypatch.setattr(
            "sys.argv",
            ["fetch_peps.py", "--output-dir", str(output_dir)],
        )

        # main()を実行
        exit_code = main()

        # 初回実行なので終了コード2（データ変更あり）を確認
        assert exit_code == 2

        # citations.csvのフォーマットを確認
        citations_path = output_dir / "citations.csv"
        assert citations_path.exists()

        with open(citations_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames

        # 正しいカラムが存在するか確認
        expected_columns = ["citing", "cited", "count"]
        assert fieldnames == expected_columns

    def test_main_no_data_change_on_second_run(
        self, temp_dir, sample_pep_files, monkeypatch
    ):
        """Test that running main() twice with the same data returns exit code 0 on second run."""
        # モックのzipファイルを作成
        zip_path = temp_dir / "mock_peps.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for pep_file in sample_pep_files.glob("*.rst"):
                arcname = f"peps-main/peps/{pep_file.name}"
                zf.write(pep_file, arcname)

        output_dir = temp_dir / "output"

        # PEPFetcherのメソッドをモック
        def mock_download_repo(self, url, output_path, timeout=60):
            shutil.copy(zip_path, output_path)
            return output_path

        monkeypatch.setattr(
            "src.data_acquisition.github_fetcher.PEPFetcher.download_repo",
            mock_download_repo,
        )
        monkeypatch.setattr(
            "sys.argv",
            ["fetch_peps.py", "--output-dir", str(output_dir)],
        )

        # 1回目の実行
        exit_code_first = main()
        # 初回実行なので終了コード2（データ変更あり）
        assert exit_code_first == 2

        # 2回目の実行（同じデータ）
        exit_code_second = main()
        # データ変更なしなので終了コード0
        assert exit_code_second == 0
