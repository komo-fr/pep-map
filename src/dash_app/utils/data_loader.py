"""データ読み込みモジュール"""

import json
from datetime import datetime

import pandas as pd

from src.dash_app.utils.constants import (
    DATA_DIR,
    STATIC_DIR,
)


# モジュールレベルでキャッシュ（アプリ起動時に一度だけ読み込む）
_peps_metadata_cache: pd.DataFrame | None = None
_citations_cache: pd.DataFrame | None = None
_metadata_cache: dict | None = None
_python_releases_cache: pd.DataFrame | None = None


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
            - fetched_at (str): データ取得日（YYYY-MM-DD HH:MM (UTC)形式）
            - source_url (str): データ取得元URL
    """
    global _metadata_cache

    if _metadata_cache is not None:
        return _metadata_cache

    file_path = DATA_DIR / "metadata.json"

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    # fetched_at を YYYY-MM-DD HH:MM (UTC) 形式に変換
    # 元のフォーマット: "2026-02-14T15:25:50.027772+00:00"
    fetched_at_str = data["fetched_at"]
    fetched_at_dt = datetime.fromisoformat(fetched_at_str)
    data["fetched_at"] = fetched_at_dt.strftime("%Y-%m-%d %H:%M (UTC)")

    _metadata_cache = data
    return data


def get_fetched_year() -> int:
    """
    データ取得日の年を取得する

    Returns:
        int: データ取得日の年（例: 2026）
    """
    metadata = load_metadata()
    # fetched_at は "YYYY-MM-DD HH:MM (UTC)" 形式なので、最初の4文字を取得
    fetched_at_str = metadata["fetched_at"]
    return int(fetched_at_str[:4])


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

    # 作成日で昇順ソート
    result = result.sort_values("created").reset_index(drop=True)

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

    # 作成日で昇順ソート
    result = result.sort_values("created").reset_index(drop=True)

    return result


def load_python_releases() -> pd.DataFrame:
    """
    Pythonリリース日データを読み込む

    Returns:
        pd.DataFrame: Pythonリリース日のDataFrame

    列:
        - version (str): Pythonバージョン（例: "2.0", "3.10"）
        - release_date (datetime): リリース日
        - major_version (int): メジャーバージョン（2 or 3）
    """
    global _python_releases_cache

    if _python_releases_cache is not None:
        return _python_releases_cache

    file_path = STATIC_DIR / "python_release_dates.csv"

    df = pd.read_csv(file_path, dtype={"version": str})

    # release_date列を日付型に変換
    # フォーマット: "2000/10/16" → %Y/%m/%d
    df["release_date"] = pd.to_datetime(df["release_date"], format="%Y/%m/%d")

    # メジャーバージョンを抽出（versionの最初の文字）
    df["major_version"] = df["version"].str.split(".").str[0].astype(int)

    _python_releases_cache = df
    return df


def get_python_releases_by_major_version(major_version: int) -> pd.DataFrame:
    """
    指定したメジャーバージョンのPythonリリース日を取得する

    Args:
        major_version: メジャーバージョン（2 or 3）

    Returns:
        pd.DataFrame: 指定メジャーバージョンのリリース日データ
    """
    df = load_python_releases()
    return df[df["major_version"] == major_version].copy()


def get_python_releases_for_store() -> dict:
    """
    dcc.Store用のPythonリリース日データを取得する

    Returns:
        dict: クライアントサイドコールバック用のデータ構造
            {
                "python2": [
                    {"version": "2.0", "release_date": "2000-10-16"},
                    ...
                ],
                "python3": [
                    {"version": "3.0", "release_date": "2008-12-03"},
                    ...
                ]
            }
    """
    result: dict[str, list[dict[str, str]]] = {"python2": [], "python3": []}

    for major_version in [2, 3]:
        releases = get_python_releases_by_major_version(major_version)
        key = f"python{major_version}"

        for _, row in releases.iterrows():
            result[key].append(
                {
                    "version": row["version"],
                    "release_date": row["release_date"].strftime("%Y-%m-%d"),
                }
            )

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
    global \
        _peps_metadata_cache, \
        _citations_cache, \
        _metadata_cache, \
        _python_releases_cache
    _peps_metadata_cache = None
    _citations_cache = None
    _metadata_cache = None
    _python_releases_cache = None
