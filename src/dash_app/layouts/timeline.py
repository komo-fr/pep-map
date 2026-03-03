"""Timelineタブのレイアウト"""

from dash import dcc, html

from src.dash_app.components import (
    create_empty_figure,
    create_initial_info_message,
    create_status_legend,
    create_pep_table,
    create_pep_table_description,
)
from src.dash_app.utils.constants import (
    PYTHON_2_LINE_COLOR,
    PYTHON_3_LINE_COLOR,
)
from src.dash_app.utils.data_loader import (
    get_python_releases_for_store,
    load_metadata,
)


def create_timeline_layout() -> html.Div:
    """
    Timelineタブのレイアウトを生成する

    Returns:
        html.Div: Timelineタブのレイアウト
    """
    # データ取得日付とチェック日付を取得
    metadata = load_metadata()
    fetched_at = metadata["fetched_at"]
    checked_at = metadata["checked_at"]

    return html.Div(
        [
            # === 上部セクション: 入力欄 + PEP情報 ===
            _create_top_section(),
            # === Status凡例セクション ===
            _create_legend_section(),
            # === Timeline説明セクション ===
            _create_timeline_description(),
            # === タイムライングラフセクション ===
            _create_graph_section(),
            # === データ取得日付セクション ===
            _create_metadata_section(fetched_at, checked_at),
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
                        id="pep-error-message",
                        style={
                            "color": "red",
                            "fontSize": "14px",
                            "marginTop": "4px",
                        },
                    ),
                    # How to Useリンク
                    html.A(
                        "How to Use",
                        href="https://github.com/komo-fr/pep-map/blob/production/README.md#timeline-tab",
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
                    "display": "inline-block",
                    "verticalAlign": "top",
                    "width": "200px",
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
    """Status凡例セクションとPythonリリース日表示チェックボックス"""
    return html.Div(
        [
            # Status凡例
            create_status_legend(),
            # Pythonリリース日表示チェックボックス
            _create_python_release_checkboxes(),
        ],
        style={
            "marginBottom": "0px",
            "marginTop": "0px",
        },
    )


def _create_timeline_description() -> html.Div:
    """Timelineタブの説明を生成する"""
    description = html.Div(
        [
            html.P(
                [
                    html.Strong("View PEP details:"),
                    html.Span(" ", style={"marginRight": "6px"}),
                    html.Span("Hover over a point."),
                    html.Span(" ", style={"marginRight": "16px"}),
                    html.Strong("Open official PEP page:"),
                    html.Span(" ", style={"marginRight": "6px"}),
                    html.Span("Click a point."),
                    html.Span(" ", style={"marginRight": "16px"}),
                    html.Strong("Zoom in:"),
                    html.Span(" ", style={"marginRight": "6px"}),
                    html.Span("Drag to select a range."),
                    html.Span(" ", style={"marginRight": "16px"}),
                    html.Strong("Reset the view:"),
                    html.Span(" ", style={"marginRight": "6px"}),
                    html.Span("Click the home icon in the top-right corner."),
                ],
                style={
                    "fontSize": "12px",
                    "color": "#666",
                    "margin": "0",
                },
            ),
        ],
    )

    return html.Div(description)


def _create_graph_section() -> html.Div:
    """タイムライングラフセクション"""
    # Pythonリリース日データを取得（アプリ起動時に1回のみ実行）
    python_releases_data = get_python_releases_for_store()

    return html.Div(
        [
            # Pythonリリース日データを保存するStore
            # データ構造:
            # {
            #     "python2": [{"version": "2.0", "release_date": "2000-10-16"}, ...],
            #     "python3": [{"version": "3.0", "release_date": "2008-12-03"}, ...]
            # }
            dcc.Store(id="python-releases-store", data=python_releases_data),
            # サーバーサイドコールバックが生成したベースfigureを保存する中間Store
            # クライアントサイドコールバックが縦線を追加する前のfigureデータを保持
            dcc.Store(id="timeline-figure-base"),
            dcc.Graph(
                id="timeline-graph",
                figure=create_empty_figure(),
                style={
                    "height": "350px",
                },
                config={
                    "displayModeBar": True,
                    "modeBarButtonsToRemove": [
                        "lasso2d",
                        "select2d",
                    ],
                },
            ),
            dcc.Location(id="pep-url", refresh=True),
        ],
        style={
            "marginBottom": "0",
        },
    )


def _create_metadata_section(fetched_at: str, checked_at: str) -> html.Div:
    """データ取得日付・チェック日付セクション"""
    return html.Div(
        [
            html.P(
                [
                    html.Strong("Data updated:"),
                    f" {fetched_at}",
                ],
                style={
                    "fontSize": "12px",
                    "color": "#666",
                    "marginBottom": "0px",
                    "marginTop": "0px",
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
                    "marginBottom": "0px",
                    "marginTop": "0px",
                },
            ),
        ],
        style={
            "marginBottom": "16px",
            "textAlign": "right",
        },
    )


def _create_tables_section() -> html.Div:
    """テーブルセクション: 引用しているPEP + 引用されているPEP"""
    return html.Div(
        [
            # 左側: 選択中PEPを引用しているPEP
            html.Div(
                [
                    html.H4(
                        id="citing-peps-title",
                        children="PEP N is cited by...",
                        style={"marginBottom": "8px"},
                    ),
                    create_pep_table_description(),
                    create_pep_table("citing-peps-table"),
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
                    html.H4(
                        id="cited-peps-title",
                        children="PEP N links to...",
                        style={"marginBottom": "8px"},
                    ),
                    create_pep_table_description(),
                    create_pep_table("cited-peps-table"),
                ],
                style={
                    "display": "inline-block",
                    "width": "48%",
                    "verticalAlign": "top",
                },
            ),
        ],
    )


def _create_python_release_checkboxes() -> html.Div:
    """
    Pythonリリース日表示切り替えチェックボックスを生成する

    Returns:
        html.Div: チェックボックスコンポーネント
    """
    return html.Div(
        [
            html.Div(
                [
                    dcc.Checklist(
                        id="python-release-checkboxes",
                        options=[
                            {
                                "label": html.Span(
                                    [
                                        html.Span(
                                            style={
                                                "display": "inline-block",
                                                "width": "20px",
                                                "height": "2px",
                                                "backgroundColor": PYTHON_2_LINE_COLOR,
                                                "marginRight": "6px",
                                                "verticalAlign": "middle",
                                            }
                                        ),
                                        "Show Python 2 release dates",
                                    ],
                                    style={"verticalAlign": "middle"},
                                ),
                                "value": "python2",
                            },
                            {
                                "label": html.Span(
                                    [
                                        html.Span(
                                            style={
                                                "display": "inline-block",
                                                "width": "20px",
                                                "height": "2px",
                                                "backgroundColor": PYTHON_3_LINE_COLOR,
                                                "marginRight": "6px",
                                                "verticalAlign": "middle",
                                            }
                                        ),
                                        "Show Python 3 release dates",
                                    ],
                                    style={"verticalAlign": "middle"},
                                ),
                                "value": "python3",
                            },
                        ],
                        value=[],  # デフォルトは非表示
                        inline=True,
                        style={
                            "display": "flex",
                            "gap": "24px",
                        },
                        inputStyle={
                            "marginRight": "6px",
                        },
                    ),
                ],
            ),
        ],
        style={
            "marginTop": "4px",
            "fontSize": "12px",
        },
    )
