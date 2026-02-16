"""Timelineタブ用の共通Figureコンポーネント"""

import plotly.graph_objects as go


def create_empty_figure() -> go.Figure:
    """
    空のタイムライングラフ（初期状態）を生成する

    Returns:
        go.Figure: 空のPlotly figureオブジェクト
    """
    fig = go.Figure()

    fig.update_layout(
        xaxis=dict(
            title="Created Date",
            showgrid=True,
        ),
        yaxis=dict(
            tickvals=[-1, 0, 1],
            ticktext=["", "", ""],
            range=[-1.5, 1.5],
            showgrid=False,
        ),
        showlegend=False,
        margin=dict(l=40, r=40, t=40, b=40),
        annotations=[
            dict(
                text="Enter a PEP number to see the timeline",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=14, color="#999"),
            )
        ],
    )

    return fig
