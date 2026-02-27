"""PEP Map - Timeline機能"""

import os
import logging

from dash import Dash, html, Input, Output
from dash_bootstrap_components import themes

from src.dash_app.components.header import create_header
from src.dash_app.components.network_graph import build_cytoscape_elements
from src.dash_app.layouts.common import create_tab_navigation
from src.dash_app.layouts.timeline import create_timeline_layout
from src.dash_app.layouts.network import create_network_layout
from src.dash_app.layouts.metrics_tab import create_metrics_tab_layout
from src.dash_app.callbacks.timeline_callbacks import register_timeline_callbacks
from src.dash_app.callbacks.network_callbacks import register_network_callbacks
from src.dash_app.callbacks.metrics_callbacks import register_metrics_callbacks
from src.dash_app.utils.data_loader import (
    load_peps_metadata,
    load_citations,
    load_metadata,
    load_python_releases,
    load_node_metrics,
)


logger = logging.getLogger(__name__)

# Dashアプリの初期化
app = Dash(
    __name__,
    suppress_callback_exceptions=True,  # 動的コンテンツのためコールバック例外を抑制
    external_stylesheets=[themes.BOOTSTRAP],
)
server = app.server  # for gunicorn

# データのプリロード（Renderのヘルスチェックに間に合うよう、起動時に読み込む）
logger.info("Starting data preload...")
load_peps_metadata()
load_citations()
load_metadata()
load_python_releases()
load_node_metrics()  # メトリクスデータを読み込む
build_cytoscape_elements()  # Networkグラフの座標計算（2秒程度）
logger.info("Data preload complete.")

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
        return create_network_layout()
    elif active_tab == "metrics":
        return create_metrics_tab_layout()
    else:
        return html.Div(
            [
                html.P("Unknown tab."),
            ]
        )


# Timelineコールバックを登録
register_timeline_callbacks(app)

# Networkコールバックを登録
register_network_callbacks(app)

# Metricsコールバックを登録
register_metrics_callbacks(app)


if __name__ == "__main__":
    # debugモードはセキュリティ上、明示的に有効化された場合のみTrue
    debug = os.environ.get("DEBUG", "").lower() in ("true", "1")
    app.run(debug=debug)
