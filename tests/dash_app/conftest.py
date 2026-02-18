"""Dashアプリケーションテスト用の共通フィクスチャ"""

import json

import pandas as pd
import pytest


@pytest.fixture
def sample_peps_metadata():
    """テスト用PEPメタデータのDataFrame"""
    return pd.DataFrame(
        [
            {
                "pep_number": 8,
                "title": "Style Guide for Python Code",
                "status": "Active",
                "type": "Process",
                "created": pd.Timestamp("2001-07-05"),
                "authors": "Guido van Rossum, Barry Warsaw, Alyssa Coghlan",
                "topic": "",
                "requires": "",
                "replaces": "",
            },
            {
                "pep_number": 484,
                "title": "Type Hints",
                "status": "Final",
                "type": "Standards Track",
                "created": pd.Timestamp("2014-09-29"),
                "authors": "Guido van Rossum, Jukka Lehtosalo, Łukasz Langa",
                "topic": "typing",
                "requires": "",
                "replaces": "",
            },
            {
                "pep_number": 3107,
                "title": "Function Annotations",
                "status": "Final",
                "type": "Standards Track",
                "created": pd.Timestamp("2000-01-01"),
                "authors": "Collin Winter, Tony Lownds",
                "topic": "",
                "requires": "",
                "replaces": "",
            },
        ]
    )


@pytest.fixture
def sample_citations():
    """テスト用引用関係のDataFrame"""
    return pd.DataFrame(
        [
            {"citing": 484, "cited": 3107, "count": 5},
            {"citing": 8, "cited": 484, "count": 2},
            {"citing": 484, "cited": 8, "count": 1},
        ]
    )


@pytest.fixture
def sample_metadata():
    """テスト用メタデータの辞書"""
    return {
        "fetched_at": "2026-02-14",
        "source_url": "https://github.com/python/peps/archive/refs/heads/main.zip",
    }


@pytest.fixture
def sample_python_releases():
    """テスト用Pythonリリース日のDataFrame"""
    return pd.DataFrame(
        [
            {"version": "2.7", "release_date": "2010/07/04"},
            {"version": "3.0", "release_date": "2008/12/03"},
            {"version": "3.10", "release_date": "2021/10/04"},
        ]
    )


@pytest.fixture
def mock_data_files(
    tmp_path,
    sample_peps_metadata,
    sample_citations,
    sample_metadata,
    sample_python_releases,
):
    """テスト用データファイルを一時ディレクトリに作成"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # CSVファイル作成
    peps_csv = data_dir / "peps_metadata.csv"
    sample_peps_metadata.to_csv(peps_csv, index=False, date_format="%d-%b-%Y")

    citations_csv = data_dir / "citations.csv"
    sample_citations.to_csv(citations_csv, index=False)

    python_releases_csv = data_dir / "python_release_dates.csv"
    sample_python_releases.to_csv(python_releases_csv, index=False)

    # JSONファイル作成
    metadata_json = data_dir / "metadata.json"
    metadata_json.write_text(
        json.dumps(
            {"fetched_at": "2026-02-14T15:25:50.027772+00:00", **sample_metadata}
        ),
        encoding="utf-8",
    )

    return data_dir
