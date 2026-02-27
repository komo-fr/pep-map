from dash import dcc


def create_tab_navigation():
    """
    タブナビゲーションを生成する

    Returns:
        dcc.Tabs: タブナビゲーションコンポーネント
    """
    # タブ共通スタイル
    tab_style = {
        "padding": "8px 16px",
        "fontWeight": "500",
    }
    tab_selected_style = {
        "padding": "8px 16px",
        "fontWeight": "bold",
        "borderTop": "10px solid #DDAD3E",
    }

    return dcc.Tabs(
        id="main-tabs",
        value="timeline",
        children=[
            dcc.Tab(
                label="Timeline",
                value="timeline",
                style=tab_style,
                selected_style=tab_selected_style,
            ),
            dcc.Tab(
                label="Network",
                value="network",
                style=tab_style,
                selected_style=tab_selected_style,
            ),
            dcc.Tab(
                label="PEP Metrics",
                value="metrics",
                style=tab_style,
                selected_style=tab_selected_style,
            ),
        ],
        style={
            "height": "auto",
        },
    )
