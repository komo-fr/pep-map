"""PEP Map - Timeline機能"""

from dash import Dash, html, Input, Output

from src.dash_app.layouts.common import create_tab_navigation
from src.dash_app.layouts.timeline import create_timeline_layout

# Dashアプリの初期化
app = Dash(
    __name__,
    suppress_callback_exceptions=True,  # 動的コンテンツのためコールバック例外を抑制
)

# アプリレイアウトの定義
app.layout = html.Div(
    [
        # タブナビゲーション
        create_tab_navigation(),
        # タブコンテンツ表示エリア
        html.Div(id="tab-content"),
    ]
)


@app.callback(Output("tab-content", "children"), Input("main-tabs", "value"))
def render_tab_content(active_tab):
    """
    選択されたタブに応じてコンテンツを表示する

    Args:
        active_tab: アクティブなタブの値

    Returns:
        html.Div: タブコンテンツ
    """
    if active_tab == "timeline":
        return create_timeline_layout()
    elif active_tab == "network":
        return html.Div(
            [
                html.H2("Network"),
                html.P("Network機能は将来実装予定です。"),
            ]
        )
    elif active_tab == "community":
        return html.Div(
            [
                html.H2("Community"),
                html.P("Community機能は将来実装予定です。"),
            ]
        )
    elif active_tab == "history":
        return html.Div(
            [
                html.H2("History"),
                html.P("History機能は将来実装予定です。"),
            ]
        )
    else:
        return html.Div(
            [
                html.P("不明なタブです。"),
            ]
        )


if __name__ == "__main__":
    app.run(debug=True)
