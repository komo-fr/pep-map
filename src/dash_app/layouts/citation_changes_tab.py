"""Citation Changesタブのレイアウト"""

from src.dash_app.utils.data_loader import load_metadata

from dash import dash_table, html

from src.dash_app.utils.constants import (
    CHANGE_TYPE_COLOR_MAP,
    CHANGE_TYPE_FONT_COLOR_MAP,
)
from src.dash_app.utils.data_loader import load_citation_changes


def create_citation_changes_tab_layout() -> html.Div:
    """
    Citation Changesタブのレイアウトを作成

    Returns:
        html.Div: Citation Changesタブのレイアウト
    """
    # データを読み込む
    df = load_citation_changes()

    # チェック日付を取得
    metadata = load_metadata()
    checked_at = metadata["checked_at"]

    # citing_markdown → citing, cited_markdown → cited にリネーム
    df = df.rename(columns={"citing_markdown": "citing", "cited_markdown": "cited"})

    # Change Type ごとの背景色とフォント色のスタイルを作成
    style_data_conditional = []
    for change_type, bg_color in CHANGE_TYPE_COLOR_MAP.items():
        font_color = CHANGE_TYPE_FONT_COLOR_MAP[change_type]
        style_data_conditional.append(
            {
                "if": {
                    "filter_query": f"{{change_type}} = {change_type}",
                    "column_id": "change_type",
                },
                "backgroundColor": bg_color,
                "color": font_color,
                "textAlign": "center",
            }
        )

    # PEP列（citingとcited）の位置調整スタイルを追加
    # Markdownリンクの位置を調整するために、paddingとverticalAlignを設定
    style_data_conditional.extend(
        [
            {
                "if": {"column_id": "citing"},
                "paddingTop": "11px",
                "paddingBottom": "0px",
                "fontSize": "14px",
                "verticalAlign": "bottom",
            },
            {
                "if": {"column_id": "cited"},
                "paddingTop": "11px",
                "paddingBottom": "0px",
                "fontSize": "14px",
                "verticalAlign": "bottom",
            },
        ]
    )

    return html.Div(
        [
            # 説明文
            html.Div(
                [
                    html.P(
                        "This table lists changes in citation relationships (Added, Changed, or Deleted) detected during data checks.",
                        style={"marginBottom": "8px"},
                    ),
                    html.P(
                        [
                            html.Strong("Note:"),
                            " ",
                            html.Code("Detected"),
                            " indicates when the change was observed by this system, not when the change originally occurred in the PEP.",
                        ],
                        style={"marginBottom": "8px", "color": "#666"},
                    ),
                ],
                style={
                    "fontSize": "14px",
                    "color": "#333",
                },
            ),
            # 区切り線
            html.Hr(
                style={
                    "margin": "16px 0",
                    "border": "none",
                    "borderTop": "1px solid #888",
                }
            ),
            # Last checked（右寄せ）
            html.Div(
                [
                    html.Strong("Last checked:"),
                    f" {checked_at}",
                ],
                style={
                    "fontSize": "12px",
                    "color": "#666",
                    "textAlign": "right",
                    "margin": "8px 0",
                },
            ),
            # DataTableコンポーネント
            dash_table.DataTable(  # type: ignore[attr-defined]
                id="citation-changes-table",
                columns=[
                    {"name": ["", "Detected"], "id": "detected", "type": "text"},
                    {"name": ["", "Change"], "id": "change_type", "type": "text"},
                    {
                        "name": ["PEP", "Citing"],
                        "id": "citing",
                        "type": "text",
                        "presentation": "markdown",
                    },
                    {
                        "name": ["PEP", "Cited"],
                        "id": "cited",
                        "type": "text",
                        "presentation": "markdown",
                    },
                    {"name": ["Title", "Citing"], "id": "citing_title", "type": "text"},
                    {"name": ["Title", "Cited"], "id": "cited_title", "type": "text"},
                    {"name": ["Count", "Before"], "id": "count_before", "type": "text"},
                    {"name": ["Count", "After"], "id": "count_after", "type": "text"},
                ],
                data=df.to_dict("records"),
                sort_action="native",
                filter_action="native",
                merge_duplicate_headers=True,
                style_table={"overflowX": "auto"},
                style_cell={
                    "textAlign": "left",
                    "padding": "4px 6px",
                    "fontSize": "15px",
                    "height": "auto",
                    "minHeight": "18px",
                },
                style_data={
                    "lineHeight": "1.1",
                    "verticalAlign": "middle",
                },
                style_header={
                    "backgroundColor": "#f5f5f5",
                    "fontWeight": "bold",
                },
                style_header_conditional=[
                    # PEP、Title、Count、Changeのヘッダーを中央寄せ
                    {"if": {"column_id": "change_type"}, "textAlign": "center"},
                    {"if": {"column_id": "citing"}, "textAlign": "center"},
                    {"if": {"column_id": "cited"}, "textAlign": "center"},
                    {"if": {"column_id": "citing_title"}, "textAlign": "center"},
                    {"if": {"column_id": "cited_title"}, "textAlign": "center"},
                    {"if": {"column_id": "count_before"}, "textAlign": "center"},
                    {"if": {"column_id": "count_after"}, "textAlign": "center"},
                ],
                style_data_conditional=style_data_conditional,
            ),
        ],
        style={"padding": "20px"},
    )
