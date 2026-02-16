"""Timelineタブ用の共通Figureコンポーネント"""

import plotly.graph_objects as go

from src.dash_app.utils.constants import (
    TIMELINE_ANNOTATION_FONT_COLOR,
    TIMELINE_ANNOTATION_FONT_SIZE,
    TIMELINE_MARGIN,
    TIMELINE_Y_RANGE,
    TIMELINE_Y_TICKVALS,
)


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
            tickvals=TIMELINE_Y_TICKVALS,
            ticktext=["", "", ""],
            range=list(TIMELINE_Y_RANGE),
            showgrid=False,
        ),
        showlegend=False,
        margin=dict(**TIMELINE_MARGIN),
        annotations=[
            dict(
                text="Enter a PEP number to see the timeline",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(
                    size=TIMELINE_ANNOTATION_FONT_SIZE,
                    color=TIMELINE_ANNOTATION_FONT_COLOR,
                ),
            )
        ],
    )

    return fig
