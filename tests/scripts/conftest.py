"""fetch_peps.pyテスト用の共通フィクスチャ"""

import shutil
import tempfile
import zipfile
from pathlib import Path

import pytest


def create_pep_content(pep_number: int, citations: list[int] | None = None) -> str:
    """PEPファイルの内容を生成する。

    Args:
        pep_number: PEP番号
        citations: 引用するPEP番号のリスト

    Returns:
        PEP RSTファイルの内容
    """
    citation_text = ""
    if citations:
        citation_text = " that cites " + " and ".join(f":pep:`{c}`" for c in citations)

    return f"""PEP: {pep_number}
Title: Test PEP {pep_number}
Status: Active
Type: Process
Created: 2000-01-01
Author: Test Author

This is a test PEP{citation_text}.
"""


def create_pep_files(pep_dir: Path, peps: dict[int, list[int] | None]) -> None:
    """複数のPEPファイルを作成する。

    Args:
        pep_dir: PEPファイルを作成するディレクトリ
        peps: {pep_number: citations} の辞書。citationsはNoneまたは引用PEP番号のリスト
    """
    pep_dir.mkdir(parents=True, exist_ok=True)
    for pep_number, citations in peps.items():
        content = create_pep_content(pep_number, citations)
        (pep_dir / f"pep-{pep_number:04d}.rst").write_text(content, encoding="utf-8")


def create_mock_zip(zip_path: Path, pep_dir: Path) -> Path:
    """PEPディレクトリからモックのzipファイルを作成する。

    Args:
        zip_path: 作成するzipファイルのパス
        pep_dir: PEPファイルが含まれるディレクトリ

    Returns:
        作成されたzipファイルのパス
    """
    with zipfile.ZipFile(zip_path, "w") as zf:
        for pep_file in pep_dir.glob("*.rst"):
            arcname = f"peps-main/peps/{pep_file.name}"
            zf.write(pep_file, arcname)
    return zip_path


@pytest.fixture
def temp_dir():
    """テスト用の一時ディレクトリを作成する。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_download_setup(temp_dir, monkeypatch):
    """モックダウンロードをセットアップするファクトリフィクスチャ。

    Returns:
        setup関数。peps引数で{pep_number: citations}を渡すとモックをセットアップする。
    """

    def _setup(peps: dict[int, list[int] | None]):
        # PEPファイルを作成
        pep_dir = temp_dir / f"peps_{id(peps)}"
        create_pep_files(pep_dir, peps)

        # zipファイルを作成
        zip_path = temp_dir / f"mock_peps_{id(peps)}.zip"
        create_mock_zip(zip_path, pep_dir)

        # モックをセットアップ
        def mock_download_repo(self, url, output_path, timeout=60):
            shutil.copy(zip_path, output_path)
            return output_path

        monkeypatch.setattr(
            "src.data_acquisition.github_fetcher.PEPFetcher.download_repo",
            mock_download_repo,
        )

    return _setup
