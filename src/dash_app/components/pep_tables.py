"""PEPテーブルの共通コンポーネント"""

import dash_ag_grid as dag
from dash import html

from src.dash_app.utils.constants import (
    STATUS_COLOR_MAP,
    STATUS_FONT_COLOR_MAP,
)
from src.dash_app.utils.data_loader import generate_pep_url


def create_pep_table_description() -> html.P:
    """
    PEPテーブルの説明を生成する
    """
    return html.P(
        "Scroll the table to view all rows.",
        style={"fontSize": "12px", "color": "#666", "margin": "0"},
    )


def create_pep_table(table_id: str) -> dag.AgGrid:
    """
    PEPテーブルを生成する

    引用関係を表示するためのAG Gridコンポーネントを生成する。
    カラム構成: #, PEP, Title, Status, Created

    Args:
        table_id: テーブルのコンポーネントID

    Returns:
        dag.AgGrid: テーブルコンポーネント
    """
    status_style_conditions = generate_status_styles()

    column_defs = [
        {
            "field": "pep",
            "headerName": "PEP",
            "width": 100,
            "cellRenderer": "markdown",
        },
        {
            "field": "title",
            "headerName": "Title",
            "width": 300,
            "minWidth": 300,
            "wrapText": True,
            "autoHeight": True,
            "cellStyle": {
                "lineHeight": "1.2",
                "paddingTop": "4px",
                "paddingBottom": "4px",
            },
        },
        {
            "field": "status",
            "headerName": "Status",
            "width": 110,
            "cellStyle": {
                "styleConditions": status_style_conditions,
                "defaultStyle": {"textAlign": "center"},
            },
        },
        {
            "field": "created",
            "headerName": "Created",
            "width": 120,
        },
    ]

    return dag.AgGrid(
        id=table_id,
        columnDefs=column_defs,
        rowData=[],
        defaultColDef={
            "sortable": True,
            "resizable": True,
        },
        dashGridOptions={
            "domLayout": "normal",
        },
        style={"height": "500px", "width": "100%"},
        getRowStyle={
            "styleConditions": [
                {
                    "condition": "params.rowIndex % 2 !== 0",
                    "style": {"backgroundColor": "#fafafa"},
                },
            ],
        },
        className="ag-theme-alpine",
    )


def generate_status_styles() -> list[dict]:
    """
    AG Grid用のStatus列スタイル条件を生成する

    STATUS_COLOR_MAPで定義された各ステータスに対して、
    cellStyle.styleConditionsで使用する条件リストを生成する。

    Returns:
        list[dict]: styleConditionsに使用する条件リスト
    """
    return [
        {
            "condition": f"params.value === '{status}'",
            "style": {
                "backgroundColor": bg_color,
                "color": STATUS_FONT_COLOR_MAP.get(status, "#545454"),
            },
        }
        for status, bg_color in STATUS_COLOR_MAP.items()
    ]


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
