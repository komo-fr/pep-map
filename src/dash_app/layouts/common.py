from dash import dcc


def create_tab_navigation():
    """
    タブナビゲーションを生成する

    Returns:
        dcc.Tabs: タブナビゲーションコンポーネント
    """
    return dcc.Tabs(
        id="main-tabs",
        value="timeline",
        children=[
            dcc.Tab(
                label="Timeline",
                value="timeline",
            ),
            dcc.Tab(
                label="Network",
                value="network",
                disabled=True,
            ),
            dcc.Tab(
                label="Community",
                value="community",
                disabled=True,
            ),
            dcc.Tab(
                label="History",
                value="history",
                disabled=True,
            ),
        ],
    )
