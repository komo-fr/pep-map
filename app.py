"""PEP Map - Timeline機能"""

from dash import Dash, html, Input, Output
from dash_bootstrap_components import themes

from src.dash_app.components.header import create_header
from src.dash_app.layouts.common import create_tab_navigation
from src.dash_app.layouts.timeline import create_timeline_layout
from src.dash_app.callbacks.timeline_callbacks import register_timeline_callbacks

# Dashアプリの初期化
app = Dash(
    __name__,
    suppress_callback_exceptions=True,  # 動的コンテンツのためコールバック例外を抑制
    external_stylesheets=[themes.BOOTSTRAP],
)

# アプリレイアウトの定義
app.layout = html.Div(
    [
        # ヘッダー
        create_header(),
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
                html.H2("Network - Coming Soon"),
                html.P("Interactive network graph visualization is under development."),
            ],
            style={"padding": "20px", "textAlign": "center"},
        )
    else:
        return html.Div(
            [
                html.P("Unknown tab."),
            ]
        )


# Timelineコールバックを登録
register_timeline_callbacks(app)


if __name__ == "__main__":
    app.run(debug=True)
