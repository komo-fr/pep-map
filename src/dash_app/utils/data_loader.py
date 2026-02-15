"""データ読み込みモジュール"""

import json
from datetime import datetime

import pandas as pd

from src.dash_app.utils.constants import DATA_DIR


# モジュールレベルでキャッシュ（アプリ起動時に一度だけ読み込む）
_peps_metadata_cache: pd.DataFrame | None = None
_citations_cache: pd.DataFrame | None = None
_metadata_cache: dict | None = None


def load_peps_metadata() -> pd.DataFrame:
    """
    PEPメタデータを読み込む

    Returns:
        pd.DataFrame: PEPメタデータのDataFrame

    列:
        - pep_number (int): PEP番号
        - title (str): タイトル
        - status (str): ステータス
        - type (str): タイプ
        - created (datetime): 作成日
        - authors (str): 著者
        - topic (str): トピック
        - requires (str): 必要とするPEP
        - replaces (str): 置き換えるPEP
    """
    global _peps_metadata_cache

    if _peps_metadata_cache is not None:
        return _peps_metadata_cache

    file_path = DATA_DIR / "peps_metadata.csv"

    df = pd.read_csv(file_path)

    # created列を日付型に変換
    # フォーマット: "13-Jun-2000" → %d-%b-%Y
    df["created"] = pd.to_datetime(df["created"], format="%d-%b-%Y")

    _peps_metadata_cache = df
    return df


def load_citations() -> pd.DataFrame:
    """
    引用関係データを読み込む

    Returns:
        pd.DataFrame: 引用関係のDataFrame

    列:
        - citing (int): 引用元PEP番号
        - cited (int): 引用先PEP番号
        - count (int): 引用回数
    """
    global _citations_cache

    if _citations_cache is not None:
        return _citations_cache

    file_path = DATA_DIR / "citations.csv"

    df = pd.read_csv(file_path)

    _citations_cache = df
    return df


def load_metadata() -> dict:
    """
    取得メタデータを読み込む

    Returns:
        dict: メタデータの辞書
            - fetched_at (str): データ取得日（YYYY-MM-DD形式）
            - source_url (str): データ取得元URL
    """
    global _metadata_cache

    if _metadata_cache is not None:
        return _metadata_cache

    file_path = DATA_DIR / "metadata.json"

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    # fetched_at を YYYY-MM-DD 形式に変換
    # 元のフォーマット: "2026-02-14T15:25:50.027772+00:00"
    fetched_at_str = data["fetched_at"]
    fetched_at_dt = datetime.fromisoformat(fetched_at_str)
    data["fetched_at"] = fetched_at_dt.strftime("%Y-%m-%d")

    _metadata_cache = data
    return data


def get_pep_by_number(pep_number: int) -> pd.Series | None:
    """
    指定したPEP番号のメタデータを取得する

    Args:
        pep_number: PEP番号

    Returns:
        pd.Series | None: PEPのメタデータ。存在しない場合はNone
    """
    df = load_peps_metadata()
    result = df[df["pep_number"] == pep_number]

    if result.empty:
        return None

    return result.iloc[0]


def get_citing_peps(pep_number: int) -> pd.DataFrame:
    """
    指定したPEPを引用しているPEPを取得する

    「選択中PEPを引用しているPEP」= citations.csvで cited == pep_number となるPEP

    Args:
        pep_number: PEP番号

    Returns:
        pd.DataFrame: 引用しているPEPのメタデータ
            列: pep_number, title, status, type, created, authors, topic, requires, replaces
    """
    citations = load_citations()
    peps_metadata = load_peps_metadata()

    # cited == pep_number となる行を抽出し、citing列を取得
    citing_pep_numbers = citations[citations["cited"] == pep_number]["citing"].tolist()

    # 該当するPEPのメタデータを取得
    result = peps_metadata[peps_metadata["pep_number"].isin(citing_pep_numbers)]

    # PEP番号で昇順ソート
    result = result.sort_values("pep_number").reset_index(drop=True)

    return result


def get_cited_peps(pep_number: int) -> pd.DataFrame:
    """
    指定したPEPから引用されているPEPを取得する

    「選択中PEPから引用されているPEP」= citations.csvで citing == pep_number となるPEP

    Args:
        pep_number: PEP番号

    Returns:
        pd.DataFrame: 引用されているPEPのメタデータ
            列: pep_number, title, status, type, created, authors, topic, requires, replaces
    """
    citations = load_citations()
    peps_metadata = load_peps_metadata()

    # citing == pep_number となる行を抽出し、cited列を取得
    cited_pep_numbers = citations[citations["citing"] == pep_number]["cited"].tolist()

    # 該当するPEPのメタデータを取得
    result = peps_metadata[peps_metadata["pep_number"].isin(cited_pep_numbers)]

    # PEP番号で昇順ソート
    result = result.sort_values("pep_number").reset_index(drop=True)

    return result


def generate_pep_url(pep_number: int) -> str:
    """
    PEP番号からPEPページのURLを生成する

    Args:
        pep_number: PEP番号

    Returns:
        str: PEPページのURL

    例:
        generate_pep_url(8) → "https://peps.python.org/pep-0008/"
        generate_pep_url(484) → "https://peps.python.org/pep-0484/"
    """
    from src.dash_app.utils.constants import PEP_BASE_URL

    return PEP_BASE_URL.format(pep_number=pep_number)


def clear_cache() -> None:
    """
    キャッシュをクリアする（テスト用）
    """
    global _peps_metadata_cache, _citations_cache, _metadata_cache
    _peps_metadata_cache = None
    _citations_cache = None
    _metadata_cache = None
