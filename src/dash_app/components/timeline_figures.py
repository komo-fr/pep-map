"""Timelineタブ用の共通Figureコンポーネント"""

import plotly.graph_objects as go

from src.dash_app.utils.constants import (
    TIMELINE_ANNOTATION_FONT_COLOR,
    TIMELINE_ANNOTATION_FONT_SIZE,
    TIMELINE_MARGIN,
    TIMELINE_Y_RANGE,
    TIMELINE_Y_TICKVALS,
)
from src.dash_app.utils.data_loader import get_fetched_year


def _get_xaxis_config() -> dict:
    """
    X軸の共通設定を取得する

    Returns:
        dict: X軸の設定
    """
    x_range_min = "2000-01-01"
    fetched_year = get_fetched_year()
    x_range_max = f"{fetched_year}-12-31"

    return dict(
        title="Created Date",
        showgrid=True,
        gridwidth=2,
        type="date",
        range=[x_range_min, x_range_max],
        dtick="M12",
        tick0="2000-01-01",
        tickformat="%Y",
        minor=dict(
            ticks="inside",
            showgrid=True,
            gridwidth=2,
            gridcolor="#FFFFFF",
            griddash="dot",
        ),
    )


def _get_guideline_shapes() -> list[dict]:
    """
    タイムライン散布図のガイドライン（横線）を取得する

    Returns:
        list[dict]: shapesの設定リスト
    """
    return [
        # y=1: 黒いドット
        dict(
            type="line",
            xref="paper",
            yref="y",
            x0=0,
            x1=1,
            y0=1,
            y1=1,
            line=dict(color="gray", width=1, dash="dot"),
            layer="below",
        ),
        # y=0: ピンクの太い実線
        dict(
            type="line",
            xref="paper",
            yref="y",
            x0=0,
            x1=1,
            y0=0,
            y1=0,
            line=dict(color="#FF69B4", width=5),
            layer="below",
        ),
        # y=-1: 黒いドット
        dict(
            type="line",
            xref="paper",
            yref="y",
            x0=0,
            x1=1,
            y0=-1,
            y1=-1,
            line=dict(color="gray", width=1, dash="dot"),
            layer="below",
        ),
    ]


def create_empty_figure() -> go.Figure:
    """
    空のタイムライングラフ（初期状態）を生成する

    Returns:
        go.Figure: 空のPlotly figureオブジェクト
    """
    fig = go.Figure()

    fig.update_layout(
        xaxis=_get_xaxis_config(),
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
                y=0.7,
                showarrow=False,
                font=dict(
                    size=TIMELINE_ANNOTATION_FONT_SIZE,
                    color=TIMELINE_ANNOTATION_FONT_COLOR,
                ),
            )
        ],
        shapes=_get_guideline_shapes(),
    )

    return fig
