"""Status凡例コンポーネント"""

from dash import html

from src.dash_app.utils.constants import STATUS_COLOR_MAP


def create_status_legend() -> html.Div:
    """
    Status凡例コンポーネントを生成する

    各Statusの色付き四角とテキストを横並びで表示する。

    Returns:
        html.Div: Status凡例コンポーネント
    """
    legend_items = []

    for status, color in STATUS_COLOR_MAP.items():
        # 各Statusのアイテム: 色付き四角 + テキスト
        item = html.Span(
            [
                # 色付き四角
                html.Span(
                    style={
                        "display": "inline-block",
                        "width": "12px",
                        "height": "12px",
                        "backgroundColor": color,
                        "marginRight": "4px",
                        "verticalAlign": "middle",
                    }
                ),
                # Statusテキスト
                html.Span(
                    status,
                    style={
                        "verticalAlign": "middle",
                        "fontSize": "12px",
                    },
                ),
            ],
            style={
                "display": "inline-block",
                "marginRight": "16px",
                "marginBottom": "4px",
            },
        )
        legend_items.append(item)

    return html.Div(
        [
            html.P(
                "Color means the status of PEPs",
                style={
                    "fontSize": "12px",
                    "color": "#666",
                    "marginBottom": "0px",
                },
            ),
            html.Div(legend_items),
        ],
        style={
            "padding": "0",
            # "backgroundColor": "yellow",
        },
    )
