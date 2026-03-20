"""Groupタブのレイアウト"""

import dash_cytoscape as cyto
from dash import dcc, html, dash_table

from src.dash_app.components.group_network_graph import (
    build_group_cytoscape_elements,
    get_group_base_stylesheet,
    get_preset_layout_options,
)
from src.dash_app.components.pep_info import create_group_initial_info_message
from src.dash_app.components.pep_tables import generate_status_styles
from src.dash_app.utils.data_loader import get_group_list, load_metadata


def create_group_tab_layout() -> html.Div:
    """
    Groupタブのレイアウトを生成する

    Returns:
        html.Div: Groupタブのレイアウト
    """
    metadata = load_metadata()
    fetched_at = metadata["fetched_at"]
    checked_at = metadata["checked_at"]

    return html.Div(
        [
            # === 選択ソースを追跡するStore ===
            # "dropdown": ドロップダウンから選択（赤枠非表示）
            # "node_tap": ノードタップから選択（赤枠表示）
            dcc.Store(id="group-selection-source", data="dropdown"),
            # === 上部セクション: グループ選択 + PEP情報 ===
            _create_top_section(),
            # === 注意書き + データ取得日付セクション ===
            _create_note_and_data_info_section(fetched_at, checked_at),
            # === 操作説明セクション ===
            _create_operation_description_section(),
            # === メインコンテンツ: グラフ + テーブル ===
            _create_main_content_section(),
        ],
        style={
            "padding": "16px",
        },
    )


def _create_top_section() -> html.Div:
    """上部セクション: グループ選択 + PEP情報表示エリア"""
    return html.Div(
        [
            # 左側: グループ選択
            html.Div(
                [
                    _create_group_selector_section(),
                ],
                style={
                    "display": "inline-block",
                    "verticalAlign": "top",
                    "width": "250px",
                },
            ),
            # 右側: PEP情報表示
            html.Div(
                id="group-pep-info-display",
                children=create_group_initial_info_message(),
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


def _create_group_selector_section() -> html.Div:
    """グループ選択ドロップダウンセクション + PEP番号入力欄"""
    group_options = get_group_list()

    return html.Div(
        [
            # グループ選択ドロップダウン
            html.Div(
                [
                    html.Label(
                        "Group:",
                        style={
                            "fontWeight": "bold",
                            "marginRight": "8px",
                        },
                    ),
                    dcc.Dropdown(
                        id="group-selector-dropdown",
                        options=group_options,
                        value="all",
                        clearable=False,
                        maxHeight=500,
                        style={
                            "width": "250px",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                },
            ),
            # PEP番号入力欄（グループ選択のショートカット）
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
                        id="group-pep-input",
                        type="text",
                        placeholder="Enter PEP number",
                        inputMode="numeric",
                        pattern="[0-9]*",
                        style={
                            "width": "180px",
                        },
                    ),
                    # エラーメッセージ表示エリア
                    html.Div(
                        id="group-pep-error-message",
                        style={
                            "color": "red",
                            "fontSize": "14px",
                            "marginTop": "4px",
                        },
                    ),
                ],
                style={
                    "marginTop": "12px",
                },
            ),
        ],
    )


def _create_note_and_data_info_section(fetched_at: str, checked_at: str) -> html.Div:
    """注意書き + データ取得日付セクション"""
    return html.Div(
        [
            # 左側: Color と Node sizes の説明
            html.Div(
                [
                    html.P(
                        [
                            html.Strong("Color"),
                            " indicates the group of each PEP.",
                        ],
                        style={
                            "fontSize": "12px",
                            "color": "#666",
                            "margin": "0",
                        },
                    ),
                    html.P(
                        [
                            html.Strong("Node sizes"),
                            " in the network graph are based on PageRank computed from the full citation network.",
                        ],
                        style={
                            "fontSize": "12px",
                            "color": "#666",
                            "margin": "0",
                        },
                    ),
                ],
            ),
            # 右側: Data updated と Last checked（右寄せ）
            html.Div(
                [
                    html.P(
                        [
                            html.Strong("Data updated:"),
                            f" {fetched_at}",
                        ],
                        style={
                            "fontSize": "12px",
                            "color": "#666",
                            "margin": "0",
                            "textAlign": "right",
                        },
                    ),
                    html.P(
                        [
                            html.Strong("Last checked:"),
                            f" {checked_at}",
                        ],
                        style={
                            "fontSize": "12px",
                            "color": "#666",
                            "margin": "0",
                            "textAlign": "right",
                        },
                    ),
                ],
                style={
                    "marginLeft": "auto",
                },
            ),
        ],
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "flex-start",
            "marginBottom": "8px",
        },
    )


def _create_operation_description_section() -> html.Div:
    """操作説明セクション"""
    return html.Div(
        [
            html.P(
                [
                    html.Strong("Zoom in/out: "),
                    "Pinch in/out or use the mouse wheel.",
                    html.Span("", style={"marginRight": "16px"}),
                    html.Strong("Move a node: "),
                    "Click and drag it.",
                    html.Span("", style={"marginRight": "16px"}),
                    html.Strong("Select group: "),
                    "Use dropdown or tap a node.",
                ],
                style={"fontSize": "12px", "color": "#666", "margin": "0"},
            ),
        ],
        style={
            "margin": "10px 0",
        },
    )


def _create_main_content_section() -> html.Div:
    """メインコンテンツ: グラフエリア + テーブルエリア"""
    return html.Div(
        [
            # 左側: ネットワークグラフ
            html.Div(
                [
                    _create_group_graph(),
                ],
                style={
                    "display": "inline-block",
                    "width": "55%",
                    "verticalAlign": "top",
                },
            ),
            # 右側: テーブルエリア
            html.Div(
                [
                    _create_group_pep_table_section(),
                ],
                style={
                    "display": "inline-block",
                    "width": "43%",
                    "verticalAlign": "top",
                    "marginLeft": "2%",
                },
            ),
        ],
    )


def _create_group_graph() -> cyto.Cytoscape:
    """グループネットワークグラフコンポーネントを生成する"""
    elements = build_group_cytoscape_elements()

    return cyto.Cytoscape(
        id="group-network-graph",
        elements=elements,
        layout=get_preset_layout_options(),
        style={
            "width": "100%",
            "height": "600px",
            "border": "1px solid #ddd",
            "backgroundColor": "#fafafa",
        },
        stylesheet=get_group_base_stylesheet(),
    )


def _create_group_pep_table_section() -> html.Div:
    """グループPEPテーブルセクション"""
    return html.Div(
        [
            html.H4(
                id="group-pep-table-title",
                children="Select a group to view PEPs",
                style={"marginBottom": "8px", "marginTop": "8px"},
            ),
            html.P(
                "Scroll the table to view all rows.",
                style={"fontSize": "12px", "color": "#666", "marginBottom": "2px"},
            ),
            html.P(
                "All metrics in this table are calculated within the selected group.",
                style={"fontSize": "12px", "color": "#666", "marginBottom": "8px"},
            ),
            _create_group_pep_table(),
        ],
    )


def _create_group_pep_table() -> dash_table.DataTable:  # type: ignore[name-defined]
    """グループPEPテーブルを生成する"""
    # Status列の条件付きスタイルを生成
    status_styles = generate_status_styles()

    return dash_table.DataTable(  # type: ignore[attr-defined]
        id="group-pep-table",
        columns=[
            {"name": "PEP", "id": "pep", "type": "text", "presentation": "markdown"},
            {"name": "Title", "id": "title", "type": "text"},
            {"name": "Status", "id": "status", "type": "text"},
            {"name": "Created", "id": "created", "type": "text"},
            {"name": "In-degree", "id": "in_degree", "type": "numeric"},
            {"name": "Out-degree", "id": "out_degree", "type": "numeric"},
            {"name": "Degree", "id": "degree", "type": "numeric"},
            {"name": "PageRank", "id": "pagerank", "type": "text"},
        ],
        data=[],
        sort_action="native",
        sort_mode="single",
        page_action="none",
        style_table={
            "overflowX": "auto",
            "overflowY": "scroll",
            "height": "500px",
        },
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
                "width": "250px",
                "minWidth": "250px",
                "whiteSpace": "normal",
            },
            {"if": {"column_id": "status"}, "width": "90px", "textAlign": "center"},
            {"if": {"column_id": "created"}, "width": "90px"},
            {
                "if": {"column_id": "in_degree"},
                "minWidth": "30px",
                "width": "30px",
                "textAlign": "right",
            },
            {
                "if": {"column_id": "out_degree"},
                "minWidth": "30px",
                "width": "30px",
                "textAlign": "right",
            },
            {
                "if": {"column_id": "degree"},
                "minWidth": "30px",
                "width": "30px",
                "textAlign": "right",
            },
            {
                "if": {"column_id": "pagerank"},
                "minWidth": "30px",
                "width": "30px",
                "textAlign": "right",
            },
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
        markdown_options={"html": True},
    )
