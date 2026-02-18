"""Timelineタブのコールバック関数"""

import plotly.graph_objects as go
from dash import Input, Output, html

from src.dash_app.components import create_empty_figure, create_initial_info_message
from src.dash_app.utils.constants import (
    DEFAULT_STATUS_COLOR,
    STATUS_COLOR_MAP,
    TIMELINE_MARKER_SIZE,
    TIMELINE_MARGIN,
    TIMELINE_TEXT_FONT_SIZE,
    TIMELINE_Y_CITED,
    TIMELINE_Y_CITING,
    TIMELINE_Y_RANGE,
    TIMELINE_Y_SELECTED,
    TIMELINE_Y_TICKVALS,
    TIMELINE_ZEROLINE_COLOR,
    TIMELINE_ZEROLINE_WIDTH,
)
from src.dash_app.utils.data_loader import (
    generate_pep_url,
    get_cited_peps,
    get_citing_peps,
    get_pep_by_number,
)


def _parse_pep_number(value):
    """
    PEP番号の入力値を整数に変換する

    Args:
        value: 入力値（str, int, None）

    Returns:
        int | None: 整数に変換されたPEP番号、または None
    """
    if value is None or value == "":
        return None

    try:
        return int(value)
    except (ValueError, TypeError):
        return None


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
            pep_number: 入力されたPEP番号（str, int または None）

        Returns:
            tuple: (PEP情報表示コンテンツ, エラーメッセージ)
        """
        # 入力値を整数に変換
        pep_number = _parse_pep_number(pep_number)

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

    @app.callback(
        Output("citing-peps-title", "children"),
        Output("cited-peps-title", "children"),
        Input("pep-input", "value"),
    )
    def update_table_titles(pep_number):
        """
        PEP番号入力に連動してテーブルタイトルを更新する

        Args:
            pep_number: 入力されたPEP番号（str, int または None）

        Returns:
            tuple: (citing_title, cited_title)
        """
        pep_number = _parse_pep_number(pep_number)

        if pep_number is None:
            return "PEP N is linked from...", "PEP N links to..."

        return f"PEP {pep_number} is linked from...", f"PEP {pep_number} links to..."

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
            pep_number: 入力されたPEP番号（str, int または None）

        Returns:
            tuple: (citing_tableのデータ, cited_tableのデータ)
        """
        # 入力値を整数に変換
        pep_number = _parse_pep_number(pep_number)

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
            pep_number: 入力されたPEP番号（str, int または None）

        Returns:
            go.Figure: Plotlyのfigureオブジェクト
        """
        # 入力値を整数に変換
        pep_number = _parse_pep_number(pep_number)

        # 入力が空/Noneの場合: 空のグラフを返す
        if pep_number is None:
            return create_empty_figure()

        # PEPの存在確認
        pep_data = get_pep_by_number(pep_number)
        if pep_data is None:
            return create_empty_figure()

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
            # 1行目: PEP番号（リンク付き）とタイトル
            html.H3(
                [
                    html.A(
                        f"PEP {pep_number}",
                        href=pep_url,
                        target="_blank",
                        style={
                            "color": "#0066cc",
                            "textDecoration": "underline",
                        },
                    ),
                    f": {title}",
                ],
                style={
                    "marginBottom": "4px",
                    "marginTop": "0",
                },
            ),
            # 2行目: Created、Type、Status
            html.P(
                [
                    html.Span("Created: "),
                    created_str,
                    html.Span("Type: ", style={"marginLeft": "20px"}),
                    pep_type,
                    html.Span("Status: ", style={"marginLeft": "20px"}),
                    status,
                ],
                style={
                    "marginBottom": "0",
                    "color": "#666",
                    "fontSize": "14px",
                },
            ),
        ]
    )


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
    y_positions.append(TIMELINE_Y_SELECTED)
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
        y_positions.append(TIMELINE_Y_CITING)
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
        y_positions.append(TIMELINE_Y_CITED)
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
                size=TIMELINE_MARKER_SIZE,
            ),
            text=texts,
            textposition="top right",
            textfont=dict(size=TIMELINE_TEXT_FONT_SIZE),
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
            tickvals=TIMELINE_Y_TICKVALS,
            ticktext=["", "", ""],
            range=list(TIMELINE_Y_RANGE),
            showgrid=False,
            zeroline=True,
            zerolinecolor=TIMELINE_ZEROLINE_COLOR,
            zerolinewidth=TIMELINE_ZEROLINE_WIDTH,
        ),
        showlegend=False,
        margin=dict(**TIMELINE_MARGIN),
        hovermode="closest",
    )

    return fig
