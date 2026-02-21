"""Networkタブのレイアウト"""

import dash_cytoscape as cyto
from dash import html

from src.dash_app.components import create_status_legend
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
            _create_top_section_placeholder(),
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


def _create_top_section_placeholder() -> html.Div:
    """上部セクション: PEP番号入力欄 + PEP情報表示エリア(プレースホルダー)"""
    return html.Div(
        [
            # 左側: PEP番号入力(プレースホルダー)
            html.Div(
                [
                    html.Label(
                        "PEP:",
                        style={
                            "fontWeight": "bold",
                            "marginRight": "8px",
                        },
                    ),
                    html.Span(
                        "(Coming in Phase 3)",
                        style={"color": "#999", "fontSize": "12px"},
                    ),
                ],
                style={
                    "display": "inline-block",
                    "verticalAlign": "top",
                    "width": "200px",
                },
            ),
            # 右側: PEP情報表示(プレースホルダー)
            html.Div(
                id="network-pep-info-display",
                children=html.P(
                    "Enter a PEP number to see details.",
                    style={"color": "#666", "fontStyle": "italic"},
                ),
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
            # 右側: テーブルエリア(プレースホルダー)
            html.Div(
                [
                    html.P(
                        "Tables will appear here (Phase 5)",
                        style={"color": "#999", "fontStyle": "italic"},
                    ),
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


def _create_network_graph() -> cyto.Cytoscape:
    """
    空のネットワークグラフコンポーネントを生成する

    Returns:
        cyto.Cytoscape: Cytoscapeグラフコンポーネント
    """
    return cyto.Cytoscape(
        id="network-graph",
        elements=[],  # フェーズ2でデータを追加
        layout={"name": "cose"},
        style={
            "width": "100%",
            "height": "600px",
            "border": "1px solid #ddd",
            "backgroundColor": "#fafafa",
        },
        stylesheet=_get_base_stylesheet(),
    )


def _get_base_stylesheet() -> list:
    """
    Cytoscapeグラフの基本スタイルシートを取得する

    Returns:
        list: スタイルシート定義のリスト
    """
    return [
        # ノード基本スタイル
        {
            "selector": "node",
            "style": {
                "label": "data(label)",
                "width": 20,
                "height": 20,
                "font-size": "10px",
                "text-valign": "top",
                "text-halign": "center",
                "background-color": "#666",
            },
        },
        # エッジ基本スタイル
        {
            "selector": "edge",
            "style": {
                "width": 1,
                "line-color": "#ccc",
                "target-arrow-color": "#ccc",
                "target-arrow-shape": "triangle",
                "curve-style": "bezier",
            },
        },
    ]
