import dash_bootstrap_components as dbc
from dash import dcc, html


def create_tab_navigation():
    """
    タブナビゲーションを生成する

    Returns:
        html.Div: タブナビゲーションとツールチップを含むコンポーネント
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

    return html.Div(
        [
            dcc.Tabs(
                id="main-tabs",
                value="timeline",
                children=[
                    dcc.Tab(
                        label="Timeline",
                        value="timeline",
                        style=tab_style,
                        selected_style=tab_selected_style,
                        id="main-tab-timeline",
                    ),
                    dcc.Tab(
                        label="Network",
                        value="network",
                        style=tab_style,
                        selected_style=tab_selected_style,
                        id="main-tab-network",
                    ),
                    dcc.Tab(
                        label="Groups (beta)",
                        value="groups",
                        style=tab_style,
                        selected_style=tab_selected_style,
                        id="main-tab-groups",
                    ),
                    dcc.Tab(
                        label="PEP Metrics",
                        value="metrics",
                        style=tab_style,
                        selected_style=tab_selected_style,
                        id="main-tab-metrics",
                    ),
                    dcc.Tab(
                        label="Citation Changes",
                        value="citation_changes",
                        style=tab_style,
                        selected_style=tab_selected_style,
                        id="main-tab-citation-changes",
                    ),
                ],
                style={
                    "height": "auto",
                },
            ),
            # ツールチップ（dcc.Tabsの外側に配置）
            dbc.Tooltip(
                "Use this view to trace the history of PEPs related through citations.",
                target="main-tab-timeline",
                placement="bottom",
                style={"maxWidth": "300px"},
            ),
            dbc.Tooltip(
                "Use this view to see how PEPs are connected and which PEPs are central.",
                target="main-tab-network",
                placement="bottom",
                style={"maxWidth": "300px"},
            ),
            dbc.Tooltip(
                "Use this view to explore groups of related PEPs detected from citation relationships.",
                target="main-tab-groups",
                placement="bottom",
                style={"maxWidth": "300px"},
            ),
            dbc.Tooltip(
                "Use this view to compare PEPs by structural metrics such as degree and PageRank.",
                target="main-tab-metrics",
                placement="bottom",
                style={"maxWidth": "300px"},
            ),
            dbc.Tooltip(
                "Use this view to review changes in citation relationships detected by this system.",
                target="main-tab-citation-changes",
                placement="bottom",
                style={"maxWidth": "300px"},
            ),
        ]
    )
