"""データ読み込みモジュール"""

import json
from datetime import datetime
import pickle
from typing import cast

import pandas as pd
import networkx as nx

from src.dash_app.utils.constants import (
    DATA_DIR,
    STATIC_DIR,
)


# モジュールレベルでキャッシュ（アプリ起動時に一度だけ読み込む）
_peps_metadata_cache: pd.DataFrame | None = None
_citations_cache: pd.DataFrame | None = None
_metadata_cache: dict | None = None
_python_releases_cache: pd.DataFrame | None = None
_node_metrics_cache: pd.DataFrame | None = None
_peps_with_metrics_cache: pd.DataFrame | None = None
_metrics_styles_cache: list[dict] | None = None
_citation_changes_cache: pd.DataFrame | None = None
_group_data_cache: pd.DataFrame | None = None
_group_names_cache: pd.DataFrame | None = None


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
        - pep_markdown (str): Markdownリンク形式のPEP表記
    """
    global _peps_metadata_cache

    if _peps_metadata_cache is not None:
        return _peps_metadata_cache

    file_path = DATA_DIR / "peps_metadata.csv"

    df = pd.read_csv(file_path)

    # created列を日付型に変換
    # フォーマット: "13-Jun-2000" → %d-%b-%Y
    df["created"] = pd.to_datetime(df["created"], format="%d-%b-%Y")

    # Markdownリンク列を事前計算
    df["pep_markdown"] = df["pep_number"].apply(
        lambda pep_num: f"[PEP {pep_num}]({generate_pep_url(pep_num)})"
    )

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
            - checked_at (str): データチェック日（YYYY-MM-DD HH:MM (UTC)形式）
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

    # checked_at を YYYY-MM-DD HH:MM (UTC) 形式に変換
    checked_at_str = data["checked_at"]
    checked_at_dt = datetime.fromisoformat(checked_at_str)
    data["checked_at"] = checked_at_dt.strftime("%Y-%m-%d %H:%M (UTC)")

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


def load_citation_changes() -> pd.DataFrame:
    """
    引用関係の変更履歴データを読み込む

    Returns:
        pd.DataFrame: 引用変更履歴のDataFrame

    列:
        - detected (str): 検出日（YYYY-MM-DD形式）
        - change_type (str): 変更タイプ（Added/Changed）
        - citing (int): 引用元PEP番号
        - cited (int): 引用先PEP番号
        - count_before (str): 変更前の引用回数（数値または"-"）
        - count_after (str): 変更後の引用回数（数値または"-"）
        - cited_title (str): 引用先PEPのタイトル
        - citing_title (str): 引用元PEPのタイトル
    """
    global _citation_changes_cache

    if _citation_changes_cache is not None:
        return _citation_changes_cache

    file_path = DATA_DIR / "citation_changes.csv"

    df = pd.read_csv(file_path)

    # detected_at → detected への変換処理
    # ISO形式（2026-03-07T04:33:27.412587+00:00）から日付部分のみ抽出
    # YYYY-MM-DD形式の文字列に変換
    df["detected"] = pd.to_datetime(df["detected_at"]).dt.strftime("%Y-%m-%d")
    df = df.drop(columns=["detected_at"])

    # count_before/count_after の数値を整数文字列に変換し、空値を "-" に置換
    for col in ["count_before", "count_after"]:
        df[col] = df[col].apply(lambda x: str(int(x)) if pd.notna(x) else "-")

    # peps_metadata から cited/citing に対応するタイトルを結合
    peps_metadata = load_peps_metadata()

    # cited に対応するタイトルを結合
    df = df.merge(
        peps_metadata[["pep_number", "title"]],
        left_on="cited",
        right_on="pep_number",
        how="left",
    )
    df = df.rename(columns={"title": "cited_title"})
    df = df.drop(columns=["pep_number"])

    # citing に対応するタイトルを結合
    df = df.merge(
        peps_metadata[["pep_number", "title"]],
        left_on="citing",
        right_on="pep_number",
        how="left",
    )
    df = df.rename(columns={"title": "citing_title"})
    df = df.drop(columns=["pep_number"])

    # citing と cited の Markdown リンク列を追加
    df["citing_markdown"] = df["citing"].apply(
        lambda pep_num: f"[PEP {pep_num}]({generate_pep_url(pep_num)})"
    )
    df["cited_markdown"] = df["cited"].apply(
        lambda pep_num: f"[PEP {pep_num}]({generate_pep_url(pep_num)})"
    )

    _citation_changes_cache = df
    return df


def load_node_metrics() -> pd.DataFrame:
    """
    ノードメトリクスデータを読み込む

    Returns:
        pd.DataFrame: ノードメトリクスのDataFrame

    列:
        - pep_number (int): PEP番号
        - in_degree (int): 入次数
        - out_degree (int): 出次数
        - degree (int): 次数（入次数 + 出次数）
        - pagerank (float): PageRank値
    """
    global _node_metrics_cache

    if _node_metrics_cache is not None:
        return _node_metrics_cache

    file_path = DATA_DIR / "node_metrics.csv"

    if not file_path.exists():
        # フォールバック: 空のDataFrameを返す
        return pd.DataFrame(
            columns=["pep_number", "in_degree", "out_degree", "degree", "pagerank"]
        )

    df = pd.read_csv(file_path)

    _node_metrics_cache = df
    return df


def load_peps_with_metrics() -> pd.DataFrame:
    """
    PEP基本情報とメトリクスを統合したDataFrameを返す

    Returns:
        pd.DataFrame: peps_metadata + node_metrics の統合DataFrame
    """
    global _peps_with_metrics_cache

    if _peps_with_metrics_cache is not None:
        return _peps_with_metrics_cache.copy()

    peps_df = load_peps_metadata()
    metrics_df = load_node_metrics()

    # left joinでメトリクスがないPEPも残す
    merged_df = peps_df.merge(metrics_df, on="pep_number", how="left")

    _peps_with_metrics_cache = merged_df
    return merged_df


def load_metrics_styles() -> list[dict]:
    """
    メトリクステーブルのスタイル条件を事前計算

    In-degree, Out-degree, Degree列に対してデータバースタイルを生成
    PageRank列に対してグラデーション背景を生成
    他のスタイル条件（ステータスカラー、縞模様）も含める

    Returns:
        list[dict]: style_data_conditionalに使用するスタイルのリスト
    """
    from src.dash_app.utils.table_helpers import data_bars, gradient_backgrounds
    from src.dash_app.components.pep_tables import generate_status_styles

    global _metrics_styles_cache

    if _metrics_styles_cache is not None:
        return _metrics_styles_cache

    # PEP + メトリクスデータを取得
    df = load_peps_with_metrics()

    # メトリクス列の欠損値を処理
    for col in ["in_degree", "out_degree", "degree", "pagerank"]:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    # デフォルトのスタイル条件
    base_styles = [
        {
            "if": {"row_index": "odd"},
            "backgroundColor": "#fafafa",
        },
        {
            "if": {"column_id": "pep"},
            "paddingTop": "11px",
            "paddingBottom": "0px",
            "fontSize": "14px",
            "verticalAlign": "bottom",
        },
    ] + generate_status_styles()

    # データバースタイルを生成（In-degree, Out-degree, Degree）
    data_bar_styles = []
    for column in ["in_degree", "out_degree", "degree"]:
        if column in df.columns and len(df) > 0:
            data_bar_styles.extend(data_bars(df, column))

    # PageRank列にグラデーション背景を生成
    gradient_styles = []
    if "pagerank" in df.columns and len(df) > 0:
        gradient_styles.extend(gradient_backgrounds(df, "pagerank"))

    # 全てのスタイルを結合
    all_styles = base_styles + data_bar_styles + gradient_styles

    _metrics_styles_cache = all_styles
    return all_styles


def load_group_data() -> pd.DataFrame:
    """
    グループデータを読み込む（キャッシュあり）

    Returns:
        pd.DataFrame: グループデータ

    列:
        - PEP (int): PEP番号
        - title: PEPのタイトル
        - status: PEPのステータス
        - created: PEPの作成日
        - group_id (int): グループID（最大値のグループIDは孤立ノードの集まり）
        - in-degree_group (int): グループ内入次数
        - out-degree_group (int): グループ内出次数
        - degree_group (int): グループ内次数
        - pagerank_group (float): グループ内PageRank
        - pagerank_cumsum (float): グループ内PageRankの累積和
    """
    global _group_data_cache

    if _group_data_cache is not None:
        return _group_data_cache

    group_file = DATA_DIR / "groups" / "pep_group_metrics.csv"
    if not group_file.exists():
        raise FileNotFoundError(
            f"Group data file not found: {group_file}. "
            "Run the data pipeline to generate this file."
        )
    _group_data_cache = pd.read_csv(group_file)
    return _group_data_cache


def load_group_names() -> pd.DataFrame:
    """
    グループ名データを読み込む（キャッシュあり）

    Returns:
        pd.DataFrame: グループ名データ

    列:
        - group_id (int): グループID
        - group_name (str): グループ名
        - description (str): グループの説明
    """
    global _group_names_cache

    if _group_names_cache is not None:
        return _group_names_cache

    group_names_file = DATA_DIR / "groups" / "group_names.csv"
    if not group_names_file.exists():
        # ファイルが存在しない場合は空のDataFrameを返す
        return pd.DataFrame(columns=["group_id", "group_name", "description"])

    _group_names_cache = pd.read_csv(group_names_file)
    return _group_names_cache


def get_group_name_info(group_id: int) -> dict[str, str]:
    """
    指定されたグループIDのグループ名と説明を取得する

    Args:
        group_id: グループID

    Returns:
        dict: {"group_name": str, "description": str}
              グループが見つからない場合は空文字列
    """
    df = load_group_names()
    result = df[df["group_id"] == group_id]

    if result.empty:
        return {"group_name": "", "description": ""}

    row = result.iloc[0]
    return {
        "group_name": str(row["group_name"]) if pd.notna(row["group_name"]) else "",
        "description": str(row["description"]) if pd.notna(row["description"]) else "",
    }


def get_peps_by_group(group_id: int) -> pd.DataFrame:
    """
    指定されたグループに所属するPEPを取得する

    Args:
        group_id: グループID

    Returns:
        pd.DataFrame: グループに所属するPEPのDataFrame
    """
    df = load_group_data()
    return df[df["group_id"] == group_id].copy()


def get_group_id_by_pep(pep_number: int) -> int | None:
    """
    指定されたPEP番号からグループIDを取得する

    Args:
        pep_number: PEP番号

    Returns:
        int | None: グループID。PEPが見つからない場合はNone
    """
    df = load_group_data()
    result = df[df["PEP"] == pep_number]

    if result.empty:
        return None

    return int(result.iloc[0]["group_id"])


def get_group_list() -> list[dict[str, str | int]]:
    """
    グループ一覧を取得する（ドロップダウン用）

    Returns:
        list[dict[str, str | int]]: [{"label": "All Groups", "value": "all"}, {"label": "Group 0 (58 PEPs): グループ名", "value": 0}, ...]
    """
    df = load_group_data()
    group_counts = df.groupby("group_id").size().to_dict()

    # グループ名データを取得
    group_names_df = load_group_names()
    group_names_dict = {}
    for _, row in group_names_df.iterrows():
        group_names_dict[int(row["group_id"])] = (
            str(row["group_name"]) if pd.notna(row["group_name"]) else ""
        )

    options: list[dict[str, str | int]] = [{"label": "All Groups", "value": "all"}]
    for group_id in sorted(cast(list[int], list(group_counts.keys()))):
        count = group_counts[group_id]

        label = f"Group {group_id} ({count} PEPs)"
        # グループ名を取得
        group_name = group_names_dict.get(group_id, "")
        if group_name:
            label = f"Group {group_id} ({count} PEPs): {group_name}"
        else:
            label = f"Group {group_id} ({count} PEPs)"
        options.append({"label": label, "value": group_id})

    return options


def clear_cache() -> None:
    """
    キャッシュをクリアする（テスト用）

    data_loaderのキャッシュに加えて、依存する各モジュールのキャッシュもクリアする。
    """
    global \
        _peps_metadata_cache, \
        _citations_cache, \
        _metadata_cache, \
        _python_releases_cache, \
        _node_metrics_cache, \
        _peps_with_metrics_cache, \
        _metrics_styles_cache, \
        _citation_changes_cache, \
        _group_data_cache, \
        _group_names_cache
    _peps_metadata_cache = None
    _citations_cache = None
    _metadata_cache = None
    _python_releases_cache = None
    _node_metrics_cache = None
    _peps_with_metrics_cache = None
    _metrics_styles_cache = None
    _citation_changes_cache = None
    _group_data_cache = None
    _group_names_cache = None

    # 他モジュールのキャッシュもクリア（遅延インポートで循環参照を回避）
    from src.dash_app.components import network_graph, group_network_graph

    network_graph.clear_cache()
    group_network_graph.clear_cache()


def load_subgraph(group_id: int) -> "nx.DiGraph | None":
    """
    指定されたグループIDのサブグラフを読み込む

    Args:
        group_id: グループID

    Returns:
        NetworkX DiGraph、存在しない場合はNone
    """

    subgraph_path = (
        DATA_DIR / "groups" / "subgraphs" / "graphs" / f"subgraph_{group_id}.pkl"
    )
    if not subgraph_path.exists():
        return None

    with open(subgraph_path, "rb") as f:
        return pickle.load(f)


def load_subgraph_metrics(group_id: int) -> "pd.DataFrame | None":
    """
    指定されたグループIDのメトリクスを読み込む

    Args:
        group_id: グループID

    Returns:
        DataFrame、存在しない場合はNone
    """
    metrics_path = DATA_DIR / "groups" / "pep_group_metrics.csv"
    if not metrics_path.exists():
        return None
    df = pd.read_csv(metrics_path)
    df = df[df["group_id"] == group_id]

    return df
