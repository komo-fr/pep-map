"""ヘッダーコンポーネント"""

from dash import html

HEADER_BG_COLOR = "#2E6495"
HEADER_FONT_COLOR = "#FAFAFA"
HEADER_SUBTITLE_COLOR = "#DDAD3E"
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
                                "color": HEADER_SUBTITLE_COLOR,
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
                # 右端:  + セパレーター + ガイド + Changelog + GitHubリンク
                html.Div(
                    [
                        html.A(
                            "Guide",
                            href="https://github.com/komo-fr/pep-map/blob/production/README.md",
                            target="_blank",
                            rel="noopener noreferrer",
                            style={
                                "color": HEADER_FONT_COLOR,
                                "textDecoration": "underline",
                                "fontFamily": HEADER_FONT_FAMILY,
                                "fontSize": "15px",
                            },
                        ),
                        html.Span(
                            "|",
                            style={
                                "color": HEADER_FONT_COLOR,
                                "fontFamily": HEADER_FONT_FAMILY,
                                "fontSize": "15px",
                                "margin": "0 8px",
                            },
                        ),
                        html.A(
                            "Changelog",
                            href="https://github.com/komo-fr/pep-map/blob/production/CHANGELOG.md",
                            target="_blank",
                            rel="noopener noreferrer",
                            style={
                                "color": HEADER_FONT_COLOR,
                                "textDecoration": "underline",
                                "fontFamily": HEADER_FONT_FAMILY,
                                "fontSize": "15px",
                            },
                        ),
                        html.Span(
                            "|",
                            style={
                                "color": HEADER_FONT_COLOR,
                                "fontFamily": HEADER_FONT_FAMILY,
                                "fontSize": "15px",
                                "margin": "0 8px",
                            },
                        ),
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
                        "alignItems": "center",
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
            "backgroundColor": HEADER_BG_COLOR,
        },
    )
