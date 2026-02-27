"""PEP Metricsタブのコールバック関数"""

from dash import Input, Output

from src.dash_app.utils.data_loader import load_peps_with_metrics, generate_pep_url


def register_metrics_callbacks(app):
    """
    Metricsタブのコールバックを登録

    Args:
        app: Dashアプリケーションインスタンス
    """

    @app.callback(
        Output("metrics-table", "data"),
        Input("main-tabs", "value"),  # タブが切り替わったら更新
    )
    def update_metrics_table(active_tab: str) -> list[dict]:
        """
        メトリクステーブルのデータを更新

        Args:
            active_tab: アクティブなタブのvalue

        Returns:
            list[dict]: テーブルデータ（辞書のリスト）
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

        return table_data
