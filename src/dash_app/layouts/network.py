"""Networkタブのレイアウト"""

import dash_cytoscape as cyto  # type: ignore[import-untyped]
from dash import dcc, html

from src.dash_app.components import (
    create_status_legend,
    build_cytoscape_elements,
    get_base_stylesheet,
    get_preset_layout_options,
    create_pep_table,
    create_network_initial_info_message,
)
from src.dash_app.utils.data_loader import load_metadata


def create_network_layout() -> html.Div:
    """
    Networkタブのレイアウトを生成する

    Returns:
        html.Div: Networkタブのレイアウト
    """
    # データ取得日付を取得
    metadata = load_metadata()
    fetched_at = metadata["fetched_at"]

    return html.Div(
        [
            # === 上部セクション: 入力欄 + PEP情報(プレースホルダー) ===
            _create_top_section(),
            # === Status凡例セクション ===
            _create_legend_section(),
            # === データ取得日付セクション ===
            _create_metadata_section(fetched_at),
            # === メインコンテンツ: グラフ + テーブル ===
            _create_main_content_section(),
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
                        id="network-pep-input",
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
                        id="network-pep-error-message",
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
                    "width": "200px",
                },
            ),
            # 右側: PEP情報表示
            html.Div(
                id="network-pep-info-display",
                children=create_network_initial_info_message(),
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
        [
            create_status_legend(),
        ],
        style={
            "marginBottom": "0px",
            "marginTop": "0px",
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


def _create_main_content_section() -> html.Div:
    """メインコンテンツ: グラフエリア + テーブルエリア"""
    return html.Div(
        [
            # 左側: ネットワークグラフ
            html.Div(
                [
                    _create_network_graph(),
                ],
                style={
                    "display": "inline-block",
                    "width": "60%",
                    "verticalAlign": "top",
                },
            ),
            # 右側: テーブルエリア
            html.Div(
                [
                    _create_tables_section(),
                ],
                style={
                    "display": "inline-block",
                    "width": "38%",
                    "verticalAlign": "top",
                    "marginLeft": "2%",
                },
            ),
        ],
    )


def _create_tables_section() -> html.Div:
    """テーブルセクション: 引用しているPEP + 引用されているPEP"""
    return html.Div(
        [
            # 上部: 選択中PEPを引用しているPEP
            html.Div(
                [
                    html.H4(
                        id="network-citing-peps-title",
                        children="PEP N is cited by...",
                        style={"marginBottom": "8px", "marginTop": "0"},
                    ),
                    create_pep_table("network-citing-peps-table"),
                ],
                style={
                    "marginBottom": "16px",
                },
            ),
            # 下部: 選択中PEPから引用されているPEP
            html.Div(
                [
                    html.H4(
                        id="network-cited-peps-title",
                        children="PEP N cites...",
                        style={"marginBottom": "8px", "marginTop": "0"},
                    ),
                    create_pep_table("network-cited-peps-table"),
                ],
            ),
        ],
    )


def _create_network_graph() -> cyto.Cytoscape:
    """
    ネットワークグラフコンポーネントを生成する

    全PEPの引用関係をグラフとして表示する。

    Returns:
        cyto.Cytoscape: Cytoscapeグラフコンポーネント
    """
    # グラフデータを構築
    elements = build_cytoscape_elements()

    return cyto.Cytoscape(
        id="network-graph",
        elements=elements,
        layout=get_preset_layout_options(),
        style={
            "width": "100%",
            "height": "600px",
            "border": "1px solid #ddd",
            "backgroundColor": "#fafafa",
        },
        stylesheet=get_base_stylesheet(),
    )
