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
            # === Beta注意書き ===
            html.Div(
                "🤖 Beta: Group names and descriptions are AI-generated. They are currently available only in Japanese.",
                style={
                    "backgroundColor": "#fffacd",
                    "border": "1px solid black",
                    "padding": "8px",
                    "borderRadius": "4px",
                    "marginBottom": "16px",
                    "fontSize": "13px",
                },
            ),
            # === 上部セクション: グループ選択 + PEP情報 + 日付情報 ===
            _create_top_section(fetched_at, checked_at),
            # === 操作説明セクション ===
            _create_operation_description_section(),
            # === メインコンテンツ: グラフ（タブ切り替え） + テーブル ===
            _create_main_content_section(),
        ],
        style={
            "padding": "16px",
        },
    )


def _create_top_section(fetched_at: str, checked_at: str) -> html.Div:
    """上部セクション: グループ選択 + PEP情報表示エリア + 日付情報"""
    return html.Div(
        [
            # 左側: グループ選択
            html.Div(
                [
                    _create_group_selector_section(),
                ],
                style={
                    "verticalAlign": "top",
                    "width": "250px",
                    "flexShrink": "0",
                },
            ),
            # 中央: PEP情報表示
            html.Div(
                id="group-pep-info-display",
                children=create_group_initial_info_message(),
                style={
                    "verticalAlign": "top",
                    "marginLeft": "16px",
                    "flexGrow": "1",
                },
            ),
            # 右側: 日付情報
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
                    "flexShrink": "0",
                    "alignSelf": "flex-end",
                },
            ),
        ],
        style={
            "display": "flex",
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
                    # How to Useリンク
                    html.A(
                        "How to Use",
                        href="https://github.com/komo-fr/pep-map/blob/production/README.md#groups-tab",
                        target="_blank",
                        rel="noopener noreferrer",
                        style={
                            "fontSize": "12px",
                            "marginTop": "4px",
                            "display": "block",
                        },
                    ),
                ],
                style={
                    "marginTop": "12px",
                },
            ),
        ],
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
    """メインコンテンツ: グラフエリア（タブ切り替え） + テーブルエリア"""
    return html.Div(
        [
            # 左側: ネットワークグラフ（タブ切り替え）
            html.Div(
                [
                    _create_network_tabs(),
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


def _create_network_tabs() -> html.Div:
    """ネットワークグラフのタブ（Full Network / Group Network）を生成する

    CSSベースの切り替えを使用して、両方のグラフをDOMに保持し、
    ズーム・パン状態を維持する。
    """
    # タブボタンの共通スタイル
    tab_button_base_style = {
        "padding": "8px 16px",
        "border": "1px solid #ddd",
        "borderBottom": "none",
        "backgroundColor": "#f5f5f5",
        "cursor": "pointer",
        "marginRight": "4px",
        "borderRadius": "4px 4px 0 0",
    }
    tab_button_selected_style = {
        **tab_button_base_style,
        "backgroundColor": "#fff",
        "fontWeight": "bold",
        "borderBottom": "1px solid #fff",
        "marginBottom": "-1px",
    }

    return html.Div(
        [
            # タブボタン
            html.Div(
                [
                    html.Button(
                        "Full Network",
                        id="full-network-tab-button",
                        n_clicks=0,
                        style=tab_button_selected_style,
                    ),
                    html.Button(
                        "Group Network",
                        id="group-network-tab-button",
                        n_clicks=0,
                        style=tab_button_base_style,
                    ),
                ],
                style={
                    "borderBottom": "1px solid #ddd",
                    "paddingLeft": "4px",
                },
            ),
            # タブコンテンツコンテナ（position: relativeで子要素を重ねる）
            html.Div(
                [
                    # Full Networkコンテンツ（初期表示）
                    html.Div(
                        id="full-network-content",
                        children=_create_full_network_tab_content(),
                        style={
                            "visibility": "visible",
                            "position": "relative",
                            "zIndex": "1",
                        },
                    ),
                    # Group Networkコンテンツ（初期非表示）
                    html.Div(
                        id="group-network-content",
                        children=_create_subgraph_tab_content(),
                        style={
                            "visibility": "hidden",
                            "position": "absolute",
                            "top": "0",
                            "left": "0",
                            "right": "0",
                            "zIndex": "0",
                        },
                    ),
                ],
                style={"position": "relative"},
            ),
        ],
    )


def _create_full_network_tab_content() -> html.Div:
    """Full Networkタブの内容を生成する"""
    return html.Div(
        [
            # 説明テキスト
            html.P(
                [
                    html.Strong("Color"),
                    " indicates the group of each PEP.",
                ],
                style={"fontSize": "12px", "color": "#666", "marginBottom": "4px"},
            ),
            html.P(
                [
                    html.Strong("Node sizes"),
                    " in the network graph are based on PageRank computed from the full citation network.",
                ],
                style={"fontSize": "12px", "color": "#666", "marginBottom": "8px"},
            ),
            # ネットワークグラフ
            _create_group_graph(),
        ],
        style={"paddingTop": "8px"},
    )


def _create_subgraph_tab_content() -> html.Div:
    """Group Networkタブの内容（サブグラフ）を生成する"""
    return html.Div(
        [
            # 説明テキスト
            html.P(
                [
                    html.Strong("Node sizes"),
                    " are based on PageRank computed within the selected group.",
                ],
                style={"fontSize": "12px", "color": "#666", "marginBottom": "4px"},
            ),
            html.P(
                [
                    html.Strong("Color"),
                    " indicates the status of each PEP.",
                ],
                style={"fontSize": "12px", "color": "#666", "marginBottom": "8px"},
            ),
            # サブグラフ表示エリア（初期状態はプレースホルダー + 非表示Cytoscape）
            html.Div(
                id="subgraph-container",
                children=_create_subgraph_placeholder_with_dummy(),
                style={"minHeight": "600px"},
            ),
        ],
        style={"paddingTop": "8px"},
    )


def _create_group_graph() -> cyto.Cytoscape:
    """グループネットワークグラフコンポーネントを生成する"""
    elements = build_group_cytoscape_elements()

    return cyto.Cytoscape(
        id="group-full-network-graph",
        elements=elements,
        layout=get_preset_layout_options(),
        style={
            "width": "100%",
            "height": "800px",
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
            # グループ名表示エリア（初期状態は空）
            html.P(
                id="group-name-display",
                children="",
                style={
                    "fontWeight": "bold",
                    "fontSize": "14px",
                    "marginBottom": "4px",
                    "marginTop": "0",
                },
            ),
            # グループ説明表示エリア（初期状態は空、非表示）
            html.Div(
                id="group-description-display",
                children="",
                style={
                    "display": "none",  # 初期状態は非表示
                },
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


def _create_subgraph_placeholder() -> html.Div:
    """サブグラフ未選択時のプレースホルダーを生成する（テキストのみ）"""
    return html.Div(
        "Select a group to view its subgraph",
        style={
            "height": "600px",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "backgroundColor": "#f5f5f5",
            "border": "1px solid #ddd",
            "color": "#999",
            "fontSize": "16px",
        },
    )


def _create_subgraph_placeholder_with_dummy() -> html.Div:
    """サブグラフ未選択時のプレースホルダー + ダミーCytoscapeを生成する

    コールバック登録時にgroup-subgraph-network-graphが存在する必要があるため、
    初期状態では非表示のCytoscapeコンポーネントを含める。
    """
    return html.Div(
        [
            # プレースホルダーテキスト
            html.Div(
                "Select a group to view its subgraph",
                style={
                    "height": "600px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "backgroundColor": "#f5f5f5",
                    "border": "1px solid #ddd",
                    "color": "#999",
                    "fontSize": "16px",
                },
            ),
            # ダミーのCytoscapeコンポーネント（コールバック登録用、非表示）
            cyto.Cytoscape(
                id="group-subgraph-network-graph",
                elements=[],
                layout={"name": "preset"},
                style={"display": "none"},
            ),
        ]
    )
