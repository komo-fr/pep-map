"""Timelineタブのコールバック関数"""

from dash import Input, Output, html

from src.dash_app.utils.data_loader import (
    generate_pep_url,
    get_cited_peps,
    get_citing_peps,
    get_pep_by_number,
)


def register_timeline_callbacks(app):
    """
    Timelineタブのコールバックを登録する

    Args:
        app: Dashアプリケーションインスタンス
    """

    @app.callback(
        Output("pep-info-display", "children"),
        Output("pep-error-message", "children"),
        Input("pep-input", "value"),
    )
    def update_pep_info(pep_number):
        """
        PEP番号入力に連動してPEP情報を更新する

        Args:
            pep_number: 入力されたPEP番号（int または None）

        Returns:
            tuple: (PEP情報表示コンテンツ, エラーメッセージ)
        """
        # 入力が空/Noneの場合: 初期説明文を表示
        if pep_number is None:
            return _create_initial_info_message(), ""

        # PEPの存在確認
        pep_data = get_pep_by_number(pep_number)

        # 存在しない場合: エラーメッセージを表示
        if pep_data is None:
            error_message = f"Not Found: PEP {pep_number}"
            return _create_initial_info_message(), error_message

        # 存在する場合: PEP情報を表示
        return _create_pep_info_display(pep_data), ""

    # === テーブル更新コールバック（新規追加） ===
    @app.callback(
        Output("citing-peps-table", "data"),
        Output("cited-peps-table", "data"),
        Input("pep-input", "value"),
    )
    def update_tables(pep_number):
        """
        PEP番号入力に連動してテーブルデータを更新する

        Args:
            pep_number: 入力されたPEP番号（int または None）

        Returns:
            tuple: (citing_tableのデータ, cited_tableのデータ)
        """
        # 入力が空/Noneまたは存在しないPEPの場合: 空のテーブル
        if pep_number is None:
            return [], []

        pep_data = get_pep_by_number(pep_number)
        if pep_data is None:
            return [], []

        # このPEPを引用しているPEPを取得
        citing_peps_df = get_citing_peps(pep_number)
        citing_table_data = _convert_df_to_table_data(citing_peps_df)

        # このPEPに引用されているPEPを取得
        cited_peps_df = get_cited_peps(pep_number)
        cited_table_data = _convert_df_to_table_data(cited_peps_df)

        return citing_table_data, cited_table_data


def _convert_df_to_table_data(df) -> list[dict]:
    """
    DataFrameをDataTable用のデータ形式に変換する

    Args:
        df: PEPメタデータのDataFrame

    Returns:
        list[dict]: DataTable用のレコードリスト
    """
    if df.empty:
        return []

    table_data: list[dict] = []
    for idx, row in df.iterrows():
        pep_number = row["pep_number"]
        pep_url = generate_pep_url(pep_number)

        # 日付をフォーマット（YYYY-MM-DD）
        created_str = row["created"].strftime("%Y-%m-%d")

        table_data.append(
            {
                "row_num": len(table_data) + 1,  # 通し番号（1から開始）
                "pep": f"[PEP {pep_number}]({pep_url})",  # Markdownリンク
                "pep_number": pep_number,  # ソート用（非表示）
                "title": row["title"],
                "status": row["status"],
                "created": created_str,
            }
        )

    return table_data


def _create_initial_info_message() -> html.Div:
    """
    初期状態のPEP情報表示（説明文）を生成する

    Returns:
        html.Div: 初期説明文のコンポーネント
    """
    return html.Div(
        [
            html.P(
                "Let's enter the PEP number in the left text box.",
                style={"marginBottom": "8px"},
            ),
            html.P("Then you can see the following information."),
            html.Ul(
                [
                    html.Li("Which PEPs do link that PEP?"),
                    html.Li("Which PEPs are linked from that PEP?"),
                ]
            ),
        ],
        style={
            "color": "#666",
        },
    )


def _create_pep_info_display(pep_data) -> html.Div:
    """
    PEP情報表示コンポーネントを生成する

    Args:
        pep_data: PEPのメタデータ（pd.Series）

    Returns:
        html.Div: PEP情報のコンポーネント
    """
    pep_number = pep_data["pep_number"]
    title = pep_data["title"]
    status = pep_data["status"]
    pep_type = pep_data["type"]
    created = pep_data["created"]

    # 日付をフォーマット（YYYY-MM-DD）
    created_str = created.strftime("%Y-%m-%d")

    # PEPページへのURL
    pep_url = generate_pep_url(pep_number)

    return html.Div(
        [
            # 1行目: Created と Type
            html.P(
                f"Created: {created_str}  Type: {pep_type}",
                style={
                    "marginBottom": "4px",
                    "color": "#666",
                    "fontSize": "14px",
                },
            ),
            # 2行目: PEP番号（リンク付き）
            html.H3(
                html.A(
                    f"PEP {pep_number}",
                    href=pep_url,
                    target="_blank",
                    style={
                        "color": "#0066cc",
                        "textDecoration": "none",
                    },
                ),
                style={
                    "marginBottom": "4px",
                    "marginTop": "0",
                },
            ),
            # 3行目: タイトル（Statusを括弧内に表示）
            html.P(
                f"{title} ({status})",
                style={
                    "marginBottom": "0",
                    "fontSize": "16px",
                },
            ),
        ]
    )
