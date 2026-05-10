"""Groupタブのレイアウト"""

import json

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
from dash import dcc, html

from src.dash_app.components.group_network_graph import (
    build_group_cytoscape_elements,
    get_group_base_stylesheet,
    get_preset_layout_options,
)
from src.dash_app.components.group_to_group_network_graph import (
    build_group_to_group_cytoscape_elements,
    get_group_to_group_base_stylesheet,
    get_group_to_group_layout_options,
)
from src.dash_app.components.pep_info import create_group_initial_info_message
from src.dash_app.components.group_created_timeline import (
    create_group_timeline_empty_figure,
)
from src.dash_app.styles.tab_styles import (
    TAB_BUTTON_SELECTED_STYLE,
    TAB_BUTTON_UNSELECTED_STYLE,
    TAB_CONTENT_VISIBLE_STYLE,
    TAB_CONTENT_HIDDEN_STYLE,
)
from src.dash_app.utils.constants import STATUS_COLOR_MAP, STATUS_FONT_COLOR_MAP
from src.dash_app.utils.data_loader import (
    get_group_list,
    load_metadata,
    get_all_group_tooltip_info,
)


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
                    "padding": "4px 8px",
                    "borderRadius": "4px",
                    "marginBottom": "12px",
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
        "borderTop": "3px solid #DDAD3E",
        "borderBottom": "1px solid #fff",
        "marginBottom": "-1px",
    }

    return html.Div(
        [
            # タブボタン
            html.Div(
                [
                    html.Button(
                        "Full PEP Network",
                        id="full-network-tab-button",
                        n_clicks=0,
                        style=tab_button_selected_style,
                    ),
                    html.Button(
                        "Selected Group Network",
                        id="group-network-tab-button",
                        n_clicks=0,
                        style=tab_button_base_style,
                    ),
                    html.Button(
                        "Group-to-Group Network",
                        id="group-to-group-tab-button",
                        n_clicks=0,
                        style=tab_button_base_style,
                    ),
                    # ツールチップ
                    dbc.Tooltip(
                        "Use this view to see the selected group in the context of the entire PEP citation network.",
                        target="full-network-tab-button",
                        placement="bottom",
                        style={"maxWidth": "300px"},
                    ),
                    dbc.Tooltip(
                        "Use this view to see which PEPs are central within the selected group and how they cite each other.",
                        target="group-network-tab-button",
                        placement="bottom",
                        style={"maxWidth": "300px"},
                    ),
                    dbc.Tooltip(
                        "Use this view to see how the selected group is connected to other groups through citations.",
                        target="group-to-group-tab-button",
                        placement="bottom",
                        style={"maxWidth": "300px"},
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
                    # Group-to-Group Networkコンテンツ（初期非表示）
                    html.Div(
                        id="group-to-group-content",
                        children=_create_group_to_group_tab_content(),
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
                style={"fontSize": "12px", "color": "#666", "margin": "0"},
            ),
            html.P(
                [
                    html.Strong("Node sizes"),
                    " in the network graph are based on PageRank computed from the full citation network.",
                ],
                style={"fontSize": "12px", "color": "#666", "margin": "0 0 4px 0"},
            ),
            # ネットワークグラフ
            _create_group_graph(),
        ],
        style={"paddingTop": "4px"},
    )


def _create_subgraph_tab_content() -> html.Div:
    """Group Networkタブの内容（サブグラフ）を生成する"""
    return html.Div(
        [
            # 説明テキスト
            html.P(
                [
                    html.Strong("Color"),
                    " indicates the status of each PEP.",
                ],
                style={"fontSize": "12px", "color": "#666", "margin": "0"},
            ),
            html.P(
                [
                    html.Strong("Node sizes"),
                    " are based on PageRank computed within the selected group.",
                ],
                style={"fontSize": "12px", "color": "#666", "margin": "0 0 4px 0"},
            ),
            # サブグラフ表示エリア（初期状態はプレースホルダー + 非表示Cytoscape）
            html.Div(
                id="subgraph-container",
                children=create_subgraph_placeholder_with_dummy(),
                style={"minHeight": "600px"},
            ),
        ],
        style={"paddingTop": "4px"},
    )


def _create_group_to_group_tab_content() -> html.Div:
    """Group-to-Group Networkタブの内容を生成する"""
    return html.Div(
        [
            # 説明テキスト
            html.P(
                [
                    html.Strong("Color"),
                    " indicates the group (same as Full Network).",
                ],
                style={"fontSize": "12px", "color": "#666", "margin": "0"},
            ),
            html.P(
                [
                    html.Strong("Node sizes"),
                    " are based on the number of PEPs in each group.",
                ],
                style={"fontSize": "12px", "color": "#666", "margin": "0"},
            ),
            html.P(
                [
                    html.Strong("Edge widths"),
                    " are based on the number of citations between groups.",
                ],
                style={"fontSize": "12px", "color": "#666", "margin": "0 0 4px 0"},
            ),
            # ネットワークグラフ
            _create_group_to_group_graph(),
        ],
        style={"paddingTop": "4px"},
    )


def _create_group_to_group_graph() -> cyto.Cytoscape:
    """Group-to-Groupネットワークグラフコンポーネントを生成する"""
    elements = build_group_to_group_cytoscape_elements()

    return cyto.Cytoscape(
        id="group-to-group-network-graph",
        elements=elements,
        layout=get_group_to_group_layout_options(),
        style={
            "width": "100%",
            "height": "800px",
            "border": "1px solid #ddd",
            "backgroundColor": "#fafafa",
        },
        stylesheet=get_group_to_group_base_stylesheet(),
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
    """グループPEPテーブルセクション（PEPs / Created タブ付き）"""
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
            # 隣接グループ表示エリア（初期状態は非表示）
            html.Div(
                id="adjacent-groups-display",
                children="",
                style={
                    "display": "none",  # 初期状態は非表示
                },
            ),
            # PEPs / Created タブ
            _create_pep_content_tabs(),
        ],
    )


def _create_pep_content_tabs() -> html.Div:
    """PEPsタブとCreatedタブを生成する"""
    return html.Div(
        [
            # タブボタン
            html.Div(
                [
                    html.Button(
                        "PEPs",
                        id="group-peps-tab-button",
                        n_clicks=0,
                        style=TAB_BUTTON_SELECTED_STYLE,
                    ),
                    html.Button(
                        "Created",
                        id="group-created-tab-button",
                        n_clicks=0,
                        style=TAB_BUTTON_UNSELECTED_STYLE,
                    ),
                    dbc.Tooltip(
                        "View PEPs in this group as a table with metrics.",
                        target="group-peps-tab-button",
                        placement="bottom",
                    ),
                    dbc.Tooltip(
                        "View PEP creation timeline to see when PEPs were created.",
                        target="group-created-tab-button",
                        placement="bottom",
                    ),
                ],
                style={
                    "borderBottom": "1px solid #ddd",
                    "paddingLeft": "4px",
                },
            ),
            # タブコンテンツコンテナ
            html.Div(
                [
                    # PEPsタブコンテンツ（初期表示）
                    html.Div(
                        id="group-peps-content",
                        children=_create_peps_tab_content(),
                        style=TAB_CONTENT_VISIBLE_STYLE,
                    ),
                    # Createdタブコンテンツ（初期非表示）
                    html.Div(
                        id="group-created-content",
                        children=_create_created_tab_content(),
                        style=TAB_CONTENT_HIDDEN_STYLE,
                    ),
                ],
                style={"position": "relative"},
            ),
        ],
    )


def _create_peps_tab_content() -> html.Div:
    """PEPsタブの内容を生成する"""
    return html.Div(
        [
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
        style={"paddingTop": "8px"},
    )


def _create_created_tab_content() -> html.Div:
    """Createdタブの内容（タイムライングラフ）を生成する"""
    return html.Div(
        [
            html.P(
                [
                    html.Strong("Color"),
                    " indicates the status of each PEP.",
                ],
                style={"fontSize": "12px", "color": "#666", "margin": "0"},
            ),
            html.P(
                "Shows when PEPs in this group were created.",
                style={"fontSize": "12px", "color": "#666", "marginBottom": "8px"},
            ),
            dcc.Graph(
                id="group-created-timeline-graph",
                figure=create_group_timeline_empty_figure(),
            ),
        ],
        style={"paddingTop": "8px"},
    )


def _create_group_pep_table() -> dag.AgGrid:
    """グループPEPテーブルを生成する（AG Grid版）"""
    # Status列の条件付きスタイルを生成
    status_style_conditions = _generate_status_style_conditions()

    # グループツールチップ情報を取得
    group_tooltip_info = get_all_group_tooltip_info()

    column_defs = [
        {
            "field": "pep",
            "headerName": "PEP",
            "width": 100,
            "pinned": "left",
            "cellRenderer": "markdown",
            "autoHeight": True,
            "tooltipField": "title",
        },
        {
            "field": "title",
            "headerName": "Title",
            "width": 250,
            "minWidth": 250,
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
            },
        },
        {
            "field": "created",
            "headerName": "Created",
            "width": 110,
        },
        {
            "field": "in_degree",
            "headerName": "In-degree ⓘ",
            "headerTooltip": "Number of PEPs within the selected group that cite this PEP.\nPEPs with a high in-degree are widely referenced within the group and often influential.",
            "width": 115,
            "type": "numericColumn",
        },
        {
            "field": "out_degree",
            "headerName": "Out-degree ⓘ",
            "headerTooltip": "Number of PEPs within the selected group cited by this PEP.\nPEPs with a high out-degree tend to reference many other PEPs within the group and may serve as integrative or coordinating proposals.",
            "width": 120,
            "type": "numericColumn",
        },
        {
            "field": "degree",
            "headerName": "Degree ⓘ",
            "headerTooltip": "Sum of in-degree and out-degree within the selected group.",
            "width": 105,
            "type": "numericColumn",
        },
        {
            "field": "pagerank",
            "headerName": "PageRank ⓘ",
            "headerTooltip": "Network-based importance score computed from the citation structure within the selected group.",
            "width": 115,
            "type": "rightAligned",
        },
        {
            "field": "cited_by_groups",
            "headerName": "Cited by Groups ⓘ",
            "headerTooltip": "Groups of PEPs that cite this PEP (excluding the current group). Click a badge to navigate to that group.",
            "width": 150,
            "cellRenderer": "GroupBadges",
            "cellRendererParams": {"groupInfo": group_tooltip_info},
            "autoHeight": True,
            "sortable": False,
        },
        {
            "field": "cites_groups",
            "headerName": "Cites Groups ⓘ",
            "headerTooltip": "Groups of PEPs that this PEP cites (excluding the current group). Click a badge to navigate to that group.",
            "width": 150,
            "cellRenderer": "GroupBadges",
            "cellRendererParams": {"groupInfo": group_tooltip_info},
            "autoHeight": True,
            "sortable": False,
        },
    ]

    default_col_def = {
        "sortable": True,
        "resizable": True,
    }

    return dag.AgGrid(
        id="group-pep-table",
        columnDefs=column_defs,
        rowData=[],
        defaultColDef=default_col_def,
        dashGridOptions={
            "tooltipShowDelay": 0,
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


def _generate_status_style_conditions() -> list[dict]:
    """
    AG Grid用のStatus列スタイル条件を生成する

    Returns:
        list[dict]: styleConditionsのリスト
    """
    conditions = []
    for status, bg_color in STATUS_COLOR_MAP.items():
        font_color = STATUS_FONT_COLOR_MAP.get(status, "#545454")
        conditions.append(
            {
                "condition": f"params.value === {json.dumps(status)}",
                "style": {
                    "backgroundColor": bg_color,
                    "color": font_color,
                    "textAlign": "center",
                },
            }
        )
    return conditions


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


def create_subgraph_placeholder_with_dummy() -> html.Div:
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
