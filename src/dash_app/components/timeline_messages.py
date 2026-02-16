"""Timelineタブ用の共通メッセージコンポーネント"""

from dash import html


def create_initial_info_message() -> html.Div:
    """
    初期状態のPEP情報表示（説明文）を生成する

    Returns:
        html.Div: 初期説明文のコンポーネント
    """
    return html.Div(
        [
            html.P(
                "Enter a PEP number in the left text box (e.g. 8).",
                style={"marginBottom": "8px"},
            ),
            html.P("You can then see the following information:"),
            html.Ul(
                [
                    html.Li("Which PEPs link to that PEP"),
                    html.Li("Which PEPs are linked from that PEP?"),
                ]
            ),
        ],
        style={
            "color": "#666",
        },
    )
