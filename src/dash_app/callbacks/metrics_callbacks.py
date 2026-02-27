"""PEP Metricsタブのコールバック関数"""

from dash import Input, Output

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
        ],
        Input("main-tabs", "value"),  # タブが切り替わったら更新
    )
    def update_metrics_table(active_tab: str) -> tuple[list[dict], list[dict]]:
        """
        メトリクステーブルのデータとスタイルを更新

        スタイル条件（data_bars）はアプリ起動時に事前計算しているため、
        ここではデータのみを更新する

        Args:
            active_tab: アクティブなタブのvalue

        Returns:
            tuple: (テーブルデータ, style_data_conditional)
        """
        if active_tab != "metrics":
            # Metricsタブ以外では更新しない（パフォーマンス向上）
            return [], load_metrics_styles()

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

        # 辞書のリストに変換（Markdownリンクは事前計算済み）
        table_data = []
        for _, row in df.iterrows():
            table_data.append(
                {
                    "pep": row["pep_markdown"],  # 事前計算されたMarkdownリンク
                    "pep_number": row["pep_number"],  # ソート用
                    "title": row["title"],
                    "status": row["status"],
                    "created": row["created"],
                    "in_degree": row.get("in_degree", 0),
                    "out_degree": row.get("out_degree", 0),
                    "degree": row.get("degree", 0),
                    "pagerank": row.get("pagerank", 0),
                }
            )

        # スタイル条件はアプリ起動時に事前計算したものをキャッシュから取得
        return table_data, load_metrics_styles()
