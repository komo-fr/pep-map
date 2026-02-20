"""ヘッダーコンポーネント"""

from dash import html

from src.dash_app.utils.constants import PYTHON_2_LINE_COLOR, PYTHON_3_LINE_COLOR

HEADER_FONT_COLOR = "#FAFAFA"
HEADER_FONT_FAMILY = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
GITHUB_URL = "https://github.com/komo-fr/pep-map"


def create_header() -> html.Header:
    """
    アプリ上部に表示するヘッダーコンポーネントを作成する。

    Returns:
        html.Header: ヘッダー要素
    """
    return html.Header(
        html.Div(
            [
                # 左端: タイトル + サブタイトルのグループ
                html.Div(
                    [
                        html.Span(
                            "PEP Map",
                            style={
                                "color": HEADER_FONT_COLOR,
                                "fontFamily": HEADER_FONT_FAMILY,
                                "fontSize": "20px",
                                "fontWeight": "700",
                                "marginRight": "12px",
                            },
                        ),
                        html.Span(
                            "Visualization of Citation Relationships in PEPs",
                            style={
                                "color": PYTHON_2_LINE_COLOR,
                                "fontFamily": HEADER_FONT_FAMILY,
                                "fontSize": "13px",
                            },
                        ),
                    ],
                    style={
                        "display": "flex",
                        "alignItems": "center",
                    },
                ),
                # 右端: GitHubリンク
                html.A(
                    "GitHub",
                    href=GITHUB_URL,
                    target="_blank",
                    rel="noopener noreferrer",
                    style={
                        "color": HEADER_FONT_COLOR,
                        "textDecoration": "underline",
                        "fontFamily": HEADER_FONT_FAMILY,
                        "fontSize": "15px",
                    },
                ),
            ],
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "padding": "10px 20px",
            },
        ),
        style={
            "backgroundColor": PYTHON_3_LINE_COLOR,
        },
    )
