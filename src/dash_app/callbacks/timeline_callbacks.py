"""Timelineタブのコールバック関数"""

import plotly.graph_objects as go
from dash import Input, Output, html, no_update

from src.dash_app.components import create_empty_figure, create_initial_info_message
from src.dash_app.components.timeline_figures import (
    _get_guideline_shapes,
    _get_xaxis_config,
)
from src.dash_app.utils.constants import (
    DEFAULT_STATUS_COLOR,
    STATUS_COLOR_MAP,
    TIMELINE_ANNOTATION_ARROW_AY,
    TIMELINE_ANNOTATION_ARROW_COLOR,
    TIMELINE_ANNOTATION_ARROW_SIZE,
    TIMELINE_ANNOTATION_ARROW_WIDTH,
    TIMELINE_ANNOTATION_TEXT_COLOR,
    TIMELINE_ANNOTATION_TEXT_SIZE,
    TIMELINE_ANNOTATION_X,
    TIMELINE_ANNOTATION_Y_CITED_TEXT,
    TIMELINE_ANNOTATION_Y_CITING_TEXT,
    TIMELINE_MARKER_SIZE,
    TIMELINE_MARGIN,
    TIMELINE_TEXT_FONT_SIZE,
    TIMELINE_Y_CITED,
    TIMELINE_Y_CITING,
    TIMELINE_Y_RANGE,
    TIMELINE_Y_SELECTED,
    TIMELINE_Y_TICKVALS,
    PYTHON_2_LINE_COLOR,
    PYTHON_3_LINE_COLOR,
    TIMELINE_Y_PYTHON2_LABEL,
    TIMELINE_Y_PYTHON3_LABEL,
)
from src.dash_app.utils.data_loader import (
    generate_pep_url,
    get_cited_peps,
    get_citing_peps,
    get_pep_by_number,
    get_python_releases_by_major_version,
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
        return _compute_table_titles(pep_number)

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
        Input("python-release-checkboxes", "value"),
    )
    def update_timeline_graph(pep_number, python_release_options):
        """
        PEP番号入力とチェックボックスに連動してタイムライングラフを更新する

        Args:
            pep_number: 入力されたPEP番号（str, int または None）
            python_release_options: 選択されたPythonリリース表示オプション（list）
                - "python2": Python 2系を表示
                - "python3": Python 3系を表示

        Returns:
            go.Figure: Plotlyのfigureオブジェクト
        """
        # 入力値を整数に変換
        pep_number = _parse_pep_number(pep_number)

        # python_release_optionsがNoneの場合は空リストに
        if python_release_options is None:
            python_release_options = []

        # 入力が空/Noneの場合: 空のグラフ + 縦線を返す
        if pep_number is None:
            fig = create_empty_figure()
            _add_python_release_lines(fig, python_release_options)
            return fig

        # PEPの存在確認
        pep_data = get_pep_by_number(pep_number)
        if pep_data is None:
            fig = create_empty_figure()
            _add_python_release_lines(fig, python_release_options)
            return fig

        # グラフデータを構築
        return _create_timeline_figure(pep_number, pep_data, python_release_options)

    # === クリックイベント: 点をクリックしたときにPEPページへ遷移 ===
    @app.callback(
        Output("pep-url", "href"),
        Input("timeline-graph", "clickData"),
        prevent_initial_call=True,
    )
    def navigate_to_pep(click_data):
        """
        タイムラインのグラフ上のデータ点をクリックしたときにPEPページへ遷移する

        Args:
            click_data: Plotlyのクリックイベントデータ

        Returns:
            str | None: PEPページのURL、またはno_update
        """
        # 本当は別タブ遷移にしたいがJavaScriptを使う必要がありそうなので一旦同タブ遷移にしている
        if click_data and click_data["points"]:
            # customdata は JSON シリアライズ経由で float/str になる可能性があるため int() でキャスト
            pep_number = int(click_data["points"][0]["customdata"])
            return generate_pep_url(pep_number)
        return no_update


def _compute_table_titles(pep_number_input) -> tuple[str, str]:
    """
    テーブルタイトルを計算する

    Args:
        pep_number_input: 入力されたPEP番号（str, int または None）

    Returns:
        tuple: (citing_title, cited_title)
    """
    pep_number = _parse_pep_number(pep_number_input)

    if pep_number is None:
        return "PEP N is cited by...", "PEP N cites..."

    if get_pep_by_number(pep_number) is None:
        return "PEP N is cited by...", "PEP N cites..."

    return f"PEP {pep_number} is cited by...", f"PEP {pep_number} cites..."


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


def _create_status_badge(status: str):
    """
    Statusバッジ（色付き四角 + テキスト）を生成する

    Args:
        status: PEPのステータス

    Returns:
        html.Span: 色付きバッジコンポーネント
    """
    bg_color = STATUS_COLOR_MAP.get(status, DEFAULT_STATUS_COLOR)

    return html.Span(
        [
            # 色付き四角
            html.Span(
                style={
                    "display": "inline-block",
                    "width": "12px",
                    "height": "12px",
                    "backgroundColor": bg_color,
                    "marginRight": "4px",
                    "verticalAlign": "middle",
                    "border": "1px solid #ccc",
                }
            ),
            # Statusテキスト
            html.Span(
                status,
                style={
                    "verticalAlign": "middle",
                    "fontWeight": "normal",
                },
            ),
        ],
        style={
            "display": "inline",
            "marginLeft": "0px",
        },
    )


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
                    _create_status_badge(status),
                ],
                style={
                    "marginBottom": "0",
                    "color": "#666",
                    "fontSize": "14px",
                },
            ),
        ]
    )


def _create_pep_annotations(pep_number: int) -> list[dict]:
    """
    PEP番号入力時のアノテーション（テキストと矢印）を生成する

    Args:
        pep_number: 入力されたPEP番号

    Returns:
        list[dict]: アノテーション設定のリスト
    """
    return [
        # 上部: 矢印のみ (TIMELINE_Y_CITING のPEP群から TIMELINE_Y_SELECTED へ)
        # arrowhead が TIMELINE_Y_SELECTED (Y=0)、tail は TIMELINE_Y_CITING (Y=1) 方向
        dict(
            text="",
            xref="paper",
            yref="y",
            x=TIMELINE_ANNOTATION_X,
            y=TIMELINE_Y_SELECTED,
            ax=0,
            ay=TIMELINE_ANNOTATION_ARROW_AY,
            showarrow=True,
            arrowhead=2,
            arrowsize=TIMELINE_ANNOTATION_ARROW_SIZE,
            arrowwidth=TIMELINE_ANNOTATION_ARROW_WIDTH,
            arrowcolor=TIMELINE_ANNOTATION_ARROW_COLOR,
        ),
        # 上部テキスト: TIMELINE_Y_CITING と TIMELINE_Y_SELECTED の中間より下
        dict(
            text=f"PEP {pep_number} is cited by ...",
            xref="paper",
            yref="y",
            x=TIMELINE_ANNOTATION_X,
            y=TIMELINE_ANNOTATION_Y_CITING_TEXT,
            showarrow=False,
            font=dict(
                size=TIMELINE_ANNOTATION_TEXT_SIZE,
                color=TIMELINE_ANNOTATION_TEXT_COLOR,
            ),
            align="left",
            xanchor="left",
            yanchor="middle",
        ),
        # 下部: 矢印のみ (TIMELINE_Y_CITED のPEP群から TIMELINE_Y_SELECTED へ)
        # arrowhead が TIMELINE_Y_CITED (Y=-1)、tail は TIMELINE_Y_SELECTED (Y=0) 方向
        dict(
            text="",
            xref="paper",
            yref="y",
            x=TIMELINE_ANNOTATION_X,
            y=TIMELINE_Y_CITED,
            ax=0,
            ay=TIMELINE_ANNOTATION_ARROW_AY,
            showarrow=True,
            arrowhead=2,
            arrowsize=TIMELINE_ANNOTATION_ARROW_SIZE,
            arrowwidth=TIMELINE_ANNOTATION_ARROW_WIDTH,
            arrowcolor=TIMELINE_ANNOTATION_ARROW_COLOR,
        ),
        # 下部テキスト: TIMELINE_Y_CITED と TIMELINE_Y_SELECTED の中間より上
        dict(
            text=f"PEP {pep_number} links to ...",
            xref="paper",
            yref="y",
            x=TIMELINE_ANNOTATION_X,
            y=TIMELINE_ANNOTATION_Y_CITED_TEXT,
            showarrow=False,
            font=dict(
                size=TIMELINE_ANNOTATION_TEXT_SIZE,
                color=TIMELINE_ANNOTATION_TEXT_COLOR,
            ),
            align="left",
            xanchor="left",
            yanchor="middle",
        ),
    ]


def _create_timeline_figure(
    pep_number: int, pep_data, python_release_options: list[str] | None = None
) -> go.Figure:
    """
    タイムライングラフを生成する

    Args:
        pep_number: 選択中のPEP番号
        pep_data: 選択中のPEPのメタデータ
        python_release_options: Pythonリリース表示オプション

    Returns:
        go.Figure: Plotly figureオブジェクト
    """
    if python_release_options is None:
        python_release_options = []
    # 引用関係のPEPを取得
    citing_peps_df = get_citing_peps(pep_number)  # このPEPを引用しているPEP
    cited_peps_df = get_cited_peps(pep_number)  # このPEPに引用されているPEP

    # グラフデータを構築
    dates = []
    y_positions = []
    colors = []
    texts = []
    hover_texts = []
    pep_numbers = []  # クリック時のURL生成用

    # 選択中のPEP（Y=0）
    dates.append(pep_data["created"])
    y_positions.append(TIMELINE_Y_SELECTED)
    colors.append(STATUS_COLOR_MAP.get(pep_data["status"], DEFAULT_STATUS_COLOR))
    texts.append(str(pep_number))
    pep_numbers.append(pep_number)
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
        pep_numbers.append(row["pep_number"])
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
        pep_numbers.append(row["pep_number"])
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
                opacity=0.7,
            ),
            text=texts,
            textposition="top right",
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
        xaxis=_get_xaxis_config(),
        yaxis=dict(
            tickvals=TIMELINE_Y_TICKVALS,
            ticktext=["", "", ""],
            range=list(TIMELINE_Y_RANGE),
            showgrid=False,
        ),
        showlegend=False,
        margin=dict(**TIMELINE_MARGIN),
        hovermode="closest",
        shapes=_get_guideline_shapes(),
        annotations=_create_pep_annotations(pep_number),
    )

    # Pythonリリース日の縦線を追加
    _add_python_release_lines(fig, python_release_options)

    return fig


def _add_python_release_lines(
    fig: go.Figure, python_release_options: list[str]
) -> None:
    """
    タイムライングラフにPythonリリース日の縦線を追加する

    Args:
        fig: Plotly figureオブジェクト
        python_release_options: Pythonリリース表示オプション
            - "python2": Python 2系を表示
            - "python3": Python 3系を表示
    """
    if "python2" in python_release_options:
        _add_release_lines_for_major_version(
            fig, 2, PYTHON_2_LINE_COLOR, TIMELINE_Y_PYTHON2_LABEL
        )

    if "python3" in python_release_options:
        _add_release_lines_for_major_version(
            fig, 3, PYTHON_3_LINE_COLOR, TIMELINE_Y_PYTHON3_LABEL
        )


def _add_release_lines_for_major_version(
    fig: go.Figure, major_version: int, line_color: str, y_label_position: float
) -> None:
    """
    指定したメジャーバージョンのPythonリリース日縦線を追加する

    Args:
        fig: Plotly figureオブジェクト
        major_version: Pythonメジャーバージョン（2 or 3）
        line_color: 縦線の色
        y_label_position: バージョンラベルを表示するY座標
    """
    releases = get_python_releases_by_major_version(major_version)

    for _, row in releases.iterrows():
        release_date = row["release_date"]
        version = row["version"]

        # 縦線を追加
        fig.add_vline(
            x=release_date,
            line=dict(
                color=line_color,
                width=1,
                dash="solid",
            ),
        )

        # バージョン番号ラベルをY座標指定でアノテーション表示
        fig.add_annotation(
            x=release_date,
            y=y_label_position,
            text=version,
            showarrow=False,
            xref="x",
            yref="y",
            font=dict(
                size=10,
                color=line_color,
            ),
            xanchor="left",
            yanchor="middle",
        )
