"""PEP Map - Timeline機能"""

import os
import logging

from dash import Dash, html, Input, Output
from dash_bootstrap_components import themes

from src.dash_app.layouts.citation_changes_tab import create_citation_changes_tab_layout
from src.dash_app.layouts.group_tab import create_group_tab_layout
from src.dash_app.callbacks.group_callbacks import (
    register_group_callbacks,
    preload_group_selection_outputs,
)
from src.dash_app.components.header import create_header
from src.dash_app.components.network_graph import build_cytoscape_elements
from src.dash_app.components.subgraph_network_graph import preload_all_subgraph_elements
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
    load_metrics_styles,
    load_citation_changes,
    load_group_data,
    load_group_to_group_network,
)


logger = logging.getLogger(__name__)

# Dashアプリの初期化
app = Dash(
    __name__,
    suppress_callback_exceptions=True,  # 動的コンテンツのためコールバック例外を抑制
    external_stylesheets=[themes.BOOTSTRAP],
)
app.title = "PEP Map | Visualization of Citation Relationships in PEPs"
server = app.server  # for gunicorn

# データのプリロード（Renderのヘルスチェックに間に合うよう、起動時に読み込む）
logger.info("Starting data preload...")
load_peps_metadata()
load_citations()
load_metadata()
load_python_releases()
load_node_metrics()  # メトリクスデータを読み込む
load_metrics_styles()  # メトリクステーブルのスタイル条件を事前計算
build_cytoscape_elements()  # Networkグラフの座標計算（2秒程度）
load_citation_changes()  # 引用変更履歴データを読み込む
load_group_data()  # グループデータを読み込む
load_group_to_group_network()  # グループ間ネットワークを読み込む
preload_all_subgraph_elements()  # 全グループのサブグラフ要素を事前計算
preload_group_selection_outputs()  # 全グループの選択時出力を事前計算
logger.info("Data preload complete.")

# 全タブのレイアウトを起動時に生成（常時マウント方式）
# タブ切り替え時はCSSのdisplayで表示/非表示を切り替えるため、
# 状態（ズーム・パン、選択など）が保持される
logger.info("Building tab layouts...")
_timeline_layout = create_timeline_layout()
_network_layout = create_network_layout()
_groups_layout = create_group_tab_layout()
_metrics_layout = create_metrics_tab_layout()
_citation_changes_layout = create_citation_changes_tab_layout()
logger.info("Tab layouts complete.")

# タブコンテンツのスタイル定義
# 初期状態では全タブを表示してCytoscapeを正しく初期化し、
# clientside callbackで適切なタブ以外を非表示に切り替える
_TAB_INITIAL_STYLE = {"display": "block"}

# アプリレイアウトの定義
# 全タブのコンテンツを含み、CSSで表示切り替え
app.layout = html.Div(
    [
        # ヘッダー
        create_header(),
        # タブナビゲーション
        create_tab_navigation(),
        # タブコンテンツ（全タブを常時マウント、displayで表示切り替え）
        # 初期状態では全タブを表示してCytoscapeを正しく初期化
        html.Div(
            [
                html.Div(
                    id="tab-content-timeline",
                    children=_timeline_layout,
                    style=_TAB_INITIAL_STYLE,
                ),
                html.Div(
                    id="tab-content-network",
                    children=_network_layout,
                    style=_TAB_INITIAL_STYLE,
                ),
                html.Div(
                    id="tab-content-groups",
                    children=_groups_layout,
                    style=_TAB_INITIAL_STYLE,
                ),
                html.Div(
                    id="tab-content-metrics",
                    children=_metrics_layout,
                    style=_TAB_INITIAL_STYLE,
                ),
                html.Div(
                    id="tab-content-citation_changes",
                    children=_citation_changes_layout,
                    style=_TAB_INITIAL_STYLE,
                ),
            ],
        ),
    ]
)


# タブ切り替えコールバック（クライアントサイド）
# 初期ロード時およびタブ切り替え時にdisplayスタイルを設定
# 初期状態で全タブがdisplay:blockのため、Cytoscapeは正しいサイズで初期化される
app.clientside_callback(
    """
    function(activeTab) {
        const tabs = ['timeline', 'network', 'groups', 'metrics', 'citation_changes'];
        const styles = tabs.map(function(tab) {
            return {display: tab === activeTab ? 'block' : 'none'};
        });
        return styles;
    }
    """,
    Output("tab-content-timeline", "style"),
    Output("tab-content-network", "style"),
    Output("tab-content-groups", "style"),
    Output("tab-content-metrics", "style"),
    Output("tab-content-citation_changes", "style"),
    Input("main-tabs", "value"),
)


# Timelineコールバックを登録
register_timeline_callbacks(app)

# Networkコールバックを登録
register_network_callbacks(app)

# Metricsコールバックを登録
register_metrics_callbacks(app)

# Groupコールバックを登録
register_group_callbacks(app)

if __name__ == "__main__":
    # debugモードはセキュリティ上、明示的に有効化された場合のみTrue
    debug = os.environ.get("DEBUG", "").lower() in ("true", "1")
    app.run(debug=debug)
