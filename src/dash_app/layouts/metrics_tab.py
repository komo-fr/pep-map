"""PEP Metricsタブのレイアウト"""

import dash_ag_grid as dag
import dash_bootstrap_components as dbc  # type: ignore[import-untyped]
from dash import html

from src.dash_app.utils.data_loader import load_metadata, load_metrics_styles


def create_metrics_tab_layout() -> html.Div:
    """
    PEP Metricsタブのレイアウトを作成

    Returns:
        html.Div: PEP Metricsタブのレイアウト
    """
    # データ取得日付とチェック日付を取得
    metadata = load_metadata()
    fetched_at = metadata["fetched_at"]
    checked_at = metadata["checked_at"]

    # 事前計算されたスタイル条件を取得
    styles = load_metrics_styles()

    column_defs = [
        {
            "field": "pep",
            "headerName": "PEP",
            "minWidth": 100,
            "cellRenderer": "markdown",
        },
        {
            "field": "title",
            "headerName": "Title",
            "minWidth": 300,
            "flex": 1,
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
            "minWidth": 110,
            "cellStyle": {
                "styleConditions": styles.get("status", []),
                "defaultStyle": {"textAlign": "center"},
            },
        },
        {
            "field": "created",
            "headerName": "Created",
            "minWidth": 120,
        },
        {
            "field": "in_degree",
            "headerName": "In-degree ⓘ",
            "headerTooltip": "Number of PEPs that cite this PEP. PEPs with a high in-degree are widely referenced and often influential.",
            "minWidth": 120,
            "type": "numericColumn",
            "cellStyle": {
                "styleConditions": styles.get("in_degree", []),
            },
        },
        {
            "field": "out_degree",
            "headerName": "Out-degree ⓘ",
            "headerTooltip": "Number of PEPs cited by this PEP. PEPs with a high out-degree tend to reference many other PEPs and may serve as integrative or coordinating proposals.",
            "minWidth": 125,
            "type": "numericColumn",
            "cellStyle": {
                "styleConditions": styles.get("out_degree", []),
            },
        },
        {
            "field": "degree",
            "headerName": "Degree ⓘ",
            "headerTooltip": "Sum of in-degree and out-degree.",
            "minWidth": 110,
            "type": "numericColumn",
            "cellStyle": {
                "styleConditions": styles.get("degree", []),
            },
        },
        {
            "field": "pagerank",
            "headerName": "PageRank ⓘ",
            "headerTooltip": "Network-based importance score.",
            "minWidth": 120,
            "type": "numericColumn",
            "cellStyle": {
                "styleConditions": styles.get("pagerank", []),
            },
        },
    ]

    return html.Div(
        [
            # 説明文
            html.Div(
                [
                    html.P(
                        "This table shows structural metrics derived from PEP citation relationships.",
                        style={"marginBottom": "8px"},
                    ),
                    html.Ul(
                        [
                            html.Li(
                                [
                                    html.Code("In-degree"),
                                    " : Number of PEPs that cite a given PEP. PEPs with a high in-degree are widely referenced and often influential.",
                                ]
                            ),
                            html.Li(
                                [
                                    html.Code("Out-degree"),
                                    " : Number of PEPs cited by a given PEP. PEPs with a high out-degree tend to reference many other PEPs and may serve as integrative or coordinating proposals.",
                                ]
                            ),
                            html.Li(
                                [
                                    html.Code("Degree"),
                                    " : Sum of in-degree and out-degree.",
                                ]
                            ),
                            html.Li(
                                [
                                    html.Code("PageRank"),
                                    " : Network-based importance score computed from the overall citation structure.",
                                ]
                            ),
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
            # 検索ボックス + メタデータセクション（1行、下寄せ）
            html.Div(
                [
                    # 検索ボックス（左寄せ）
                    html.Div(
                        dbc.Input(
                            id="metrics-search-input",
                            type="text",
                            placeholder="Search by title... (e.g., 'async coroutine' for AND search)",
                            debounce=True,
                            style={
                                "fontSize": "14px",
                                "padding": "8px 12px",
                                "height": "32px",
                            },
                        ),
                        style={
                            "flex": "0 0 auto",
                            "minWidth": "400px",
                            "maxWidth": "500px",
                        },
                    ),
                    # データ取得日付・チェック日付（右寄せ、縦並び）
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Strong("Data updated:"),
                                    f" {fetched_at}",
                                ],
                                style={
                                    "fontSize": "12px",
                                    "color": "#666",
                                },
                            ),
                            html.Div(
                                [
                                    html.Strong("Last checked:"),
                                    f" {checked_at}",
                                ],
                                style={
                                    "fontSize": "12px",
                                    "color": "#666",
                                },
                            ),
                        ],
                        style={
                            "marginLeft": "auto",
                        },
                    ),
                ],
                style={
                    "marginBottom": "8px",
                    "marginTop": "8px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "space-between",
                    "gap": "16px",
                },
            ),
            # ページサイズ選択 + ページネーション + Download CSVリンク（1行）
            html.Div(
                [
                    # 左側: ページサイズドロップダウン + ページネーション
                    html.Div(
                        [
                            # ページサイズドロップダウン
                            html.Div(
                                [
                                    html.Label(
                                        "Rows per page:",
                                        style={
                                            "marginRight": "6px",
                                            "fontSize": "13px",
                                            "fontWeight": "500",
                                            "whiteSpace": "nowrap",
                                            "lineHeight": "1",
                                            "margin": "0",
                                            "padding": "0",
                                            "display": "flex",
                                            "alignItems": "center",
                                        },
                                    ),
                                    dbc.Select(
                                        id="metrics-page-size-select",
                                        options=[
                                            {"label": "50", "value": 50},
                                            {"label": "100", "value": 100},
                                            {"label": "200", "value": 200},
                                            {"label": "All", "value": -1},
                                        ],
                                        value=50,
                                        style={
                                            "width": "80px",
                                            "height": "32px",
                                            "fontSize": "13px",
                                            "margin": "0 !important",
                                            "padding": "4px 6px",
                                        },
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "margin": "0",
                                    "padding": "0",
                                    "marginRight": "16px",
                                },
                            ),
                            # ページネーション
                            html.Div(
                                dbc.Pagination(
                                    id="metrics-pagination-top",
                                    max_value=1,
                                    fully_expanded=False,
                                    first_last=True,
                                    size="sm",
                                ),
                                style={
                                    "display": "flex",
                                    "margin": "12px 0 0 0",
                                    "padding": "0",
                                    "alignItems": "center",
                                },
                            ),
                        ],
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "margin": "0",
                            "padding": "0",
                        },
                    ),
                    # 右側: Download CSVリンク
                    html.Div(
                        html.A(
                            "Download CSV",
                            href="https://raw.githubusercontent.com/komo-fr/pep-map/production/data/processed/node_metrics.csv",
                            style={
                                "fontSize": "12px",
                                "color": "#0066cc",
                                "textDecoration": "underline",
                                "cursor": "pointer",
                            },
                        ),
                        style={
                            "marginLeft": "auto",
                            "margin": "0",
                            "padding": "0",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "space-between",
                    "margin": "0",
                    "padding": "0",
                },
            ),
            # メトリクステーブル
            dag.AgGrid(
                id="metrics-table",
                columnDefs=column_defs,
                rowData=[],
                columnSize="responsiveSizeToFit",
                defaultColDef={
                    "sortable": True,
                    "resizable": True,
                },
                dashGridOptions={
                    "pagination": True,
                    "paginationPageSize": 50,
                    "paginationPageSizeSelector": [50, 100, 200],
                    "tooltipShowDelay": 0,
                    "domLayout": "autoHeight",
                },
                style={"width": "100%"},
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
        style={
            "padding": "16px",
        },
    )
