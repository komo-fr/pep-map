"""テスト用の共通フィクスチャ"""

from pathlib import Path

import pytest


@pytest.fixture
def sample_data_dir():
    """サンプルデータディレクトリのパスを返す"""
    return Path(__file__).parent / "fixtures"
