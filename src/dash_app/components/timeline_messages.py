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
                "Enter a PEP number in the text box on the left (e.g., 8).",
                style={"marginBottom": "8px"},
            ),
            html.P(
                "The following information will be displayed in order of creation date:"
            ),
            html.Ul(
                [
                    html.Li("Which PEPs cite the selected PEP?"),
                    html.Li("Which PEPs does the selected PEP cite?"),
                ]
            ),
        ],
        style={
            "color": "#666",
        },
    )
