"""Timelineタブのレイアウト"""

from dash import dash_table, dcc, html

from src.dash_app.components import (
    create_empty_figure,
    create_initial_info_message,
    create_status_legend,
)
from src.dash_app.utils.data_loader import load_metadata


def create_timeline_layout() -> html.Div:
    """
    Timelineタブのレイアウトを生成する

    Returns:
        html.Div: Timelineタブのレイアウト
    """
    # データ取得日付を取得
    metadata = load_metadata()
    fetched_at = metadata["fetched_at"]

    return html.Div(
        [
            # === 上部セクション: 入力欄 + PEP情報 ===
            _create_top_section(),
            # === Status凡例セクション ===
            _create_legend_section(),
            # === タイムライングラフセクション ===
            _create_graph_section(),
            # === データ取得日付セクション ===
            _create_metadata_section(fetched_at),
            # === テーブルセクション ===
            _create_tables_section(),
        ],
        style={
            "padding": "16px",
        },
    )


def _create_top_section() -> html.Div:
    """上部セクション: PEP番号入力欄 + PEP情報表示エリア"""
    return html.Div(
        [
            # 左側: PEP番号入力
            html.Div(
                [
                    html.Label(
                        "PEP:",
                        style={
                            "fontWeight": "bold",
                            "marginRight": "8px",
                        },
                    ),
                    dcc.Input(
                        id="pep-input",
                        type="number",
                        placeholder="",
                        style={
                            "width": "80px",
                        },
                    ),
                    # エラーメッセージ表示エリア
                    html.Div(
                        id="pep-error-message",
                        style={
                            "color": "red",
                            "fontSize": "14px",
                            "marginTop": "4px",
                        },
                    ),
                ],
                style={
                    "display": "inline-block",
                    "verticalAlign": "top",
                    "width": "150px",
                },
            ),
            # 右側: PEP情報表示
            html.Div(
                id="pep-info-display",
                children=create_initial_info_message(),
                style={
                    "display": "inline-block",
                    "verticalAlign": "top",
                    "marginLeft": "16px",
                },
            ),
        ],
        style={
            "marginBottom": "16px",
            "borderBottom": "1px solid #ddd",
            "paddingBottom": "16px",
        },
    )


def _create_legend_section() -> html.Div:
    """Status凡例セクション"""
    return html.Div(
        create_status_legend(),
        style={
            "marginBottom": "16px",
        },
    )


def _create_graph_section() -> html.Div:
    """タイムライングラフセクション"""
    return html.Div(
        dcc.Graph(
            id="timeline-graph",
            figure=create_empty_figure(),
            style={
                "height": "300px",
            },
        ),
        style={
            "marginBottom": "16px",
        },
    )


def _create_metadata_section(fetched_at: str) -> html.Div:
    """データ取得日付セクション"""
    return html.Div(
        html.P(
            f"Data as of: {fetched_at}",
            style={
                "fontSize": "12px",
                "color": "#666",
            },
        ),
        style={
            "marginBottom": "16px",
        },
    )


def _create_tables_section() -> html.Div:
    """テーブルセクション: 引用しているPEP + 引用されているPEP"""
    return html.Div(
        [
            # 左側: 選択中PEPを引用しているPEP
            html.Div(
                [
                    html.H4("PEP is linked from...", style={"marginBottom": "8px"}),
                    _create_pep_table("citing-peps-table"),
                ],
                style={
                    "display": "inline-block",
                    "width": "48%",
                    "verticalAlign": "top",
                    "marginRight": "2%",
                },
            ),
            # 右側: 選択中PEPから引用されているPEP
            html.Div(
                [
                    html.H4("PEP links to...", style={"marginBottom": "8px"}),
                    _create_pep_table("cited-peps-table"),
                ],
                style={
                    "display": "inline-block",
                    "width": "48%",
                    "verticalAlign": "top",
                },
            ),
        ],
    )


def _create_pep_table(table_id: str) -> dash_table.DataTable:  # type: ignore[name-defined]
    """PEPテーブルを生成する"""
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
        },
        style_cell={
            "textAlign": "left",
            "padding": "8px",
            "fontSize": "13px",
        },
        style_header={
            "fontWeight": "bold",
            "backgroundColor": "#f5f5f5",
        },
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "#fafafa",
            }
        ],
    )
