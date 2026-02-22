"""PEP情報表示の共通コンポーネント"""

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

    # 日付をフォーマット（YYYY-MM-DD）
    created_str = created.strftime("%Y-%m-%d")

    # PEPページへのURL
    pep_url = generate_pep_url(pep_number)

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
            # 2行目: Created、Type、Status
            html.P(
                [
                    html.Span("Created: "),
                    created_str,
                    html.Span("Type: ", style={"marginLeft": "20px"}),
                    pep_type,
                    html.Span("Status: ", style={"marginLeft": "20px"}),
                    create_status_badge(status),
                ],
                style={
                    "marginBottom": "0",
                    "color": "#666",
                    "fontSize": "14px",
                },
            ),
        ]
    )
