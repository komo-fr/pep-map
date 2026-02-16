"""Timelineタブのコールバック関数"""

import plotly.graph_objects as go
from dash import Input, Output, html

from src.dash_app.components.timeline_messages import create_initial_info_message
from src.dash_app.utils.constants import DEFAULT_STATUS_COLOR, STATUS_COLOR_MAP
from src.dash_app.utils.data_loader import (
    generate_pep_url,
    get_cited_peps,
    get_citing_peps,
    get_pep_by_number,
)


def register_timeline_callbacks(app):
    """
    Timelineタブのコールバックを登録する

    Args:
        app: Dashアプリケーションインスタンス
    """

    @app.callback(
        Output("pep-info-display", "children"),
        Output("pep-error-message", "children"),
        Input("pep-input", "value"),
    )
    def update_pep_info(pep_number):
        """
        PEP番号入力に連動してPEP情報を更新する

        Args:
            pep_number: 入力されたPEP番号（int または None）

        Returns:
            tuple: (PEP情報表示コンテンツ, エラーメッセージ)
        """
        # 入力が空/Noneの場合: 初期説明文を表示
        if pep_number is None:
            return create_initial_info_message(), ""

        # PEPの存在確認
        pep_data = get_pep_by_number(pep_number)

        # 存在しない場合: エラーメッセージを表示
        if pep_data is None:
            error_message = f"Not Found: PEP {pep_number}"
            return create_initial_info_message(), error_message

        # 存在する場合: PEP情報を表示
        return _create_pep_info_display(pep_data), ""

    # === テーブル更新コールバック（新規追加） ===
    @app.callback(
        Output("citing-peps-table", "data"),
        Output("cited-peps-table", "data"),
        Input("pep-input", "value"),
    )
    def update_tables(pep_number):
        """
        PEP番号入力に連動してテーブルデータを更新する

        Args:
            pep_number: 入力されたPEP番号（int または None）

        Returns:
            tuple: (citing_tableのデータ, cited_tableのデータ)
        """
        # 入力が空/Noneまたは存在しないPEPの場合: 空のテーブル
        if pep_number is None:
            return [], []

        pep_data = get_pep_by_number(pep_number)
        if pep_data is None:
            return [], []

        # このPEPを引用しているPEPを取得
        citing_peps_df = get_citing_peps(pep_number)
        citing_table_data = _convert_df_to_table_data(citing_peps_df)

        # このPEPに引用されているPEPを取得
        cited_peps_df = get_cited_peps(pep_number)
        cited_table_data = _convert_df_to_table_data(cited_peps_df)

        return citing_table_data, cited_table_data

    # === グラフ更新コールバック（新規追加） ===
    @app.callback(
        Output("timeline-graph", "figure"),
        Input("pep-input", "value"),
    )
    def update_timeline_graph(pep_number):
        """
        PEP番号入力に連動してタイムライングラフを更新する

        Args:
            pep_number: 入力されたPEP番号（int または None）

        Returns:
            go.Figure: Plotlyのfigureオブジェクト
        """
        # 入力が空/Noneの場合: 空のグラフを返す
        if pep_number is None:
            return _create_empty_figure()

        # PEPの存在確認
        pep_data = get_pep_by_number(pep_number)
        if pep_data is None:
            return _create_empty_figure()

        # グラフデータを構築
        return _create_timeline_figure(pep_number, pep_data)


def _convert_df_to_table_data(df) -> list[dict]:
    """
    DataFrameをDataTable用のデータ形式に変換する

    Args:
        df: PEPメタデータのDataFrame

    Returns:
        list[dict]: DataTable用のレコードリスト
    """
    if df.empty:
        return []

    table_data: list[dict] = []
    for idx, row in df.iterrows():
        pep_number = row["pep_number"]
        pep_url = generate_pep_url(pep_number)

        # 日付をフォーマット（YYYY-MM-DD）
        created_str = row["created"].strftime("%Y-%m-%d")

        table_data.append(
            {
                "row_num": len(table_data) + 1,  # 通し番号（1から開始）
                "pep": f"[PEP {pep_number}]({pep_url})",  # Markdownリンク
                "pep_number": pep_number,  # ソート用（非表示）
                "title": row["title"],
                "status": row["status"],
                "created": created_str,
            }
        )

    return table_data


def _create_pep_info_display(pep_data) -> html.Div:
    """
    PEP情報表示コンポーネントを生成する

    Args:
        pep_data: PEPのメタデータ（pd.Series）

    Returns:
        html.Div: PEP情報のコンポーネント
    """
    pep_number = pep_data["pep_number"]
    title = pep_data["title"]
    status = pep_data["status"]
    pep_type = pep_data["type"]
    created = pep_data["created"]

    # 日付をフォーマット（YYYY-MM-DD）
    created_str = created.strftime("%Y-%m-%d")

    # PEPページへのURL
    pep_url = generate_pep_url(pep_number)

    return html.Div(
        [
            # 1行目: Created と Type
            html.P(
                f"Created: {created_str}  Type: {pep_type}",
                style={
                    "marginBottom": "4px",
                    "color": "#666",
                    "fontSize": "14px",
                },
            ),
            # 2行目: PEP番号（リンク付き）
            html.H3(
                html.A(
                    f"PEP {pep_number}",
                    href=pep_url,
                    target="_blank",
                    style={
                        "color": "#0066cc",
                        "textDecoration": "none",
                    },
                ),
                style={
                    "marginBottom": "4px",
                    "marginTop": "0",
                },
            ),
            # 3行目: タイトル（Statusを括弧内に表示）
            html.P(
                f"{title} ({status})",
                style={
                    "marginBottom": "0",
                    "fontSize": "16px",
                },
            ),
        ]
    )


def _create_empty_figure() -> go.Figure:
    """
    空のグラフ（初期状態）を生成する

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


def _create_timeline_figure(pep_number: int, pep_data) -> go.Figure:
    """
    タイムライングラフを生成する

    Args:
        pep_number: 選択中のPEP番号
        pep_data: 選択中のPEPのメタデータ

    Returns:
        go.Figure: Plotly figureオブジェクト
    """
    # 引用関係のPEPを取得
    citing_peps_df = get_citing_peps(pep_number)  # このPEPを引用しているPEP
    cited_peps_df = get_cited_peps(pep_number)  # このPEPに引用されているPEP

    # グラフデータを構築
    dates = []
    y_positions = []
    colors = []
    texts = []
    hover_texts = []

    # 選択中のPEP（Y=0）
    dates.append(pep_data["created"])
    y_positions.append(0)
    colors.append(STATUS_COLOR_MAP.get(pep_data["status"], DEFAULT_STATUS_COLOR))
    texts.append(str(pep_number))
    hover_texts.append(
        f"PEP {pep_number}<br>"
        f"{pep_data['title']}<br>"
        f"Status: {pep_data['status']}<br>"
        f"Created: {pep_data['created'].strftime('%Y-%m-%d')}"
    )

    # 引用しているPEP（Y=1）
    for _, row in citing_peps_df.iterrows():
        dates.append(row["created"])
        y_positions.append(1)
        colors.append(STATUS_COLOR_MAP.get(row["status"], DEFAULT_STATUS_COLOR))
        texts.append(str(row["pep_number"]))
        hover_texts.append(
            f"PEP {row['pep_number']}<br>"
            f"{row['title']}<br>"
            f"Status: {row['status']}<br>"
            f"Created: {row['created'].strftime('%Y-%m-%d')}"
        )

    # 引用されているPEP（Y=-1）
    for _, row in cited_peps_df.iterrows():
        dates.append(row["created"])
        y_positions.append(-1)
        colors.append(STATUS_COLOR_MAP.get(row["status"], DEFAULT_STATUS_COLOR))
        texts.append(str(row["pep_number"]))
        hover_texts.append(
            f"PEP {row['pep_number']}<br>"
            f"{row['title']}<br>"
            f"Status: {row['status']}<br>"
            f"Created: {row['created'].strftime('%Y-%m-%d')}"
        )

    # Plotly Figureを生成
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=y_positions,
            mode="markers+text",
            marker=dict(
                color=colors,
                size=10,
            ),
            text=texts,
            textposition="top right",
            textfont=dict(size=10),
            hovertext=hover_texts,
            hoverinfo="text",
        )
    )

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
            zeroline=True,
            zerolinecolor="#ddd",
            zerolinewidth=1,
        ),
        showlegend=False,
        margin=dict(l=40, r=40, t=40, b=40),
        hovermode="closest",
    )

    return fig
