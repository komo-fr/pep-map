"""PEP情報表示の共通コンポーネント"""

import pandas as pd
from dash import html

from src.dash_app.utils.constants import DEFAULT_STATUS_COLOR, STATUS_COLOR_MAP
from src.dash_app.utils.data_loader import generate_pep_url


def parse_pep_number(value):
    """
    PEP番号の入力値を整数に変換する

    Args:
        value: 入力値（str, int, None）

    Returns:
        int | None: 整数に変換されたPEP番号、または None
    """
    if value is None or value == "":
        return None

    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def format_python_version(value) -> str:
    """
    Python-Versionの表示文字列を返す（未設定の場合は'-'）

    Args:
        value: Python-Versionの値（文字列、数値、またはNaN）

    Returns:
        str: フォーマットされた表示文字列（未設定の場合は"-"）
    """
    if pd.notna(value) and str(value).strip():
        return str(value)
    return "-"


def create_status_badge(status: str) -> html.Span:
    """
    Statusバッジ（色付き四角 + テキスト）を生成する

    Args:
        status: PEPのステータス

    Returns:
        html.Span: 色付きバッジコンポーネント
    """
    bg_color = STATUS_COLOR_MAP.get(status, DEFAULT_STATUS_COLOR)

    return html.Span(
        [
            # 色付き四角
            html.Span(
                style={
                    "display": "inline-block",
                    "width": "12px",
                    "height": "12px",
                    "backgroundColor": bg_color,
                    "marginRight": "4px",
                    "verticalAlign": "middle",
                    "border": "1px solid #ccc",
                }
            ),
            # Statusテキスト
            html.Span(
                status,
                style={
                    "verticalAlign": "middle",
                    "fontWeight": "normal",
                },
            ),
        ],
        style={
            "display": "inline",
            "marginLeft": "0px",
        },
    )


def create_network_initial_info_message() -> html.Div:
    """
    Network タブの初期状態のPEP情報表示（説明文）を生成する

    Returns:
        html.Div: 初期説明文のコンポーネント
    """
    return html.Div(
        [
            html.P(
                "Enter a PEP number in the text box on the left (e.g., 8).",
                style={"marginBottom": "8px"},
            ),
            html.P("The selected PEP will be highlighted in the network graph."),
        ],
        style={
            "color": "#666",
        },
    )


def create_group_initial_info_message() -> html.Div:
    """
    Group タブの初期状態のPEP情報表示（説明文）を生成する

    Returns:
        html.Div: 初期説明文のコンポーネント
    """
    return html.Div(
        [
            html.P(
                "Select a group from the dropdown on the left.",
                style={"marginBottom": "4px"},
            ),
            html.P(
                "PEPs belonging to the selected group will be highlighted in the network graph.",
                style={"marginBottom": "8px"},
            ),
            html.P(
                "Groups are detected automatically from the citation network using a community detection algorithm.",
                style={"marginBottom": "0", "fontSize": "12px"},
            ),
        ],
        style={
            "color": "#666",
        },
    )


def create_pep_info_display(pep_data) -> html.Div:
    """
    PEP情報表示コンポーネントを生成する

    Args:
        pep_data: PEPのメタデータ（pd.Series）

    Returns:
        html.Div: PEP情報のコンポーネント
    """
    pep_number = pep_data["pep_number"]
    title = pep_data["title"]
    status = pep_data["status"]
    pep_type = pep_data["type"]
    created = pep_data["created"]
    python_version = pep_data["python_version"]

    # 日付をフォーマット（YYYY-MM-DD）
    created_str = created.strftime("%Y-%m-%d")

    # PEPページへのURL
    pep_url = generate_pep_url(pep_number)

    # Python-Versionの表示文字列を決定
    python_version_str = format_python_version(python_version)

    # 2行目の情報要素を構築
    info_elements = [
        html.Span("Created: "),
        created_str,
        html.Span("Python-Version: ", style={"marginLeft": "20px"}),
        python_version_str,
        html.Span("Type: ", style={"marginLeft": "20px"}),
        pep_type,
        html.Span("Status: ", style={"marginLeft": "20px"}),
        create_status_badge(status),
    ]

    return html.Div(
        [
            # 1行目: PEP番号（リンク付き）とタイトル
            html.H3(
                [
                    html.A(
                        f"PEP {pep_number}",
                        href=pep_url,
                        target="_blank",
                        style={
                            "color": "#0066cc",
                            "textDecoration": "underline",
                        },
                    ),
                    f": {title}",
                ],
                style={
                    "marginBottom": "4px",
                    "marginTop": "0",
                },
            ),
            # 2行目: Created、Python-Version (あれば)、Type、Status
            html.P(
                info_elements,
                style={
                    "marginBottom": "0",
                    "color": "#666",
                    "fontSize": "14px",
                },
            ),
        ]
    )
