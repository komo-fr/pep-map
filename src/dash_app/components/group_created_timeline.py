"""グループ内PEPのCreatedタイムライン"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

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

    上段: 散布図（PEP作成日）
    下段: 積み上げヒストグラム（年ごとのStatus別カウント）

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

    # 散布図用データ
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

    # ヒストグラム用データ（年ごとのStatus別カウント）
    df["year"] = df["created"].dt.year
    year_status_counts = df.groupby(["year", "status"]).size().unstack(fill_value=0)

    # subplotsを作成（上: ヒストグラム、下: 散布図）
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.35, 0.65],
    )

    # 上段: 積み上げヒストグラム（Statusごと）
    years = year_status_counts.index.tolist()
    year_dates = [f"{y}-07-01" for y in years]

    for status in year_status_counts.columns:
        counts = year_status_counts[status].tolist()
        color = STATUS_COLOR_MAP.get(status, DEFAULT_STATUS_COLOR)
        fig.add_trace(
            go.Bar(
                x=year_dates,
                y=counts,
                name=status,
                marker_color=color,
                opacity=0.8,
                hovertemplate=f"{status}: %{{y}}<extra></extra>",
            ),
            row=1,
            col=1,
        )

    # 下段: 散布図
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
            showlegend=False,
        ),
        row=2,
        col=1,
    )

    # X軸設定
    x_range_min = "2000-01-01"
    fetched_year = get_fetched_year()
    x_range_max = f"{fetched_year}-12-31"

    # レイアウト更新
    fig.update_layout(
        barmode="stack",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="left",
            x=0,
            font=dict(size=10),
        ),
        margin=dict(l=40, r=40, t=80, b=80),
        hovermode="closest",
        height=520,
        title=dict(
            text="Created Date",
            x=0.5,
            y=0.99,
            xanchor="center",
            font=dict(size=14),
        ),
    )

    # 上段Y軸（ヒストグラム）
    fig.update_yaxes(
        title_text="Count",
        showgrid=True,
        row=1,
        col=1,
    )

    # 下段Y軸（散布図）
    fig.update_yaxes(
        showticklabels=False,
        showgrid=False,
        zeroline=False,
        range=[-1.2, 1.2],
        row=2,
        col=1,
    )

    # X軸設定（上段 - 上側に表示）
    fig.update_xaxes(
        type="date",
        range=[x_range_min, x_range_max],
        dtick="M12",
        tick0="2000-01-01",
        tickformat="%Y",
        showgrid=True,
        showticklabels=True,
        side="top",
        row=1,
        col=1,
    )

    fig.update_xaxes(
        type="date",
        range=[x_range_min, x_range_max],
        dtick="M12",
        tick0="2000-01-01",
        tickformat="%Y",
        showgrid=True,
        row=2,
        col=1,
    )

    return fig
