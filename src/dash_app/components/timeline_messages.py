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
                "Let's enter the PEP number in the left text box.",
                style={"marginBottom": "8px"},
            ),
            html.P("Then you can see the following information."),
            html.Ul(
                [
                    html.Li("Which PEPs do link that PEP?"),
                    html.Li("Which PEPs are linked from that PEP?"),
                ]
            ),
        ],
        style={
            "color": "#666",
        },
    )
