"""PEP Metricsタブのコールバック関数"""

import re
from dash import Input, Output, callback_context

from src.dash_app.utils.data_loader import (
    load_peps_with_metrics,
    load_metrics_styles,
)


def register_metrics_callbacks(app):
    """
    Metricsタブのコールバックを登録

    Args:
        app: Dashアプリケーションインスタンス
    """

    @app.callback(
        [
            Output("metrics-table", "data"),
            Output("metrics-table", "style_data_conditional"),
            Output("metrics-table", "page_count"),
        ],
        [
            Input("main-tabs", "value"),  # タブが切り替わったら更新
            Input("metrics-table", "page_current"),  # ページ切り替え
            Input("metrics-table", "sort_by"),  # ソート変更
            Input("metrics-page-size-select", "value"),  # ページサイズ変更
            Input("metrics-search-input", "value"),  # 検索文字列
        ],
    )
    def update_metrics_table(
        active_tab: str,
        page_current: int,
        sort_by: list,
        page_size: int,
        search_query: str,
    ) -> tuple[list[dict], list[dict], int]:
        """
        メトリクステーブルのデータとスタイルを更新（サーバサイドページング）

        スタイル条件（data_bars）はアプリ起動時に事前計算しているため、
        ここではデータのみを更新する。

        Args:
            active_tab: アクティブなタブのvalue
            page_current: 現在のページ番号（0-indexed）
            sort_by: ソート設定のリスト
            page_size: 1ページあたりの行数（-1の場合は全データ）
            search_query: タイトル検索用の文字列（スペース区切りでAND検索）

        Returns:
            tuple: (テーブルデータ, style_data_conditional, 全ページ数)
        """
        if active_tab != "metrics":
            # Metricsタブ以外では更新しない（パフォーマンス向上）
            return [], [], 0

        # page_sizeを整数に変換（dbc.Selectから文字列で受け取るため）
        page_size = int(page_size)

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

        # ソート処理（全データに対して実行）
        if sort_by:
            sort_col = sort_by[0]["column_id"]
            sort_direction = sort_by[0]["direction"]
            is_ascending = sort_direction == "asc"

            # "pep"列でソートする場合は、pep_number列を使用
            if sort_col == "pep":
                df = df.sort_values("pep_number", ascending=is_ascending)
            else:
                df = df.sort_values(sort_col, ascending=is_ascending)

        # created列を文字列に変換（YYYY-MM-DD形式）
        if "created" in df.columns:
            df["created"] = df["created"].dt.strftime("%Y-%m-%d")

        # ページサイズが-1（全データ）の場合の処理
        if page_size == -1:
            # 全データを表示（ページングなし）
            paged_df = df
            total_pages = 1
        else:
            # ページング処理（指定されたページのデータのみを抽出）
            offset = (page_current or 0) * page_size
            paged_df = df.iloc[offset : offset + page_size]

            # 全ページ数を計算
            total_rows = len(df)
            total_pages = (total_rows + page_size - 1) // page_size  # 切り上げ

        # 辞書のリストに変換（Markdownリンクは事前計算済み）
        table_data = (
            paged_df[
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

        # スタイル条件はアプリ起動時に事前計算したものをキャッシュから取得
        return table_data, load_metrics_styles(), total_pages

    @app.callback(
        [
            Output("metrics-table", "page_current"),
            Output("metrics-pagination", "active_page"),
            Output("metrics-pagination-bottom", "active_page"),
        ],
        [
            Input("metrics-pagination", "active_page"),
            Input("metrics-pagination-bottom", "active_page"),
            Input("metrics-page-size-select", "value"),
            Input("metrics-search-input", "value"),
        ],
    )
    def sync_pagination_and_table(
        top_active_page: int, bottom_active_page: int, page_size: int, search_query: str
    ) -> tuple[int, int, int]:
        """
        上下のページネーションボタンとDataTableを同期、ページサイズ変更対応

        ページネーションボタンがクリックされたら：
        1. DataTableのページを更新
        2. もう一方のページネーションボタンも同期

        ページサイズが変更されたら、ページを1ページ目にリセット

        Args:
            top_active_page: 上のページネーションボタンのページ番号（1-indexed）
            bottom_active_page: 下のページネーションボタンのページ番号（1-indexed）
            page_size: 選択されたページサイズ

        Returns:
            tuple: (DataTableのpage_current, 上のページネーション, 下のページネーション)
        """
        ctx = callback_context

        # どのコンポーネントがトリガーされたかを確認
        if not ctx.triggered:
            return 0, 1, 1

        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # ページサイズまたは検索文字列が変更された場合は、ページをリセット
        if triggered_id in ["metrics-page-size-select", "metrics-search-input"]:
            return 0, 1, 1

        # トリガーされたコンポーネントから値を取得
        if triggered_id == "metrics-pagination":
            active_page = top_active_page
        elif triggered_id == "metrics-pagination-bottom":
            active_page = bottom_active_page
        else:
            return 0, 1, 1

        if active_page is None:
            return 0, 1, 1

        # dbc.Paginationは1-indexed、DataTableは0-indexedなので変換
        page_current = active_page - 1

        # DataTableとページネーションボタンを同期（両方同じページを表示）
        return page_current, active_page, active_page

    @app.callback(
        Output("metrics-table", "page_size"),
        Input("metrics-page-size-select", "value"),
    )
    def update_table_page_size(selected_page_size) -> int:
        """
        ドロップダウンで選択されたページサイズをテーブルに反映

        Args:
            selected_page_size: ドロップダウンで選択されたページサイズ（-1は全データ）

        Returns:
            int: テーブルに設定するページサイズ
        """
        # 文字列から整数に変換
        page_size = int(selected_page_size)

        # -1（全データ）の場合は、十分に大きな数を返す（ページングが無効化される）
        if page_size == -1:
            return 10000
        return page_size

    @app.callback(
        [
            Output("metrics-pagination", "max_value"),
            Output("metrics-pagination-bottom", "max_value"),
        ],
        Input("metrics-table", "page_count"),
    )
    def update_pagination_max_values(page_count: int) -> tuple[int, int]:
        """
        DataTableのページ数から、上下のページネーションボタンの最大値を更新する

        Args:
            page_count: DataTableの全ページ数

        Returns:
            tuple: (上のページネーション、下のページネーション)の最大値
        """
        max_value = page_count or 1
        return max_value, max_value
