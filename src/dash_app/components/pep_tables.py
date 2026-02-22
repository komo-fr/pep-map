"""PEPテーブルの共通コンポーネント"""

from dash import dash_table

from src.dash_app.utils.constants import (
    STATUS_COLOR_MAP,
    STATUS_FONT_COLOR_MAP,
)
from src.dash_app.utils.data_loader import generate_pep_url


def create_pep_table(table_id: str) -> dash_table.DataTable:  # type: ignore[name-defined]
    """
    PEPテーブルを生成する

    引用関係を表示するためのDataTableコンポーネントを生成する。
    カラム構成: #, PEP, Title, Status, Created

    Args:
        table_id: テーブルのコンポーネントID

    Returns:
        dash_table.DataTable: テーブルコンポーネント
    """
    # Status列の条件付きスタイルを生成
    status_styles = generate_status_styles()

    return dash_table.DataTable(  # type: ignore[attr-defined]
        id=table_id,
        columns=[
            {"name": "#", "id": "row_num", "type": "numeric"},
            {"name": "PEP", "id": "pep", "type": "text", "presentation": "markdown"},
            {"name": "Title", "id": "title", "type": "text"},
            {"name": "Status", "id": "status", "type": "text"},
            {"name": "Created", "id": "created", "type": "text"},
        ],
        data=[],
        sort_action="native",
        sort_mode="single",
        page_action="none",
        style_table={
            "overflowX": "auto",
            "overflowY": "scroll",
            "height": "400px",
        },
        style_cell={
            "textAlign": "left",
            "padding": "4px 6px",
            "fontSize": "15px",
            "height": "auto",
            "minHeight": "18px",
        },
        style_cell_conditional=[
            {"if": {"column_id": "row_num"}, "width": "40px", "textAlign": "right"},
            {"if": {"column_id": "pep"}, "width": "80px"},
            {
                "if": {"column_id": "title"},
                "width": "300px",
                "maxWidth": "300px",
                "whiteSpace": "normal",
            },
            {"if": {"column_id": "status"}, "width": "100px", "textAlign": "center"},
            {"if": {"column_id": "created"}, "width": "100px"},
        ],
        style_data={
            "lineHeight": "1.1",
            "verticalAlign": "middle",
        },
        style_header={
            "fontWeight": "bold",
            "backgroundColor": "#f5f5f5",
        },
        style_data_conditional=[
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
        ]
        + status_styles,
    )


def generate_status_styles() -> list:
    """
    Status列の各ステータス値に対する条件付きスタイルを生成する

    STATUS_COLOR_MAPで定義された各ステータスに対して、
    背景色とフォント色を設定するスタイルルールを生成する。

    Returns:
        list: 条件付きスタイルのリスト
    """
    styles = []
    for status, bg_color in STATUS_COLOR_MAP.items():
        font_color = STATUS_FONT_COLOR_MAP.get(status, "#545454")
        styles.append(
            {
                "if": {
                    "column_id": "status",
                    "filter_query": f'{{status}} = "{status}"',
                },
                "backgroundColor": bg_color,
                "color": font_color,
            }
        )
    return styles


def convert_df_to_table_data(df) -> list[dict]:
    """
    DataFrameをDataTable用のデータ形式に変換する

    Args:
        df: PEPメタデータのDataFrame
            必須カラム: pep_number, title, status, created

    Returns:
        list[dict]: DataTable用のレコードリスト
    """
    if df.empty:
        return []

    table_data: list[dict] = []
    for _, row in df.iterrows():
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
