"""PEP Metricsタブのレイアウト"""

from dash import dash_table, html
import dash_bootstrap_components as dbc

from src.dash_app.utils.data_loader import load_metadata


def create_metrics_tab_layout() -> html.Div:
    """
    PEP Metricsタブのレイアウトを作成

    Returns:
        html.Div: PEP Metricsタブのレイアウト
    """
    # データ取得日付を取得
    metadata = load_metadata()
    fetched_at = metadata["fetched_at"]

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
            # メタデータセクション
            html.Div(
                [
                    html.Span(
                        [
                            html.Span("Data as of:", style={"fontWeight": "bold"}),
                            f" {fetched_at}",
                        ],
                        style={
                            "fontSize": "12px",
                            "color": "#666",
                            "marginRight": "12px",
                        },
                    ),
                    html.Span(
                        "|",
                        style={
                            "fontSize": "12px",
                            "color": "#999",
                            "marginRight": "12px",
                        },
                    ),
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
                ],
                style={
                    "marginBottom": "16px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "flex-end",
                },
            ),
            # ページサイズ選択 + ページネーションコンポーネント（テーブルの上）
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
                        },
                    ),
                    # ページネーション
                    html.Div(
                        dbc.Pagination(
                            id="metrics-pagination",
                            max_value=15,  # 初期値（コールバックで更新）
                            fully_expanded=False,  # 中程度の表示（... で省略）
                            first_last=True,  # 最初・最後のボタンを表示
                            size="sm",  # 小さいサイズ
                            class_name="metrics-pagination-custom",
                        ),
                        style={
                            "display": "flex",
                            "justifyContent": "flex-end",
                            "margin": "0",
                            "padding": "0",
                        },
                    ),
                ],
                style={
                    "marginBottom": "16px",
                    "display": "flex",
                    "alignItems": "flex-start",
                    "justifyContent": "space-between",
                    "gap": "16px",
                    "margin": "0",
                    "padding": "0",
                },
            ),
            # メトリクステーブル
            dash_table.DataTable(
                id="metrics-table",
                columns=[
                    {
                        "name": "PEP",
                        "id": "pep",
                        "type": "text",
                        "presentation": "markdown",
                    },
                    {"name": "Title", "id": "title", "type": "text"},
                    {"name": "Status", "id": "status", "type": "text"},
                    {"name": "Created", "id": "created", "type": "text"},
                    {"name": "In-degree ⓘ", "id": "in_degree", "type": "numeric"},
                    {"name": "Out-degree ⓘ", "id": "out_degree", "type": "numeric"},
                    {"name": "Degree ⓘ", "id": "degree", "type": "numeric"},
                    {"name": "PageRank ⓘ", "id": "pagerank", "type": "numeric"},
                ],
                data=[],  # 初期は空、コールバックで更新
                sort_action="custom",  # サーバサイドソート
                sort_mode="single",
                page_action="custom",  # サーバサイドページング
                page_size=50,  # 1ページあたり50行
                page_count=0,  # 全ページ数（コールバックで更新）
                style_table={
                    "overflowX": "auto",
                },
                tooltip_header={
                    "in_degree": "Number of PEPs that cite this PEP. PEPs with a high in-degree are widely referenced and often influential.",
                    "out_degree": "Number of PEPs cited by this PEP. PEPs with a high out-degree tend to reference many other PEPs and may serve as integrative or coordinating proposals.",
                    "degree": "Sum of in-degree and out-degree.",
                    "pagerank": "Network-based importance score.",
                },
                tooltip_delay=0,
                tooltip_duration=None,
                style_cell={
                    "textAlign": "left",
                    "padding": "4px 6px",
                    "fontSize": "15px",
                    "height": "auto",
                    "minHeight": "18px",
                },
                style_cell_conditional=[
                    {"if": {"column_id": "pep"}, "width": "80px"},
                    {
                        "if": {"column_id": "title"},
                        "width": "300px",
                        "maxWidth": "300px",
                        "whiteSpace": "normal",
                    },
                    {
                        "if": {"column_id": "status"},
                        "width": "100px",
                        "textAlign": "center",
                    },
                    {"if": {"column_id": "created"}, "width": "100px"},
                    {
                        "if": {"column_id": "in_degree"},
                        "width": "90px",
                        "textAlign": "right",
                    },
                    {
                        "if": {"column_id": "out_degree"},
                        "width": "90px",
                        "textAlign": "right",
                    },
                    {
                        "if": {"column_id": "degree"},
                        "width": "80px",
                        "textAlign": "right",
                    },
                    {
                        "if": {"column_id": "pagerank"},
                        "width": "100px",
                        "textAlign": "right",
                    },
                ],
                style_header={
                    "backgroundColor": "#f5f5f5",
                    "fontWeight": "bold",
                },
                style_data={
                    "lineHeight": "1.1",
                    "verticalAlign": "middle",
                },
                style_data_conditional=[],  # コールバックで動的に設定
                css=[
                    {
                        "selector": ".dash-table-tooltip",
                        "rule": "background-color: #222; color: white; font-size: 12px;",
                    },
                    {
                        "selector": ".previous-next-container",
                        "rule": "display: none;",
                    },
                ],
            ),
            # ページネーションコンポーネント（テーブルの下）
            html.Div(
                dbc.Pagination(
                    id="metrics-pagination-bottom",
                    max_value=15,  # 初期値（コールバックで更新）
                    fully_expanded=False,  # 中程度の表示（... で省略）
                    first_last=True,  # 最初・最後のボタンを表示
                    size="sm",  # 小さいサイズ
                ),
                style={
                    "marginTop": "16px",
                    "display": "flex",
                    "justifyContent": "flex-end",
                },
            ),
        ],
        style={
            "padding": "16px",
        },
    )
