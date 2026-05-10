"""グループ内PEPのCreatedタイムライン"""

import plotly.graph_objects as go

from src.dash_app.utils.constants import (
    DEFAULT_STATUS_COLOR,
    STATUS_COLOR_MAP,
    TIMELINE_MARGIN,
    TIMELINE_MARKER_SIZE,
    TIMELINE_TEXT_FONT_SIZE,
)
from src.dash_app.utils.data_loader import get_fetched_year, get_peps_by_group


def _get_group_timeline_xaxis_config() -> dict:
    """
    グループタイムラインのX軸設定を取得する

    Returns:
        dict: X軸の設定
    """
    x_range_min = "2000-01-01"
    fetched_year = get_fetched_year()
    x_range_max = f"{fetched_year}-12-31"

    return dict(
        title="Created Date",
        showgrid=True,
        gridwidth=1,
        type="date",
        range=[x_range_min, x_range_max],
        dtick="M12",
        tick0="2000-01-01",
        tickformat="%Y",
    )


def create_group_timeline_empty_figure() -> go.Figure:
    """
    空のグループタイムライングラフ（グループ未選択時）を生成する

    Returns:
        go.Figure: 空のPlotly figureオブジェクト
    """
    fig = go.Figure()

    fig.update_layout(
        xaxis=_get_group_timeline_xaxis_config(),
        yaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            range=[-0.5, 0.5],
        ),
        showlegend=False,
        margin=dict(**TIMELINE_MARGIN),
        annotations=[
            dict(
                text="Select a group to see PEP creation timeline",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16, color="#999"),
            )
        ],
    )

    return fig


def _compute_y_positions(dates: list) -> list[float]:
    """
    重なりを避けるためにY位置を計算する

    前のPEPとの日数差が閾値以下の場合、Y方向にオフセットする。

    Args:
        dates: ソート済みの日付リスト

    Returns:
        list[float]: 各PEPのY位置
    """
    if not dates:
        return []

    y_positions = []
    prev_date = None
    current_y = 0.0
    offset_step = 0.3
    threshold_days = 120

    for date in dates:
        if prev_date is not None:
            days_diff = (date - prev_date).days
            if days_diff < threshold_days:
                current_y += offset_step
                if current_y > 0.9:
                    current_y = -0.9
            else:
                current_y = 0.0
        y_positions.append(current_y)
        prev_date = date

    return y_positions


def create_group_timeline_figure(group_id: int) -> go.Figure:
    """
    グループ内PEPのCreatedタイムライングラフを生成する

    Args:
        group_id: グループID

    Returns:
        go.Figure: Plotly figureオブジェクト
    """
    if group_id < 0:
        return create_group_timeline_empty_figure()

    df = get_peps_by_group(group_id)

    if df.empty:
        return create_group_timeline_empty_figure()

    df = df.sort_values("created").reset_index(drop=True)

    dates = []
    colors = []
    texts = []
    hover_texts = []
    pep_numbers = []

    for _, row in df.iterrows():
        pep_number = row["PEP"]
        created = row["created"]
        status = row["status"]
        title = row["title"]

        dates.append(created)
        colors.append(STATUS_COLOR_MAP.get(status, DEFAULT_STATUS_COLOR))
        texts.append(str(pep_number))
        pep_numbers.append(pep_number)

        created_str = (
            created.strftime("%Y-%m-%d")
            if hasattr(created, "strftime")
            else str(created)
        )
        hover_text = (
            f"PEP {pep_number}<br>{title}<br>Status: {status}<br>Created: {created_str}"
        )
        hover_texts.append(hover_text)

    y_positions = _compute_y_positions(dates)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=y_positions,
            mode="markers+text",
            marker=dict(
                color=colors,
                size=TIMELINE_MARKER_SIZE,
                opacity=0.7,
            ),
            text=texts,
            textposition="top center",
            textfont=dict(
                size=TIMELINE_TEXT_FONT_SIZE,
                color="rgba(0, 0, 0, 0.7)",
            ),
            hovertext=hover_texts,
            hoverinfo="text",
            customdata=pep_numbers,
        )
    )

    fig.update_layout(
        xaxis=_get_group_timeline_xaxis_config(),
        yaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            range=[-1.2, 1.2],
        ),
        showlegend=False,
        margin=dict(**TIMELINE_MARGIN),
        hovermode="closest",
        height=350,
    )

    return fig
