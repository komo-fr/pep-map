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
_full_network_positions_cache: dict[int, tuple[float, float]] | None = None
_subgraph_positions_cache: dict[int, dict[int, tuple[float, float]]] = {}
_subgraph_cache: dict[int, "nx.DiGraph"] = {}
_subgraph_metrics_cache: pd.DataFrame | None = None
_group_to_group_network_cache: "nx.DiGraph | None" = None
_group_to_group_positions_cache: dict[int, tuple[float, float]] | None = None
_group_tooltip_info_cache: dict[int, dict] | None = None


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
    df = pd.read_csv(group_file)

    # created列を日付型に変換
    # フォーマット: "09-Jul-2010" → %d-%b-%Y
    df["created"] = pd.to_datetime(df["created"], format="%d-%b-%Y")

    _group_data_cache = df
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

    group_names_file = DATA_DIR / "groups" / "group_profiles.csv"
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
    group_names_dict = {
        int(gid): str(name) if pd.notna(name) else ""
        for gid, name in zip(group_names_df["group_id"], group_names_df["group_name"])
    }

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
        _group_names_cache, \
        _full_network_positions_cache, \
        _subgraph_positions_cache, \
        _subgraph_cache, \
        _subgraph_metrics_cache, \
        _group_to_group_network_cache, \
        _group_to_group_positions_cache, \
        _group_tooltip_info_cache
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
    _full_network_positions_cache = None
    _subgraph_positions_cache = {}
    _subgraph_cache = {}
    _subgraph_metrics_cache = None
    _group_to_group_network_cache = None
    _group_to_group_positions_cache = None
    _group_tooltip_info_cache = None

    # 他モジュールのキャッシュもクリア（遅延インポートで循環参照を回避）
    from src.dash_app.components import (
        network_graph,
        group_network_graph,
        subgraph_network_graph,
    )
    from src.dash_app.callbacks import group_callbacks

    network_graph.clear_cache()
    group_network_graph.clear_cache()
    subgraph_network_graph.clear_cache()
    group_callbacks.clear_cache()


def load_subgraph(group_id: int) -> "nx.DiGraph | None":
    """
    指定されたグループIDのサブグラフを読み込む

    Args:
        group_id: グループID

    Returns:
        NetworkX DiGraph、存在しない場合はNone
    """
    global _subgraph_cache

    if group_id in _subgraph_cache:
        return _subgraph_cache[group_id]

    subgraph_path = (
        DATA_DIR / "groups" / "subgraphs" / "graphs" / f"subgraph_{group_id}.pkl"
    )
    if not subgraph_path.exists():
        return None

    with open(subgraph_path, "rb") as f:
        subgraph = pickle.load(f)

    _subgraph_cache[group_id] = subgraph
    return subgraph


def _load_all_subgraph_metrics() -> pd.DataFrame | None:
    """
    全グループのメトリクスを読み込む（内部用）

    Returns:
        DataFrame、存在しない場合はNone
    """
    global _subgraph_metrics_cache

    if _subgraph_metrics_cache is not None:
        return _subgraph_metrics_cache

    metrics_path = DATA_DIR / "groups" / "pep_group_metrics.csv"
    if not metrics_path.exists():
        return None

    _subgraph_metrics_cache = pd.read_csv(metrics_path)
    return _subgraph_metrics_cache


def load_subgraph_metrics(group_id: int) -> "pd.DataFrame | None":
    """
    指定されたグループIDのメトリクスを読み込む

    Args:
        group_id: グループID

    Returns:
        DataFrame、存在しない場合はNone
    """
    all_metrics = _load_all_subgraph_metrics()
    if all_metrics is None:
        return None

    return all_metrics[all_metrics["group_id"] == group_id]


def load_full_network_positions() -> dict[int, tuple[float, float]]:
    """
    全体ネットワークのノード座標を読み込む

    Returns:
        dict[int, tuple[float, float]]: PEP番号をキー、(x, y)座標を値とする辞書
    """
    global _full_network_positions_cache

    if _full_network_positions_cache is not None:
        return _full_network_positions_cache

    positions_path = DATA_DIR / "node_positions.json"
    if not positions_path.exists():
        raise FileNotFoundError(
            f"Node positions file not found: {positions_path}. "
            "Run the data pipeline to generate this file."
        )

    with open(positions_path, encoding="utf-8") as f:
        positions_json = json.load(f)

    # キーを整数に変換
    positions = {int(node): tuple(pos) for node, pos in positions_json.items()}

    _full_network_positions_cache = positions
    return positions


def load_subgraph_positions(group_id: int) -> dict[int, tuple[float, float]] | None:
    """
    指定されたグループIDのサブグラフ座標を読み込む

    Args:
        group_id: グループID

    Returns:
        dict[int, tuple[float, float]]: PEP番号をキー、(x, y)座標を値とする辞書
        存在しない場合はNone
    """
    global _subgraph_positions_cache

    if group_id in _subgraph_positions_cache:
        return _subgraph_positions_cache[group_id]

    positions_path = (
        DATA_DIR / "groups" / "subgraphs" / "positions" / f"group_{group_id}.json"
    )
    if not positions_path.exists():
        return None

    with open(positions_path, encoding="utf-8") as f:
        positions_json = json.load(f)

    # キーを整数に変換
    positions = {int(node): tuple(pos) for node, pos in positions_json.items()}

    _subgraph_positions_cache[group_id] = positions
    return positions


def load_group_to_group_positions() -> dict[int, tuple[float, float]]:
    """
    グループ間ネットワークのノード座標を読み込む

    Returns:
        dict[int, tuple[float, float]]: グループIDをキー、(x, y)座標を値とする辞書
    """
    global _group_to_group_positions_cache

    if _group_to_group_positions_cache is not None:
        return _group_to_group_positions_cache

    positions_path = (
        DATA_DIR / "groups" / "group_to_group" / "group_to_group_positions.json"
    )
    if not positions_path.exists():
        raise FileNotFoundError(
            f"Group-to-group positions file not found: {positions_path}. "
            "Run detect_communities.py to generate this file."
        )

    with open(positions_path, encoding="utf-8") as f:
        positions_json = json.load(f)

    # キーを整数に変換
    positions = {int(node): tuple(pos) for node, pos in positions_json.items()}

    _group_to_group_positions_cache = positions
    return positions


def load_group_to_group_network() -> "nx.DiGraph":
    """
    グループ間ネットワークを読み込む（キャッシュあり）

    Returns:
        nx.DiGraph: グループ間ネットワークグラフ
            ノード属性:
                - pep_count (int): グループに含まれるPEP数
            エッジ属性:
                - weight (int): グループ間の引用数

    Note:
        group_nameはgroup_profiles.csvで別途管理されているため、
        get_group_name_info()で取得すること
    """
    global _group_to_group_network_cache

    if _group_to_group_network_cache is not None:
        return _group_to_group_network_cache

    network_path = DATA_DIR / "groups" / "group_to_group" / "group_to_group_network.pkl"
    if not network_path.exists():
        raise FileNotFoundError(
            f"Group-to-group network file not found: {network_path}. "
            "Run the data pipeline to generate this file."
        )

    with open(network_path, "rb") as f:
        _group_to_group_network_cache = pickle.load(f)

    return _group_to_group_network_cache


def get_group_boundary_data(group_id: int) -> dict[int, dict]:
    """
    指定されたグループの全PEPについて境界グループ情報を一括取得する

    Args:
        group_id: グループID

    Returns:
        dict[int, dict]: PEP番号をキーとした境界グループ情報の辞書
            {
                pep_number: {
                    "cited_by_groups": [group_id, ...],  # グループIDリスト（表示用）
                    "cited_by_groups_detail": {group_id: [pep, ...], ...},  # グループごとのPEP（ツールチップ用）
                    "cites_groups": [group_id, ...],
                    "cites_groups_detail": {group_id: [pep, ...], ...},
                },
                ...
            }
    """
    citations = load_citations()
    group_data = load_group_data()

    # PEP→グループIDのマッピングを作成
    pep_to_group = dict(zip(group_data["PEP"], group_data["group_id"]))

    # 指定グループのPEP一覧を取得
    group_peps = set(group_data[group_data["group_id"] == group_id]["PEP"].tolist())

    # グループ全体を一括フィルタリング（全citationsを毎ループスキャンしないよう最適化）
    group_pep_list = list(group_peps)
    cited_by_df = citations[citations["cited"].isin(group_pep_list)]
    cites_out_df = citations[citations["citing"].isin(group_pep_list)]

    result = {}
    for pep_number in group_peps:
        # このPEPを引用しているPEP（グループごとに分類）
        citing_peps = cited_by_df[cited_by_df["cited"] == pep_number]["citing"].tolist()
        cited_by_groups_detail: dict[int, list[int]] = {}
        for citing_pep in citing_peps:
            grp = pep_to_group.get(citing_pep)
            if grp is not None and grp != group_id:
                if grp not in cited_by_groups_detail:
                    cited_by_groups_detail[grp] = []
                cited_by_groups_detail[grp].append(citing_pep)

        # 各グループ内のPEPをソート
        for grp in cited_by_groups_detail:
            cited_by_groups_detail[grp].sort()

        # このPEPが引用しているPEP（グループごとに分類）
        cited_peps = cites_out_df[cites_out_df["citing"] == pep_number][
            "cited"
        ].tolist()
        cites_groups_detail: dict[int, list[int]] = {}
        for cited_pep in cited_peps:
            grp = pep_to_group.get(cited_pep)
            if grp is not None and grp != group_id:
                if grp not in cites_groups_detail:
                    cites_groups_detail[grp] = []
                cites_groups_detail[grp].append(cited_pep)

        # 各グループ内のPEPをソート
        for grp in cites_groups_detail:
            cites_groups_detail[grp].sort()

        result[pep_number] = {
            "cited_by_groups": sorted(cited_by_groups_detail.keys()),
            "cited_by_groups_detail": cited_by_groups_detail,
            "cites_groups": sorted(cites_groups_detail.keys()),
            "cites_groups_detail": cites_groups_detail,
        }

    return result


def get_adjacent_groups(group_id: int) -> dict:
    """
    指定されたグループの隣接グループ情報を取得する

    Args:
        group_id: グループID

    Returns:
        dict: 隣接グループ情報
            - citing_groups: 選択中のグループを引用しているグループのリスト
                             [(group_id, weight), ...] 引用数(weight)の降順
            - cited_groups: 選択中のグループが引用しているグループのリスト
                            [(group_id, weight), ...] 引用数(weight)の降順
    """
    G = load_group_to_group_network()

    # 選択中のグループを引用しているグループ（in_edges）
    # edge: (source, target, data) で target が group_id
    citing_groups = []
    for source, _, data in G.in_edges(group_id, data=True):
        if source != group_id:  # 自己ループを除外
            citing_groups.append((source, data.get("weight", 1)))
    # 引用数の降順でソート
    citing_groups.sort(key=lambda x: x[1], reverse=True)

    # 選択中のグループが引用しているグループ（out_edges）
    # edge: (source, target, data) で source が group_id
    cited_groups = []
    for _, target, data in G.out_edges(group_id, data=True):
        if target != group_id:  # 自己ループを除外
            cited_groups.append((target, data.get("weight", 1)))
    # 引用数の降順でソート
    cited_groups.sort(key=lambda x: x[1], reverse=True)

    return {
        "citing_groups": citing_groups,
        "cited_groups": cited_groups,
    }


def get_top_peps_by_group(group_id: int, top_n: int = 5) -> list[int]:
    """
    指定されたグループのPageRank上位のPEP番号を取得する

    Args:
        group_id: グループID
        top_n: 取得するPEP数（デフォルト: 5）

    Returns:
        list[int]: PageRank上位のPEP番号リスト
    """
    df = get_peps_by_group(group_id)
    if df.empty:
        return []

    # PageRank降順でソート
    df_sorted = df.sort_values(by="pagerank_group", ascending=False)

    # 上位N件のPEP番号を取得
    return df_sorted["PEP"].head(top_n).tolist()


def get_all_group_tooltip_info() -> dict[int, dict]:
    """
    全グループのツールチップ表示用情報を取得する

    Returns:
        dict[int, dict]: グループIDをキーとした情報の辞書
            {group_id: {"name": str, "topPeps": list[int]}, ...}
    """
    global _group_tooltip_info_cache

    if _group_tooltip_info_cache is not None:
        return _group_tooltip_info_cache

    group_data = load_group_data()
    group_names_df = load_group_names()

    # グループ名のマッピング
    group_names_dict = {
        int(gid): str(name) if pd.notna(name) else ""
        for gid, name in zip(group_names_df["group_id"], group_names_df["group_name"])
    }

    # 全グループIDを取得
    all_group_ids = group_data["group_id"].unique().tolist()

    result = {}
    for group_id in all_group_ids:
        top_peps = get_top_peps_by_group(group_id, top_n=5)
        group_name = group_names_dict.get(group_id, "")
        result[group_id] = {
            "name": group_name,
            "topPeps": top_peps,
        }

    _group_tooltip_info_cache = result
    return result
