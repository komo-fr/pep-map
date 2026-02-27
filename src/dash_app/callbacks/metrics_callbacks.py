"""PEP Metricsタブのコールバック関数"""

import pandas as pd
from dash import Input, Output

from src.dash_app.utils.data_loader import load_peps_with_metrics, generate_pep_url


def data_bars(df: pd.DataFrame, column: str) -> list[dict]:
    """
    DataTableの列に数値に応じたデータバー（棒グラフ）スタイルを生成

    Args:
        df: データフレーム
        column: データバーを適用する列名

    Returns:
        list[dict]: style_data_conditionalに追加するスタイルのリスト
    """
    n_bins = 100
    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    ranges = [
        ((df[column].max() - df[column].min()) * i) + df[column].min() for i in bounds
    ]
    styles = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]
        max_bound_percentage = bounds[i] * 100
        styles.append(
            {
                "if": {
                    "filter_query": (
                        "{{{column}}} >= {min_bound}"
                        + (
                            " && {{{column}}} < {max_bound}"
                            if (i < len(bounds) - 1)
                            else ""
                        )
                    ).format(column=column, min_bound=min_bound, max_bound=max_bound),
                    "column_id": column,
                },
                "background": (
                    """
                    linear-gradient(90deg,
                    rgba(25, 118, 210, 0.35) 0%,
                    rgba(25, 118, 210, 0.35) {max_bound_percentage}%,
                    white {max_bound_percentage}%,
                    white 100%)
                """.format(max_bound_percentage=max_bound_percentage)
                ),
                "paddingBottom": 2,
                "paddingTop": 2,
            }
        )

    return styles


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
        ],
        Input("main-tabs", "value"),  # タブが切り替わったら更新
    )
    def update_metrics_table(active_tab: str) -> tuple[list[dict], list[dict]]:
        """
        メトリクステーブルのデータとスタイルを更新

        Args:
            active_tab: アクティブなタブのvalue

        Returns:
            tuple: (テーブルデータ, style_data_conditional)
        """
        from src.dash_app.components.pep_tables import generate_status_styles

        # デフォルトのstyle_data_conditional（ステータスカラーと縞模様）
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

        if active_tab != "metrics":
            # Metricsタブ以外では更新しない（パフォーマンス向上）
            return [], base_styles

        # PEP基本情報 + メトリクスを取得
        df = load_peps_with_metrics()

        # メトリクス列の欠損値を処理（メトリクスがないPEPは0埋め）
        for col in ["in_degree", "out_degree", "degree", "pagerank"]:
            if col in df.columns:
                df[col] = df[col].fillna(0)

        # PageRankを小数点4桁に丸める
        if "pagerank" in df.columns:
            df["pagerank"] = df["pagerank"].round(4)

        # created列を文字列に変換（YYYY-MM-DD形式）
        if "created" in df.columns:
            df["created"] = df["created"].dt.strftime("%Y-%m-%d")

        # 辞書のリストに変換（PEP番号をMarkdownリンクに）
        table_data = []
        for _, row in df.iterrows():
            pep_number = row["pep_number"]
            pep_url = generate_pep_url(pep_number)

            table_data.append(
                {
                    "pep": f"[PEP {pep_number}]({pep_url})",  # Markdownリンク
                    "pep_number": pep_number,  # ソート用
                    "title": row["title"],
                    "status": row["status"],
                    "created": row["created"],
                    "in_degree": row.get("in_degree", 0),
                    "out_degree": row.get("out_degree", 0),
                    "degree": row.get("degree", 0),
                    "pagerank": row.get("pagerank", 0),
                }
            )

        # データバースタイルを生成（In-degree, Out-degree, Degree列に適用）
        data_bar_styles = []
        for column in ["in_degree", "out_degree", "degree"]:
            if column in df.columns and len(df) > 0:
                data_bar_styles.extend(data_bars(df, column))

        # 全てのスタイルを結合
        all_styles = base_styles + data_bar_styles

        return table_data, all_styles
