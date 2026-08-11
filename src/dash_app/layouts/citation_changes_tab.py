"""Citation Changesタブのレイアウト"""

import dash_ag_grid as dag
from dash import html

from src.dash_app.utils.constants import (
    CHANGE_TYPE_COLOR_MAP,
    CHANGE_TYPE_FONT_COLOR_MAP,
)
from src.dash_app.utils.data_loader import load_citation_changes, load_metadata


def create_citation_changes_tab_layout() -> html.Div:
    """
    Citation Changesタブのレイアウトを作成

    Returns:
        html.Div: Citation Changesタブのレイアウト
    """
    # データを読み込む
    df = load_citation_changes()

    # チェック日付を取得
    metadata = load_metadata()
    checked_at = metadata["checked_at"]

    # citing_markdown → citing, cited_markdown → cited にリネーム
    # 元のint型カラムを先にdropしてから、markdown版をリネーム
    df = df.drop(columns=["citing", "cited"]).rename(
        columns={"citing_markdown": "citing", "cited_markdown": "cited"}
    )

    # Change Type ごとの背景色とフォント色のスタイル条件を生成
    change_type_style_conditions = [
        {
            "condition": f"params.value === '{change_type}'",
            "style": {
                "backgroundColor": bg_color,
                "color": CHANGE_TYPE_FONT_COLOR_MAP[change_type],
                "textAlign": "center",
            },
        }
        for change_type, bg_color in CHANGE_TYPE_COLOR_MAP.items()
    ]

    column_defs = [
        {
            "field": "detected",
            "headerName": "Detected",
            "width": 120,
            "sort": "desc",
        },
        {
            "field": "change_type",
            "headerName": "Change",
            "width": 100,
            "cellStyle": {
                "styleConditions": change_type_style_conditions,
                "defaultStyle": {"textAlign": "center"},
            },
            "headerClass": "ag-header-cell-center",
        },
        {
            "headerName": "PEP",
            "children": [
                {
                    "field": "citing",
                    "headerName": "Citing",
                    "width": 100,
                    "cellRenderer": "markdown",
                    "headerClass": "ag-header-cell-center",
                },
                {
                    "field": "cited",
                    "headerName": "Cited",
                    "width": 100,
                    "cellRenderer": "markdown",
                    "headerClass": "ag-header-cell-center",
                },
            ],
        },
        {
            "headerName": "Title",
            "children": [
                {
                    "field": "citing_title",
                    "headerName": "Citing",
                    "minWidth": 150,
                    "flex": 1,
                    "headerClass": "ag-header-cell-center",
                },
                {
                    "field": "cited_title",
                    "headerName": "Cited",
                    "minWidth": 150,
                    "flex": 1,
                    "headerClass": "ag-header-cell-center",
                },
            ],
        },
        {
            "headerName": "Count",
            "children": [
                {
                    "field": "count_before",
                    "headerName": "Before",
                    "width": 90,
                    "headerClass": "ag-header-cell-center",
                },
                {
                    "field": "count_after",
                    "headerName": "After",
                    "width": 90,
                    "headerClass": "ag-header-cell-center",
                },
            ],
        },
    ]

    return html.Div(
        [
            # 説明文
            html.Div(
                [
                    html.P(
                        "This table lists changes in citation relationships (Added, Changed, or Deleted) detected during data checks.",
                        style={"marginBottom": "8px"},
                    ),
                    html.P(
                        [
                            html.Strong("Note:"),
                            " ",
                            html.Code("Detected"),
                            " indicates when the change was observed by this system, not when the change originally occurred in the PEP.",
                        ],
                        style={"marginBottom": "8px", "color": "#666"},
                    ),
                ],
                style={
                    "fontSize": "14px",
                    "color": "#333",
                },
            ),
            # 区切り線
            html.Hr(
                style={
                    "margin": "16px 0",
                    "border": "none",
                    "borderTop": "1px solid #888",
                }
            ),
            # Last checked（右寄せ）
            html.Div(
                [
                    html.Strong("Last checked:"),
                    f" {checked_at}",
                ],
                style={
                    "fontSize": "12px",
                    "color": "#666",
                    "textAlign": "right",
                    "margin": "8px 0",
                },
            ),
            # AG Gridコンポーネント
            dag.AgGrid(
                id="citation-changes-table",
                columnDefs=column_defs,
                rowData=df.to_dict("records"),
                defaultColDef={
                    "sortable": True,
                    "filter": True,
                    "floatingFilter": True,
                    "resizable": True,
                },
                dashGridOptions={
                    "domLayout": "autoHeight",
                },
                getRowStyle={
                    "styleConditions": [
                        {
                            "condition": "params.rowIndex % 2 !== 0",
                            "style": {"backgroundColor": "#fafafa"},
                        },
                    ],
                },
                className="ag-theme-alpine",
            ),
        ],
        style={"padding": "20px"},
    )
