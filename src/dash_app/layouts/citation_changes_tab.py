"""Citation Changesタブのレイアウト"""

from dash import dash_table, html

from src.dash_app.utils.data_loader import load_citation_changes


def create_citation_changes_tab_layout() -> html.Div:
    """
    Citation Changesタブのレイアウトを作成

    Returns:
        html.Div: Citation Changesタブのレイアウト
    """
    # データを読み込む
    df = load_citation_changes()

    return html.Div(
        [
            # DataTableコンポーネント
            dash_table.DataTable(  # type: ignore[attr-defined]
                id="citation-changes-table",
                columns=[
                    {"name": ["", "Detected"], "id": "detected", "type": "text"},
                    {"name": ["", "Change"], "id": "change_type", "type": "text"},
                    {"name": ["PEP", "Citing"], "id": "citing", "type": "numeric"},
                    {"name": ["PEP", "Cited"], "id": "cited", "type": "numeric"},
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
                    "padding": "8px",
                    "fontSize": "14px",
                },
                style_header={
                    "backgroundColor": "#f8f9fa",
                    "fontWeight": "bold",
                    "borderBottom": "2px solid #dee2e6",
                },
            ),
        ],
        style={"padding": "20px"},
    )
