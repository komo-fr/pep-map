"""PEP Metricsタブのコールバック関数"""

import re

from dash import Input, Output, State, no_update

from src.dash_app.utils.data_loader import load_peps_with_metrics


def register_metrics_callbacks(app):
    """
    Metricsタブのコールバックを登録

    Args:
        app: Dashアプリケーションインスタンス
    """

    @app.callback(
        Output("metrics-table", "rowData"),
        [
            Input("main-tabs", "value"),
            Input("metrics-search-input", "value"),
        ],
    )
    def update_metrics_table(
        active_tab: str,
        search_query: str,
    ) -> list[dict]:
        """
        メトリクステーブルのデータを更新

        ソート・ページングはAG Gridのクライアントサイドで処理するため、
        ここでは検索フィルタリングのみ行い、全データを返す。

        Args:
            active_tab: アクティブなタブのvalue
            search_query: タイトル検索用の文字列（スペース区切りでAND検索）

        Returns:
            list[dict]: テーブルのrowData
        """
        if active_tab != "metrics":
            # Metricsタブ以外では更新しない（パフォーマンス向上）
            return []

        # PEP基本情報 + メトリクスを取得
        df = load_peps_with_metrics()

        # メトリクス列の欠損値を処理（メトリクスがないPEPは0埋め）
        for col in ["in_degree", "out_degree", "degree", "pagerank"]:
            if col in df.columns:
                df[col] = df[col].fillna(0)

        # PageRankを小数点4桁に丸める
        if "pagerank" in df.columns:
            df["pagerank"] = df["pagerank"].round(4)

        # 検索フィルタリング処理
        if search_query and search_query.strip():
            # 半角スペースと全角スペースで分割してAND検索
            keywords = re.split(r"[ 　]+", search_query.strip())
            # 各キーワードでフィルタリング（すべてのキーワードを含む行のみ残す）
            keywords = [kw for kw in keywords if kw]
            if keywords:
                # すべてのキーワードがTitle列に含まれる行のみを残す（AND検索）
                for keyword in keywords:
                    # 各キーワードをエスケープして検索（大文字小文字を区別しない）
                    escaped_keyword = re.escape(keyword)
                    mask = df["title"].str.contains(
                        escaped_keyword, case=False, na=False, regex=True
                    )
                    df = df[mask]

        # created列を文字列に変換（YYYY-MM-DD形式）
        if "created" in df.columns:
            df["created"] = df["created"].dt.strftime("%Y-%m-%d")

        # 辞書のリストに変換（Markdownリンクは事前計算済み）
        table_data = (
            df[
                [
                    "pep_markdown",
                    "pep_number",
                    "title",
                    "status",
                    "created",
                    "in_degree",
                    "out_degree",
                    "degree",
                    "pagerank",
                ]
            ]
            .fillna(0)
            .rename(columns={"pep_markdown": "pep"})
            .to_dict("records")
        )

        return table_data

    @app.callback(
        Output("metrics-table", "dashGridOptions"),
        Input("metrics-page-size-select", "value"),
        State("metrics-table", "dashGridOptions"),
    )
    def update_page_size(selected_page_size, grid_options: dict) -> dict:
        """
        ドロップダウンで選択されたページサイズをAG Gridに反映

        Args:
            selected_page_size: ドロップダウンで選択されたページサイズ（-1は全データ）
            grid_options: 現在のdashGridOptions

        Returns:
            dict: 更新されたdashGridOptions
        """
        # 文字列から整数に変換
        page_size = int(selected_page_size)
        if page_size == -1:
            grid_options["pagination"] = False
        else:
            grid_options["pagination"] = True
            grid_options["paginationPageSize"] = page_size
        return grid_options

    @app.callback(
        [
            Output("metrics-pagination-top", "max_value"),
            Output("metrics-pagination-top", "active_page"),
        ],
        Input("metrics-table", "paginationInfo"),
    )
    def sync_top_pagination(pagination_info):
        """AG Gridのページ情報から上部ページネーションを同期"""
        if pagination_info is None:
            return no_update, no_update
        return pagination_info["totalPages"], pagination_info["currentPage"] + 1

    @app.callback(
        Output("metrics-table", "paginationGoTo"),
        Input("metrics-pagination-top", "active_page"),
        prevent_initial_call=True,
    )
    def goto_page_from_top_pagination(active_page):
        """上部ページネーションのクリックでAG Gridのページを移動"""
        if active_page is None or active_page == 1:
            return "first"
        return active_page - 1
