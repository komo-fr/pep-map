"""Groupタブのコールバック関数"""

import re
import pandas as pd
import dash_cytoscape as cyto
from dash import Input, Output, State, callback_context, no_update, html, ALL
from dash.development.base_component import Component
from src.dash_app.components.pep_info import (
    create_group_initial_info_message,
    create_pep_info_display,
)
from src.dash_app.components import parse_pep_number
from src.dash_app.components.subgraph_network_graph import (
    build_subgraph_cytoscape_elements,
    get_subgraph_base_stylesheet,
    get_subgraph_layout_options,
)
from src.dash_app.utils.constants import TEXT_OUTLINE_COLOR, TEXT_OUTLINE_WIDTH
from src.dash_app.utils.data_loader import (
    get_peps_by_group,
    get_pep_by_number,
    get_group_id_by_pep,
    generate_pep_url,
    get_group_name_info,
    load_peps_metadata,
    get_adjacent_groups,
    get_top_peps_by_group,
    get_group_boundary_data,
)
from src.dash_app.layouts.group_tab import create_subgraph_placeholder_with_dummy


# PEP番号とメタデータのキャッシュ
_pep_numbers_cache: set[int] | None = None
_pep_metadata_cache: dict[int, dict[str, str]] | None = None

# グループ選択コールバックの静的出力キャッシュ
# キー: group_id, 値: (table_data, title, group_name, description_children,
#                      description_style, adjacent_children, adjacent_style, subgraph_children)
_group_selection_output_cache: dict[int, tuple] = {}

# グループボタンのスタイル（隣接グループ表示用）
_GROUP_BUTTON_STYLE: dict[str, str] = {
    "display": "inline-block",
    "padding": "0px 5px",
    "margin": "2px 4px 2px 0",
    "backgroundColor": "#E8E8E8",
    "border": "1px solid #CCC",
    "borderRadius": "16px",
    "fontSize": "12px",
    "cursor": "pointer",
    "color": "#333",
}

# 隣接グループセクションのスタイル
_ADJACENT_SECTION_STYLE: dict[str, str] = {
    "marginBottom": "8px",
    "marginTop": "0",
}

# Full Network用 基本スタイルシートのJavaScript定義（共通部分）
# グループ選択時とサブグラフタップ時の両方で使用
_FULL_NETWORK_BASE_STYLES_JS = f"""[
    {{
        selector: 'node',
        style: {{
            'label': 'data(label)',
            'background-color': 'data(group_color)',
            'width': 'data(size_pagerank)',
            'height': 'data(size_pagerank)',
            'font-size': 'data(font_size_pagerank)',
            'text-valign': 'center',
            'text-halign': 'center',
            'border-width': 1,
            'border-color': '#999',
            'opacity': 0.8,
            'text-outline-width': {TEXT_OUTLINE_WIDTH},
            'text-outline-color': '{TEXT_OUTLINE_COLOR}'
        }}
    }},
    {{
        selector: 'edge',
        style: {{
            'width': 2,
            'line-color': '#999',
            'target-arrow-color': '#999',
            'target-arrow-shape': 'triangle',
            'arrow-scale': 1,
            'curve-style': 'bezier',
            'opacity': 0.3
        }}
    }},
    {{
        selector: '.group-selected',
        style: {{
            'opacity': 1,
            'border-width': 2,
            'border-color': '#333',
            'text-outline-width': {TEXT_OUTLINE_WIDTH},
            'text-outline-color': '{TEXT_OUTLINE_COLOR}'
        }}
    }},
    {{
        selector: '.group-faded',
        style: {{
            'opacity': 0.15
        }}
    }},
    {{
        selector: '.group-selected-edge',
        style: {{
            'opacity': 1,
            'line-color': '#666',
            'target-arrow-color': '#666',
            'width': 2
        }}
    }}
]"""

# Full Network用 追加スタイル（グループ選択時のみ使用）
# :selected と .pep-highlighted のスタイル
_FULL_NETWORK_SELECTION_STYLES_JS = f"""[
    {{
        selector: ':selected',
        style: {{
            'border-width': 4,
            'border-color': '#FF0000',
            'z-index': 9999,
            'opacity': 1,
            'text-outline-width': {TEXT_OUTLINE_WIDTH},
            'text-outline-color': '{TEXT_OUTLINE_COLOR}'
        }}
    }},
    {{
        selector: '.pep-highlighted',
        style: {{
            'border-width': 4,
            'border-color': '#FF0000',
            'z-index': 9999,
            'opacity': 1,
            'text-outline-width': {TEXT_OUTLINE_WIDTH},
            'text-outline-color': '{TEXT_OUTLINE_COLOR}'
        }}
    }}
]"""

# Full Network用 オーバーライドスタイル（共通部分）
# 赤枠を非表示にするスタイル
_FULL_NETWORK_OVERRIDE_STYLES_JS = f"""[
    {{
        selector: ':selected',
        style: {{
            'border-width': 1,
            'border-color': '#999',
            'opacity': 0.8,
            'text-outline-width': {TEXT_OUTLINE_WIDTH},
            'text-outline-color': '{TEXT_OUTLINE_COLOR}'
        }}
    }},
    {{
        selector: '.group-selected:selected',
        style: {{
            'border-width': 2,
            'border-color': '#333',
            'opacity': 1,
            'text-outline-width': {TEXT_OUTLINE_WIDTH},
            'text-outline-color': '{TEXT_OUTLINE_COLOR}'
        }}
    }},
    {{
        selector: '.group-faded:selected',
        style: {{
            'border-width': 1,
            'border-color': '#999',
            'opacity': 0.15,
            'text-outline-width': {TEXT_OUTLINE_WIDTH},
            'text-outline-color': '{TEXT_OUTLINE_COLOR}'
        }}
    }}
]"""

# Full Network用 追加オーバーライドスタイル（グループ選択時のみ使用）
# pep-highlightedクラスの赤枠を非表示にするスタイル
_FULL_NETWORK_PEP_HIGHLIGHTED_OVERRIDE_STYLES_JS = f"""[
    {{
        selector: '.group-selected.pep-highlighted',
        style: {{
            'border-width': 2,
            'border-color': '#333',
            'opacity': 1,
            'text-outline-width': {TEXT_OUTLINE_WIDTH},
            'text-outline-color': '{TEXT_OUTLINE_COLOR}'
        }}
    }},
    {{
        selector: '.group-faded.pep-highlighted',
        style: {{
            'border-width': 1,
            'border-color': '#999',
            'opacity': 0.15,
            'text-outline-width': {TEXT_OUTLINE_WIDTH},
            'text-outline-color': '{TEXT_OUTLINE_COLOR}'
        }}
    }}
]"""


def _create_group_button_with_tooltip(
    grp_id: int,
    weight: int,
    direction: str,
    button_style: dict[str, str],
) -> Component:
    """ツールチップ付きのグループボタンを作成

    Args:
        grp_id: グループID
        weight: 引用数
        direction: "citing" または "cited"（IDの一意性のため）
        button_style: ボタンのスタイル辞書

    Returns:
        ツールチップ付きボタンのSpanコンポーネント
    """
    # グループ名を取得
    grp_info = get_group_name_info(grp_id)
    grp_name = grp_info["group_name"] or f"Group {grp_id}"

    # 代表的なPEPを取得
    top_peps = get_top_peps_by_group(grp_id, top_n=5)
    top_peps_str = ", ".join(str(p) for p in top_peps) if top_peps else "-"

    # ツールチップコンテンツを作成
    tooltip_content = [
        html.Div(
            grp_name,
            style={"fontWeight": "bold", "marginBottom": "4px"},
        ),
        html.Div(
            f"Citation links: {weight}",
            style={"fontSize": "11px", "color": "#aaa"},
        ),
        html.Div(
            f"Top PEPs by PageRank: {top_peps_str}",
            style={"fontSize": "11px", "color": "#aaa", "marginTop": "2px"},
        ),
    ]

    return html.Span(
        [
            html.Span(
                f"Group {grp_id}",
                style=button_style,
            ),
            html.Span(
                tooltip_content,
                className="pep-tooltip-text",
            ),
        ],
        id={
            "type": "adjacent-group-button",
            "group_id": grp_id,
            "direction": direction,
        },
        className="pep-link-tooltip",
        style={"cursor": "pointer"},
    )


def _get_pep_data() -> tuple[set[int], dict[int, dict[str, str]]]:
    """
    PEP番号のセットとメタデータマッピングを取得する（キャッシュ付き）

    Returns:
        tuple[set[int], dict[int, dict[str, str]]]:
            (PEP番号のセット, PEP番号→メタデータの辞書)
            メタデータには title, status, created が含まれる
    """
    global _pep_numbers_cache, _pep_metadata_cache
    if _pep_numbers_cache is None or _pep_metadata_cache is None:
        df = load_peps_metadata()
        _pep_numbers_cache = set(df["pep_number"].tolist())
        _pep_metadata_cache = {}
        for _, row in df.iterrows():
            pep_num = row["pep_number"]
            created = row["created"]
            # created を文字列に変換
            if pd.isna(created):
                created_str = ""
            else:
                created_str = created.strftime("%Y-%m-%d")
            _pep_metadata_cache[pep_num] = {
                "title": row["title"],
                "status": row["status"],
                "created": created_str,
            }
    return _pep_numbers_cache, _pep_metadata_cache


def _build_tooltip_content(metadata: dict[str, str]) -> list:
    """
    ツールチップの内容を構築する

    Args:
        metadata: PEPのメタデータ（title, status, created）

    Returns:
        list: ツールチップ用のDashコンポーネントリスト
    """
    title = metadata.get("title", "")
    status = metadata.get("status", "")
    created = metadata.get("created", "")

    tooltip_children = [html.Div(title)]
    if status or created:
        meta_parts = []
        if status:
            meta_parts.append(f"Status: {status}")
        if created:
            meta_parts.append(f"Created: {created}")
        tooltip_children.append(
            html.Div(
                " | ".join(meta_parts),
                style={"fontSize": "11px", "color": "#aaa", "marginTop": "4px"},
            )
        )
    return tooltip_children


def _create_pep_link(
    display_text: str, pep_num: int, metadata: dict[str, str]
) -> Component:
    """
    PEPリンク（ツールチップ付き）コンポーネントを構築する

    Args:
        display_text: リンクとして表示する文字列
        pep_num: PEP番号
        metadata: PEPのメタデータ（title, status, created）

    Returns:
        Component: ツールチップ付きリンクのDashコンポーネント
    """
    url = generate_pep_url(pep_num)
    return html.Span(
        [
            html.A(
                display_text,
                href=url,
                target="_blank",
                style={
                    "color": "#0066cc",
                    "textDecoration": "underline",
                },
            ),
            html.Span(
                _build_tooltip_content(metadata),
                className="pep-tooltip-text",
            ),
        ],
        className="pep-link-tooltip",
    )


def linkify_pep_numbers(text: str) -> list[str | Component]:
    """
    テキスト内のPEP番号をリンク付きのDashコンポーネントに変換する

    - 「PEP 484」のようなパターンをリンク化
    - 単独の数字で、後ろに「年」が続かず、存在するPEP番号の場合もリンク化
    - リンクにはツールチップでPEPタイトル・Status・Createdを表示

    Args:
        text: 変換対象のテキスト

    Returns:
        list: テキストとhtml.Aコンポーネントのリスト
    """
    pep_numbers, pep_metadata = _get_pep_data()

    # パターン:
    # 1. 「PEP 数字」のパターン（「PEP 484」など）
    # 2. 単独の数字（後ろに「年」が続かない）
    pattern = r"(PEP\s+(\d+))|(\d+)"

    result: list[str | Component] = []
    last_end = 0

    for match in re.finditer(pattern, text):
        start, end = match.span()

        # マッチ前のテキストを追加
        if start > last_end:
            result.append(text[last_end:start])

        # 「PEP XXX」パターンの場合
        if match.group(1):
            pep_num = int(match.group(2))
            matched_text = match.group(1)
            # PEP番号が存在する場合のみリンク化
            if pep_num in pep_numbers:
                metadata = pep_metadata.get(pep_num, {})
                result.append(_create_pep_link(matched_text, pep_num, metadata))
            else:
                result.append(matched_text)
        # 単独の数字の場合
        elif match.group(3):
            num_str = match.group(3)
            pep_num = int(num_str)
            # 後ろに「年」が続く場合は除外
            after_match = text[end : end + 1] if end < len(text) else ""
            if after_match == "年":
                result.append(num_str)
            # PEP番号が存在する場合のみリンク化
            elif pep_num in pep_numbers:
                metadata = pep_metadata.get(pep_num, {})
                result.append(_create_pep_link(num_str, pep_num, metadata))
            else:
                result.append(num_str)

        last_end = end

    # 残りのテキストを追加
    if last_end < len(text):
        result.append(text[last_end:])

    return result


def _compute_group_static_outputs(group_id: int) -> tuple:
    """
    指定されたグループIDの静的出力を計算する

    この関数はコールバックとプリロードの両方から呼ばれる。
    結果はキャッシュされ、2回目以降はキャッシュから返される。

    Args:
        group_id: グループID

    Returns:
        tuple: (table_data, title, group_name, description_children,
                description_style, adjacent_children, adjacent_style, subgraph_children)
    """
    # キャッシュチェック
    if group_id in _group_selection_output_cache:
        return _group_selection_output_cache[group_id]

    empty_style = {"display": "none"}
    filled_style = {
        "marginBottom": "8px",
        "marginTop": "0",
    }

    # サブグラフ計算
    if group_id < 0:
        subgraph_children: object = create_subgraph_placeholder_with_dummy()
    else:
        subgraph_elements = build_subgraph_cytoscape_elements(group_id)
        if subgraph_elements is None:
            subgraph_children = create_subgraph_placeholder_with_dummy()
        else:
            subgraph_children = cyto.Cytoscape(
                id="group-subgraph-network-graph",
                elements=subgraph_elements,
                layout=get_subgraph_layout_options(),
                style={
                    "width": "100%",
                    "height": "600px",
                    "border": "1px solid #ddd",
                    "backgroundColor": "#fafafa",
                },
                stylesheet=get_subgraph_base_stylesheet(),
            )

    df = get_peps_by_group(group_id)

    # グループ名と説明を取得
    group_info = get_group_name_info(group_id)
    group_name = group_info["group_name"]
    group_description = group_info["description"]

    # グループ名表示コンポーネント
    if group_name:
        group_name_display: object = [
            html.Span("Group Name: ", className="group-name-label"),
            html.Span(group_name, className="group-name-text"),
        ]
    else:
        group_name_display = ""

    # 説明文コンポーネント
    if not group_description:
        description_children: object = ""
        description_style = empty_style
    else:
        paragraphs = group_description.split("\n\n")
        first_paragraph = paragraphs[0]
        last_paragraph = paragraphs[-1] if len(paragraphs) > 1 else None
        middle_paragraphs = paragraphs[1:-1] if len(paragraphs) > 2 else []

        # 説明文の内容を構築
        description_content: list[Component] = [
            html.P(
                linkify_pep_numbers(first_paragraph),
                style={
                    "margin": "0",
                    "fontSize": "13px",
                    "color": "#333",
                    "whiteSpace": "pre-line",
                },
            ),
        ]

        if middle_paragraphs:
            middle_text = "\n\n".join(middle_paragraphs)
            description_content.append(
                html.Details(
                    [
                        html.Summary(
                            [
                                html.Span(
                                    "▶ ネットワーク構造の説明を表示する",
                                    className="show-when-closed",
                                ),
                                html.Span(
                                    "▼ 説明を閉じる",
                                    className="show-when-open",
                                ),
                            ],
                            style={
                                "cursor": "pointer",
                                "fontSize": "12px",
                                "color": "#0066cc",
                                "marginTop": "8px",
                                "textDecoration": "underline",
                                "listStyle": "none",
                            },
                        ),
                        html.P(
                            linkify_pep_numbers(middle_text),
                            style={
                                "margin": "8px 0 0 0",
                                "padding": "12px",
                                "fontSize": "13px",
                                "color": "#333",
                                "whiteSpace": "pre-line",
                                "backgroundColor": "#f0f7ff",
                                "border": "1px solid #d0e3f7",
                                "borderRadius": "4px",
                            },
                        ),
                    ],
                ),
            )

        if last_paragraph:
            description_content.append(
                html.P(
                    linkify_pep_numbers(last_paragraph),
                    style={
                        "marginTop": "8px",
                        "marginBottom": "0",
                        "fontSize": "13px",
                        "color": "#333",
                        "whiteSpace": "pre-line",
                    },
                ),
            )

        # AI生成の注意書きを一番下に追加
        description_content.append(
            html.Div(
                [
                    html.P(
                        "🤖 グループ名と説明はAIが自動生成したものです。内容の正確性・完全性は保証されません。",
                        style={"margin": "0", "fontSize": "12px"},
                    ),
                ],
                style={
                    "backgroundColor": "#fffacd",
                    "border": "1px solid black",
                    "padding": "4px 8px",
                    "marginTop": "12px",
                    "borderRadius": "4px",
                },
            ),
        )

        # 全体を折りたたみ可能な Details でラップ
        description_children = [
            html.Details(
                [
                    html.Summary(
                        [
                            "Group Description ",
                            html.Span(
                                "🤖 AI Generated",
                                className="ai-badge",
                            ),
                        ],
                        className="group-description-summary",
                    ),
                    html.Div(
                        description_content,
                        style={"padding": "8px 12px"},
                    ),
                ],
                open=True,
                className="group-description-details",
                style={
                    "border": "1px solid #ddd",
                    "borderRadius": "4px",
                    "marginTop": "8px",
                },
            )
        ]

        description_style = filled_style

    # 隣接グループ
    adjacent_info = get_adjacent_groups(group_id)
    citing_groups = adjacent_info["citing_groups"]
    cited_groups = adjacent_info["cited_groups"]

    citing_content: html.Div | html.P
    if citing_groups:
        citing_buttons = [
            _create_group_button_with_tooltip(
                grp_id, weight, "citing", _GROUP_BUTTON_STYLE
            )
            for grp_id, weight in citing_groups
        ]
        citing_content = html.Div(citing_buttons)
    else:
        citing_content = html.P(
            "No citing groups.",
            style={
                "margin": "0",
                "fontSize": "12px",
                "color": "#999",
                "fontStyle": "italic",
            },
        )

    cited_content: html.Div | html.P
    if cited_groups:
        cited_buttons = [
            _create_group_button_with_tooltip(
                grp_id, weight, "cited", _GROUP_BUTTON_STYLE
            )
            for grp_id, weight in cited_groups
        ]
        cited_content = html.Div(cited_buttons)
    else:
        cited_content = html.P(
            "No cited groups.",
            style={
                "margin": "0",
                "fontSize": "12px",
                "color": "#999",
                "fontStyle": "italic",
            },
        )

    adjacent_children = [
        html.Details(
            [
                html.Summary(
                    "Related Groups",
                    className="related-groups-summary",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.P(
                                    "Groups citing this group:",
                                    style={
                                        "margin": "0 0 4px 0",
                                        "fontSize": "12px",
                                        "color": "#666",
                                        "fontWeight": "bold",
                                    },
                                ),
                                citing_content,
                            ],
                            style={"marginBottom": "8px"},
                        ),
                        html.Div(
                            [
                                html.P(
                                    "Groups this group cites:",
                                    style={
                                        "margin": "0 0 4px 0",
                                        "fontSize": "12px",
                                        "color": "#666",
                                        "fontWeight": "bold",
                                    },
                                ),
                                cited_content,
                            ],
                        ),
                    ],
                    style={"padding": "8px 12px"},
                ),
            ],
            open=True,
            className="related-groups-details",
            style={
                "border": "1px solid #ddd",
                "borderRadius": "4px",
                "marginTop": "8px",
            },
        )
    ]

    # テーブルデータ
    if df.empty:
        title = f"Group {group_id} (no data)"
        result: tuple = (
            [],
            title,
            group_name_display,
            description_children,
            description_style,
            adjacent_children,
            _ADJACENT_SECTION_STYLE,
            subgraph_children,
        )
        _group_selection_output_cache[group_id] = result
        return result

    df = df.sort_values(
        by=[
            "pagerank_group",
            "in-degree_group",
            "out-degree_group",
            "degree_group",
            "PEP",
        ],
        ascending=[False, False, False, False, True],
    ).reset_index(drop=True)

    df["created_str"] = df["created"].dt.strftime("%Y-%m-%d").fillna("")
    df["pep_markdown"] = df["PEP"].apply(
        lambda pep_num: f"[PEP {pep_num}]({generate_pep_url(pep_num)})"
    )
    df["pagerank_str"] = df["pagerank_group"].apply(lambda x: f"{x:.4f}")

    # 境界グループ情報を取得
    boundary_data = get_group_boundary_data(group_id)
    df["cited_by_groups"] = df["PEP"].apply(
        lambda pep: boundary_data.get(pep, {}).get("cited_by_groups", [])
    )
    df["cited_by_groups_detail"] = df["PEP"].apply(
        lambda pep: boundary_data.get(pep, {}).get("cited_by_groups_detail", {})
    )
    df["cites_groups"] = df["PEP"].apply(
        lambda pep: boundary_data.get(pep, {}).get("cites_groups", [])
    )
    df["cites_groups_detail"] = df["PEP"].apply(
        lambda pep: boundary_data.get(pep, {}).get("cites_groups_detail", {})
    )

    table_data = (
        df[
            [
                "pep_markdown",
                "title",
                "status",
                "created_str",
                "in-degree_group",
                "out-degree_group",
                "degree_group",
                "pagerank_str",
                "cited_by_groups",
                "cited_by_groups_detail",
                "cites_groups",
                "cites_groups_detail",
            ]
        ]
        .rename(
            columns={
                "pep_markdown": "pep",
                "created_str": "created",
                "in-degree_group": "in_degree",
                "out-degree_group": "out_degree",
                "degree_group": "degree",
                "pagerank_str": "pagerank",
            }
        )
        .to_dict("records")
    )

    count = len(table_data)
    title = f"Group {group_id} ({count} PEPs)"

    result = (
        table_data,
        title,
        group_name_display,
        description_children,
        description_style,
        adjacent_children,
        _ADJACENT_SECTION_STYLE,
        subgraph_children,
    )
    _group_selection_output_cache[group_id] = result
    return result


def preload_group_selection_outputs() -> None:
    """
    全グループの静的出力を事前計算してキャッシュをウォームアップする

    起動時に呼び出すことで、グループ選択時のレスポンスを高速化する。
    """
    from src.dash_app.utils.data_loader import load_group_data

    df = load_group_data()
    group_ids = df["group_id"].unique().tolist()

    for group_id in group_ids:
        if group_id < 0:
            continue
        _compute_group_static_outputs(group_id)


def clear_cache() -> None:
    """キャッシュをクリアする（テスト用）"""
    global _group_selection_output_cache
    _group_selection_output_cache = {}


def register_group_callbacks(app):
    """
    Groupタブのコールバックを登録する

    Args:
        app: Dashアプリケーションインスタンス
    """

    # ===== ノードタップ → PEP情報更新（サーバーサイド） =====
    # NOTE: ドロップダウンの Input を分離して競合状態を回避
    @app.callback(
        Output("group-pep-info-display", "children"),
        Input("group-full-network-graph", "tapNodeData"),
        Input("group-subgraph-network-graph", "tapNodeData"),
        Input("group-to-group-network-graph", "tapNodeData"),
        prevent_initial_call=True,
    )
    def update_pep_info_from_tap(tap_data, subgraph_tap_data, group_to_group_tap_data):
        """
        ノードタップ時にPEP情報を更新する

        Args:
            tap_data: フルネットワークグラフでクリックされたノードのデータ
            subgraph_tap_data: サブグラフでクリックされたノードのデータ
            group_to_group_tap_data: Group-to-Groupグラフでクリックされたノードのデータ

        Returns:
            html.Div: PEP情報表示コンテンツ
        """
        ctx = callback_context
        if not ctx.triggered:
            return no_update

        triggered_id = ctx.triggered[0]["prop_id"]

        # Group-to-Groupのノードがタップされた場合
        if "group-to-group-network-graph" in triggered_id:
            if group_to_group_tap_data is not None:
                group_id = group_to_group_tap_data.get("group_id")
                if group_id is not None:
                    # グループ情報を表示（初期メッセージを表示）
                    return create_group_initial_info_message()
            return no_update

        # サブグラフのノードがタップされた場合
        if "group-subgraph-network-graph" in triggered_id:
            if subgraph_tap_data is not None:
                pep_number = subgraph_tap_data.get("pep_number")
                if pep_number is not None:
                    pep_data = get_pep_by_number(pep_number)
                    if pep_data is not None:
                        return create_pep_info_display(pep_data)
            return no_update

        # フルネットワークのノードがタップされた場合
        if "group-full-network-graph" in triggered_id:
            if tap_data is not None:
                pep_number = tap_data.get("pep_number")
                if pep_number is not None:
                    pep_data = get_pep_by_number(pep_number)
                    if pep_data is not None:
                        return create_pep_info_display(pep_data)
            return no_update

        return no_update

    # ===== グループ選択 → グラフハイライト更新（クライアントサイド） =====
    app.clientside_callback(
        """
        function(selectedGroup, currentElements, pepInput, selectionSource) {
            // currentElementsがない場合は更新しない
            if (!currentElements || currentElements.length === 0) {
                return window.dash_clientside.no_update;
            }

            // PEP番号入力からの選択時のみ、ハイライト対象ノードIDを取得
            var selectedPepNodeId = null;
            if (selectionSource === 'pep_input' && pepInput && pepInput !== '') {
                var pepNumber = parseInt(pepInput, 10);
                if (!isNaN(pepNumber)) {
                    selectedPepNodeId = 'pep_' + pepNumber;
                }
            }

            // "all"または未選択の場合は全ノードを通常表示
            if (selectedGroup === null || selectedGroup === undefined || selectedGroup === 'all') {
                return currentElements.map(function(el) {
                    var newEl = JSON.parse(JSON.stringify(el));
                    newEl.classes = '';
                    newEl.selected = false;
                    return newEl;
                });
            }

            // 選択されたグループIDを数値に変換
            var selectedGroupId = parseInt(selectedGroup, 10);

            // 選択グループに所属するノードIDのセットを作成
            var selectedNodeIds = new Set();
            for (var i = 0; i < currentElements.length; i++) {
                var el = currentElements[i];
                var data = el.data || {};
                if (!data.source && data.group_id === selectedGroupId) {
                    selectedNodeIds.add(data.id);
                }
            }

            // elementsを更新
            return currentElements.map(function(el) {
                var newEl = JSON.parse(JSON.stringify(el));
                var data = newEl.data || {};

                // ノードの場合
                if (!data.source) {
                    // 全ノードのselectedをfalseにする（Cytoscapeの内部選択状態をリセット）
                    newEl.selected = false;

                    // PEP番号入力から選択されたノードの場合、pep-highlightedクラスを追加
                    if (selectedPepNodeId && data.id === selectedPepNodeId) {
                        if (data.group_id === selectedGroupId) {
                            newEl.classes = 'group-selected pep-highlighted';
                        } else {
                            newEl.classes = 'group-faded pep-highlighted';
                        }
                    } else {
                        if (data.group_id === selectedGroupId) {
                            newEl.classes = 'group-selected';
                        } else {
                            newEl.classes = 'group-faded';
                        }
                    }
                }
                // エッジの場合
                else {
                    var source = data.source;
                    var target = data.target;
                    if (selectedNodeIds.has(source) && selectedNodeIds.has(target)) {
                        newEl.classes = 'group-selected-edge';
                    } else {
                        newEl.classes = 'group-faded';
                    }
                }

                return newEl;
            });
        }
        """,
        Output("group-full-network-graph", "elements"),
        Input("group-selector-dropdown", "value"),
        State("group-full-network-graph", "elements"),
        State("group-pep-input", "value"),
        State("group-selection-source", "data"),
    )

    # ===== グループ選択 → テーブル/サブグラフ/PEP情報/リセットを一括更新（サーバーサイド） =====
    # ドロップダウン変更時に発火するサーバーサイド処理を1つに集約することで
    # round trip 数を削減する。元々は4つのコールバックに分散していた。
    @app.callback(
        # テーブル関連
        Output("group-pep-table", "rowData"),
        Output("group-pep-table-title", "children"),
        Output("group-name-display", "children"),
        Output("group-description-display", "children"),
        Output("group-description-display", "style"),
        Output("adjacent-groups-display", "children"),
        Output("adjacent-groups-display", "style"),
        # サブグラフ
        Output("subgraph-container", "children"),
        # PEP情報表示エリア
        Output("group-pep-info-display", "children", allow_duplicate=True),
        # selection_source / PEP入力欄リセット
        Output("group-selection-source", "data", allow_duplicate=True),
        Output("group-pep-input", "value", allow_duplicate=True),
        Input("group-selector-dropdown", "value"),
        State("group-selection-source", "data"),
        State("group-pep-input", "value"),
        prevent_initial_call=True,
    )
    def update_on_group_selection(selected_group, selection_source, pep_input):
        """
        グループ選択時に以下を一括で更新する。

        - PEPテーブル / グループ名 / グループ説明 / 隣接グループ
        - サブグラフ
        - PEP情報表示エリア（ドロップダウン直接操作時のみ初期メッセージにリセット）
        - selection_source / PEP入力欄（ノードタップ・PEP入力起因でない場合のみリセット）

        Args:
            selected_group: 選択されたグループ（"all" または グループID）
            selection_source: 現在の選択ソース ("dropdown", "node_tap", "pep_input")
            pep_input: PEP入力欄の値

        Returns:
            tuple: 上記の全Outputに対応するタプル
        """
        # 説明文が空の時のスタイル（非表示）
        empty_style = {"display": "none"}

        # === selection_source / PEP入力欄のリセット判定 ===
        # 元の `reset_on_dropdown_change` の挙動を保持する
        pep_number = parse_pep_number(pep_input)
        if pep_number is None:
            # PEP入力欄が空の場合
            if selection_source == "pep_input":
                new_selection_source: object = "dropdown"
                new_pep_input: object = no_update
            else:
                new_selection_source = no_update
                new_pep_input = no_update
        else:
            target_group_id = get_group_id_by_pep(pep_number)
            if target_group_id is None:
                # 無効なPEP番号の場合はリセット
                if selection_source == "pep_input":
                    new_selection_source = "dropdown"
                    new_pep_input = ""
                else:
                    new_selection_source = no_update
                    new_pep_input = ""
            elif str(selected_group) == str(target_group_id):
                # ノードタップ/PEP入力からのドロップダウン更新で値が一致 → 入力値を維持
                new_selection_source = no_update
                new_pep_input = no_update
            else:
                # 異なる場合はリセット
                if selection_source == "pep_input":
                    new_selection_source = "dropdown"
                    new_pep_input = ""
                else:
                    new_selection_source = no_update
                    new_pep_input = ""

        # === PEP情報表示の更新判定 ===
        # 元の `update_pep_info_from_dropdown` の挙動を保持する
        # ノードタップ/PEP入力起因の場合は他コールバックが情報を表示済みなので触らない
        if selection_source in ("pep_input", "node_tap"):
            pep_info_children: object = no_update
        else:
            pep_info_children = create_group_initial_info_message()

        # === "all"または未選択時 ===
        if selected_group is None or selected_group == "all":
            return (
                [],
                "Select a group to view PEPs",
                "",
                "",
                empty_style,
                "",
                empty_style,
                create_subgraph_placeholder_with_dummy(),
                pep_info_children,
                new_selection_source,
                new_pep_input,
            )

        group_id = int(selected_group)

        # === 静的出力を取得（キャッシュがあれば使用、なければ計算してキャッシュ） ===
        cached = _compute_group_static_outputs(group_id)

        return (
            cached[0],  # table_data
            cached[1],  # title
            cached[2],  # group_name
            cached[3],  # description_children
            cached[4],  # description_style
            cached[5],  # adjacent_children
            cached[6],  # adjacent_style
            cached[7],  # subgraph_children
            pep_info_children,
            new_selection_source,
            new_pep_input,
        )

    # ===== ノードクリック → グループ選択更新 + 選択ソース更新 + PEP入力欄更新（サーバーサイド） =====
    @app.callback(
        Output("group-selector-dropdown", "value", allow_duplicate=True),
        Output("group-selection-source", "data", allow_duplicate=True),
        Output("group-pep-input", "value", allow_duplicate=True),
        Input("group-full-network-graph", "tapNodeData"),
        Input("group-to-group-network-graph", "tapNodeData"),
        prevent_initial_call=True,
    )
    def update_from_node_tap(tap_data, group_to_group_tap_data):
        """
        ノードクリック時にグループ選択、選択ソース、PEP入力欄を更新する

        Args:
            tap_data: Full Networkグラフでクリックされたノードのデータ
            group_to_group_tap_data: Group-to-Groupグラフでクリックされたノードのデータ

        Returns:
            tuple: (グループID, 選択ソース, PEP番号)
        """
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update

        triggered_id = ctx.triggered[0]["prop_id"]

        # Group-to-Group Networkのノードがタップされた場合
        if "group-to-group-network-graph" in triggered_id:
            if group_to_group_tap_data is not None:
                group_id = group_to_group_tap_data.get("group_id")
                if group_id is not None:
                    # PEP入力欄はクリア（グループノードにはPEP番号がないため）
                    return group_id, "dropdown", ""
            return no_update, no_update, no_update

        # Full Networkのノードがタップされた場合
        if "group-full-network-graph" in triggered_id:
            if tap_data is not None:
                group_id = tap_data.get("group_id")
                pep_number = tap_data.get("pep_number")

                if group_id is not None:
                    # PEP番号を文字列に変換（入力欄に表示するため）
                    pep_input_value = str(pep_number) if pep_number is not None else ""
                    return group_id, "node_tap", pep_input_value

        return no_update, no_update, no_update

    # ===== 隣接グループボタンクリック → グループ選択更新（サーバーサイド） =====
    @app.callback(
        Output("group-selector-dropdown", "value", allow_duplicate=True),
        Output("group-selection-source", "data", allow_duplicate=True),
        Output("group-pep-input", "value", allow_duplicate=True),
        Input(
            {"type": "adjacent-group-button", "group_id": ALL, "direction": ALL},
            "n_clicks",
        ),
        prevent_initial_call=True,
    )
    def update_from_adjacent_group_click(n_clicks_list):
        """
        隣接グループボタンクリック時にグループ選択を更新する

        Args:
            n_clicks_list: 各ボタンのクリック数リスト

        Returns:
            tuple: (グループID, 選択ソース, PEP入力欄の値)
        """
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update

        # ctx.triggered_id を使用（Dash推奨パターン）
        # pattern-matching callbacks では辞書として返される
        triggered_id = ctx.triggered_id
        if triggered_id and isinstance(triggered_id, dict):
            if triggered_id.get("type") == "adjacent-group-button":
                # 実際にクリックがあった場合のみ処理（value が 1 以上）
                value = ctx.triggered[0].get("value")
                if value is not None and value >= 1:
                    group_id = triggered_id.get("group_id")
                    if group_id is not None:
                        return group_id, "dropdown", ""

        return no_update, no_update, no_update

    # ===== テーブル内グループバッジクリック → グループ選択更新（サーバーサイド） =====
    @app.callback(
        Output("group-selector-dropdown", "value", allow_duplicate=True),
        Output("group-selection-source", "data", allow_duplicate=True),
        Output("group-pep-input", "value", allow_duplicate=True),
        Input("group-pep-table", "cellRendererData"),
        prevent_initial_call=True,
    )
    def update_from_table_group_badge_click(cell_renderer_data):
        """
        テーブル内のグループバッジクリック時にグループ選択を更新する

        Args:
            cell_renderer_data: セルレンダラーからのデータ
                - value: {"groupId": int, "field": str}

        Returns:
            tuple: (グループID, 選択ソース, PEP入力欄の値)
        """
        if cell_renderer_data is None:
            return no_update, no_update, no_update

        value = cell_renderer_data.get("value")
        if value is None:
            return no_update, no_update, no_update

        group_id = value.get("groupId")
        if group_id is not None:
            return group_id, "dropdown", ""

        return no_update, no_update, no_update

    # ===== グループ選択 → スタイルシート切り替え（クライアントサイド） =====
    # NOTE: このコールバックでは selection_source を変更しない
    # selection_source の管理は update_group_from_pep_input で行う
    # これにより、コールバック間の競合状態を回避する
    app.clientside_callback(
        f"""
        function(selectedGroup, selectionSource, elements, pepInput) {{
            // 基本スタイルシート（共通部分 + 選択スタイル）
            var baseStylesheet = {_FULL_NETWORK_BASE_STYLES_JS}.concat(
                {_FULL_NETWORK_SELECTION_STYLES_JS}
            );

            // 赤枠を非表示にするオーバーライドスタイル（共通部分 + pep-highlighted用）
            var overrideStyles = {_FULL_NETWORK_OVERRIDE_STYLES_JS}.concat(
                {_FULL_NETWORK_PEP_HIGHLIGHTED_OVERRIDE_STYLES_JS}
            );

            // "all"または未選択の場合は基本スタイルシート + 選択状態の赤枠を非表示
            if (selectedGroup === null || selectedGroup === undefined || selectedGroup === 'all') {{
                return baseStylesheet.concat(overrideStyles);
            }}

            // ノードタップからの選択: 赤枠を表示（基本スタイルシート）
            if (selectionSource === 'node_tap') {{
                return baseStylesheet;
            }}

            // PEP番号入力からの選択の場合、PEP入力値のグループIDと選択グループIDを比較
            if (selectionSource === 'pep_input') {{
                // PEP入力値が有効かチェック
                if (pepInput && pepInput !== '') {{
                    var pepNumber = parseInt(pepInput, 10);
                    if (!isNaN(pepNumber)) {{
                        var pepNodeId = 'pep_' + pepNumber;
                        var selectedGroupId = parseInt(selectedGroup, 10);

                        // elementsからPEP入力値に対応するノードのグループIDを取得
                        var pepGroupId = null;
                        if (elements) {{
                            for (var i = 0; i < elements.length; i++) {{
                                var el = elements[i];
                                var data = el.data || {{}};
                                if (data.id === pepNodeId && data.group_id !== undefined) {{
                                    pepGroupId = data.group_id;
                                    break;
                                }}
                            }}
                        }}

                        // PEP入力値のグループIDと選択グループIDが一致する場合のみ赤枠を維持
                        if (pepGroupId !== null && pepGroupId === selectedGroupId) {{
                            // :selectedの赤枠を非表示、pep-highlightedクラスで赤枠表示
                            // overrideStylesから:selectedのみを除外（.pep-highlightedの赤枠は維持）
                            var pepInputOverrideStyles = [
                                {{
                                    selector: '.group-selected:selected',
                                    style: {{
                                        'border-width': 2,
                                        'border-color': '#333',
                                        'opacity': 1,
                                        'text-outline-width': {TEXT_OUTLINE_WIDTH},
                                        'text-outline-color': '{TEXT_OUTLINE_COLOR}'
                                    }}
                                }},
                                {{
                                    selector: '.group-faded:selected',
                                    style: {{
                                        'border-width': 1,
                                        'border-color': '#999',
                                        'opacity': 0.15,
                                        'text-outline-width': {TEXT_OUTLINE_WIDTH},
                                        'text-outline-color': '{TEXT_OUTLINE_COLOR}'
                                    }}
                                }}
                            ];
                            return baseStylesheet.concat(pepInputOverrideStyles);
                        }}
                    }}
                }}
                // グループIDが一致しない場合は赤枠を非表示
                return baseStylesheet.concat(overrideStyles);
            }}

            // ドロップダウンからの選択: 赤枠を非表示
            return baseStylesheet.concat(overrideStyles);
        }}
        """,
        Output("group-full-network-graph", "stylesheet"),
        Input("group-selector-dropdown", "value"),
        State("group-selection-source", "data"),
        State("group-full-network-graph", "elements"),
        State("group-pep-input", "value"),
        prevent_initial_call=True,
    )

    # ===== PEP番号入力 → グループ選択 + 選択ソース更新 + エラーメッセージ更新（サーバーサイド） =====
    @app.callback(
        Output("group-selector-dropdown", "value", allow_duplicate=True),
        Output("group-selection-source", "data", allow_duplicate=True),
        Output("group-pep-error-message", "children"),
        Input("group-pep-input", "value"),
        State("group-selection-source", "data"),
        prevent_initial_call=True,
    )
    def update_group_from_pep_input(pep_input, selection_source):
        """
        PEP番号入力に連動してグループを選択する
        選択ソースを'pep_input'に設定してノードタップと同様の挙動にする

        Args:
            pep_input: 入力されたPEP番号（str, int または None）
            selection_source: 選択ソース ("dropdown", "node_tap", "pep_input")

        Returns:
            tuple: (グループID or no_update, 選択ソース or no_update, エラーメッセージ)
        """
        # ノードタップからの更新の場合は selection_source をリセットして終了
        # （グループ選択は既にノードタップ側で処理済み）
        # NOTE: スタイルシートコールバックでは selection_source を変更しないため、
        # ここでリセットすることで次のドロップダウン操作が正しく動作する
        if selection_source == "node_tap":
            return no_update, "dropdown", ""

        # 入力値を整数に変換
        pep_number = parse_pep_number(pep_input)

        # 入力が空/Noneの場合: 何もしない
        if pep_number is None:
            return no_update, no_update, ""

        # PEPの存在確認
        pep_data = get_pep_by_number(pep_number)
        if pep_data is None:
            error_message = f"Not Found: PEP {pep_number}"
            return no_update, no_update, error_message

        # グループIDを取得
        group_id = get_group_id_by_pep(pep_number)
        if group_id is None:
            error_message = f"Not Found: PEP {pep_number}"
            return no_update, no_update, error_message

        # グループを選択（ドロップダウンの値を更新）
        # 選択ソースを'pep_input'に設定（ノードタップと同様に赤枠表示するため）
        return group_id, "pep_input", ""

    # ===== PEP番号入力 → PEP情報更新（サーバーサイド） =====
    @app.callback(
        Output("group-pep-info-display", "children", allow_duplicate=True),
        Input("group-pep-input", "value"),
        State("group-selection-source", "data"),
        prevent_initial_call=True,
    )
    def update_pep_info_from_input(pep_input, selection_source):
        """
        PEP番号入力に連動してPEP情報を更新する

        Args:
            pep_input: 入力されたPEP番号（str, int または None）
            selection_source: 選択ソース ("dropdown", "node_tap", "pep_input")

        Returns:
            html.Div: PEP情報表示コンテンツ
        """
        # ノードタップからの更新の場合は何もしない（既にノードタップ側で処理済み）
        if selection_source == "node_tap":
            return no_update

        # 入力値を整数に変換
        pep_number = parse_pep_number(pep_input)

        # 入力が空/Noneの場合: 初期メッセージを表示
        if pep_number is None:
            return create_group_initial_info_message()

        # PEPの存在確認
        pep_data = get_pep_by_number(pep_number)
        if pep_data is None:
            return create_group_initial_info_message()

        return create_pep_info_display(pep_data)

    # ===== ネットワークタブ切り替え（クライアントサイド） =====
    # visibility/positionベースの切り替えでCytoscapeのレイアウト計算を維持
    app.clientside_callback(
        """
        function(fullClicks, groupClicks, groupToGroupClicks) {
            // どのボタンがクリックされたかを判定
            const ctx = window.dash_clientside.callback_context;

            // 表示タブのスタイル（通常表示）
            const visibleContentStyle = {
                'visibility': 'visible',
                'position': 'relative',
                'zIndex': '1'
            };

            // 非表示タブのスタイル（見えないが高さを持つ）
            const hiddenContentStyle = {
                'visibility': 'hidden',
                'position': 'absolute',
                'top': '0',
                'left': '0',
                'right': '0',
                'zIndex': '0'
            };

            // 選択されたタブボタンのスタイル
            const selectedButtonStyle = {
                'padding': '8px 16px',
                'border': '1px solid #ddd',
                'borderTop': '6px solid #DDAD3E',
                'borderBottom': '1px solid #fff',
                'backgroundColor': '#fff',
                'cursor': 'pointer',
                'marginRight': '4px',
                'borderRadius': '4px 4px 0 0',
                'fontWeight': 'bold',
                'marginBottom': '-1px'
            };

            // 非選択タブボタンのスタイル
            const unselectedButtonStyle = {
                'padding': '8px 16px',
                'border': '1px solid #ddd',
                'borderBottom': 'none',
                'backgroundColor': '#f5f5f5',
                'cursor': 'pointer',
                'marginRight': '4px',
                'borderRadius': '4px 4px 0 0'
            };

            if (!ctx.triggered || ctx.triggered.length === 0) {
                // 初期状態: Full Network表示
                return [
                    visibleContentStyle,
                    hiddenContentStyle,
                    hiddenContentStyle,
                    selectedButtonStyle,
                    unselectedButtonStyle,
                    unselectedButtonStyle
                ];
            }

            const triggeredId = ctx.triggered[0].prop_id.split('.')[0];

            if (triggeredId === 'full-network-tab-button') {
                return [
                    visibleContentStyle,
                    hiddenContentStyle,
                    hiddenContentStyle,
                    selectedButtonStyle,
                    unselectedButtonStyle,
                    unselectedButtonStyle
                ];
            } else if (triggeredId === 'group-network-tab-button') {
                return [
                    hiddenContentStyle,
                    visibleContentStyle,
                    hiddenContentStyle,
                    unselectedButtonStyle,
                    selectedButtonStyle,
                    unselectedButtonStyle
                ];
            } else {
                // group-to-group-tab-button
                return [
                    hiddenContentStyle,
                    hiddenContentStyle,
                    visibleContentStyle,
                    unselectedButtonStyle,
                    unselectedButtonStyle,
                    selectedButtonStyle
                ];
            }
        }
        """,
        Output("full-network-content", "style"),
        Output("group-network-content", "style"),
        Output("group-to-group-content", "style"),
        Output("full-network-tab-button", "style"),
        Output("group-network-tab-button", "style"),
        Output("group-to-group-tab-button", "style"),
        Input("full-network-tab-button", "n_clicks"),
        Input("group-network-tab-button", "n_clicks"),
        Input("group-to-group-tab-button", "n_clicks"),
    )

    # ===== Full Networkタップ → Group Network選択解除（クライアントサイド） =====
    app.clientside_callback(
        """
        function(tapData, currentElements) {
            // tapDataがない、またはelementsがない場合は更新しない
            if (!tapData || !currentElements || currentElements.length === 0) {
                return window.dash_clientside.no_update;
            }
            // 全ノードのselectedをfalseにする
            return currentElements.map(function(el) {
                var newEl = JSON.parse(JSON.stringify(el));
                newEl.selected = false;
                return newEl;
            });
        }
        """,
        Output("group-subgraph-network-graph", "elements", allow_duplicate=True),
        Input("group-full-network-graph", "tapNodeData"),
        State("group-subgraph-network-graph", "elements"),
        prevent_initial_call=True,
    )

    # ===== Group Networkタップ → Full Network選択解除（クライアントサイド） =====
    # NOTE: elementsのselected=falseだけではCytoscapeの:selected状態は解除されない
    # そのため、下のスタイルシート更新コールバックで:selectedの見た目を上書きする
    app.clientside_callback(
        """
        function(tapData, currentElements) {
            // tapDataがない、またはelementsがない場合は更新しない
            if (!tapData || !currentElements || currentElements.length === 0) {
                return window.dash_clientside.no_update;
            }
            // 全ノードのselectedをfalseにする
            return currentElements.map(function(el) {
                var newEl = JSON.parse(JSON.stringify(el));
                newEl.selected = false;
                return newEl;
            });
        }
        """,
        Output("group-full-network-graph", "elements", allow_duplicate=True),
        Input("group-subgraph-network-graph", "tapNodeData"),
        State("group-full-network-graph", "elements"),
        prevent_initial_call=True,
    )

    # ===== Group Networkタップ → Full Networkスタイルシート更新（クライアントサイド） =====
    # Cytoscapeの:selected擬似クラスによる赤枠を非表示にする
    app.clientside_callback(
        f"""
        function(tapData, selectedGroup) {{
            // tapDataがない場合は更新しない
            if (!tapData) {{
                return window.dash_clientside.no_update;
            }}

            // 基本スタイルシート（共通部分のみ）
            var baseStylesheet = {_FULL_NETWORK_BASE_STYLES_JS};

            // :selectedの赤枠を非表示にするスタイル（共通部分のみ）
            var overrideStyles = {_FULL_NETWORK_OVERRIDE_STYLES_JS};

            return baseStylesheet.concat(overrideStyles);
        }}
        """,
        Output("group-full-network-graph", "stylesheet", allow_duplicate=True),
        Input("group-subgraph-network-graph", "tapNodeData"),
        State("group-selector-dropdown", "value"),
        prevent_initial_call=True,
    )

    # ===== Group Networkノードタップ → エッジハイライト更新（クライアントサイド） =====
    app.clientside_callback(
        """
        function(tapNodeData, currentElements) {
            // tapNodeDataまたはelementsがない場合は更新しない
            if (!tapNodeData || !currentElements || currentElements.length === 0) {
                return window.dash_clientside.no_update;
            }

            // タップされたノードのID
            var selectedNodeId = 'pep_' + tapNodeData.pep_number;

            // タップされたノードを探す
            var selectedNode = null;
            for (var i = 0; i < currentElements.length; i++) {
                if (currentElements[i].data && currentElements[i].data.id === selectedNodeId) {
                    selectedNode = currentElements[i];
                    break;
                }
            }

            // 選択ノードが見つからない場合は更新しない
            if (!selectedNode) {
                return window.dash_clientside.no_update;
            }

            // 隣接情報を取得
            var adjacentNodes = selectedNode.data.adjacent_nodes || [];
            var incomingEdges = selectedNode.data.incoming_edges || [];
            var outgoingEdges = selectedNode.data.outgoing_edges || [];

            // セットに変換（高速検索用）
            var adjacentNodesSet = new Set(adjacentNodes);
            var incomingEdgesSet = new Set(incomingEdges);
            var outgoingEdgesSet = new Set(outgoingEdges);

            // elementsを更新
            return currentElements.map(function(el) {
                var newEl = JSON.parse(JSON.stringify(el));
                var data = newEl.data;

                // ノードの場合
                if (!data.source) {
                    if (data.id === selectedNodeId) {
                        newEl.classes = 'selected';
                    } else if (adjacentNodesSet.has(data.id)) {
                        newEl.classes = 'connected';
                    } else {
                        newEl.classes = 'faded';
                    }
                }
                // エッジの場合
                else {
                    if (incomingEdgesSet.has(data.id)) {
                        newEl.classes = 'incoming-edge';
                    } else if (outgoingEdgesSet.has(data.id)) {
                        newEl.classes = 'outgoing-edge';
                    } else {
                        newEl.classes = 'faded';
                    }
                }

                return newEl;
            });
        }
        """,
        Output("group-subgraph-network-graph", "elements", allow_duplicate=True),
        Input("group-subgraph-network-graph", "tapNodeData"),
        State("group-subgraph-network-graph", "elements"),
        prevent_initial_call=True,
    )

    # ===== Group Network背景クリック → ハイライト解除（クライアントサイド） =====
    # selectedNodeDataが空配列になったとき（背景クリック等）にハイライトを初期状態に戻す
    app.clientside_callback(
        """
        function(selectedNodeData, currentElements) {
            // elementsがない場合は更新しない
            if (!currentElements || currentElements.length === 0) {
                return window.dash_clientside.no_update;
            }

            // selectedNodeDataが空配列の場合（ノード選択解除 = 背景クリック等）
            if (!selectedNodeData || selectedNodeData.length === 0) {
                // 全elementsのclassesをクリアして初期状態に戻す
                return currentElements.map(function(el) {
                    var newEl = JSON.parse(JSON.stringify(el));
                    newEl.classes = '';
                    return newEl;
                });
            }

            // ノードが選択されている場合は更新しない（tapNodeDataのコールバックで処理）
            return window.dash_clientside.no_update;
        }
        """,
        Output("group-subgraph-network-graph", "elements", allow_duplicate=True),
        Input("group-subgraph-network-graph", "selectedNodeData"),
        State("group-subgraph-network-graph", "elements"),
        prevent_initial_call=True,
    )

    # ===== グループ選択 → Group-to-Group Networkハイライト更新（クライアントサイド） =====
    # ドロップダウンやFull Networkタップでグループが選択されたときに
    # Group-to-Group Networkの該当ノードをハイライトする
    app.clientside_callback(
        """
        function(selectedGroup, currentElements) {
            // elementsがない場合は更新しない
            if (!currentElements || currentElements.length === 0) {
                return window.dash_clientside.no_update;
            }

            // "all"または未選択の場合は全要素のハイライトをクリア
            if (selectedGroup === null || selectedGroup === undefined || selectedGroup === 'all') {
                return currentElements.map(function(el) {
                    var newEl = JSON.parse(JSON.stringify(el));
                    newEl.classes = '';
                    newEl.selected = false;
                    return newEl;
                });
            }

            // 選択されたグループIDを数値に変換
            var selectedGroupId = parseInt(selectedGroup, 10);
            var selectedNodeId = 'group_' + selectedGroupId;

            // 選択されたノードを探す
            var selectedNode = null;
            for (var i = 0; i < currentElements.length; i++) {
                if (currentElements[i].data && currentElements[i].data.id === selectedNodeId) {
                    selectedNode = currentElements[i];
                    break;
                }
            }

            // 選択ノードが見つからない場合はハイライトをクリア
            if (!selectedNode) {
                return currentElements.map(function(el) {
                    var newEl = JSON.parse(JSON.stringify(el));
                    newEl.classes = '';
                    newEl.selected = false;
                    return newEl;
                });
            }

            // 隣接情報を取得
            var adjacentNodes = selectedNode.data.adjacent_nodes || [];
            var incomingEdges = selectedNode.data.incoming_edges || [];
            var outgoingEdges = selectedNode.data.outgoing_edges || [];

            // セットに変換（高速検索用）
            var adjacentNodesSet = new Set(adjacentNodes);
            var incomingEdgesSet = new Set(incomingEdges);
            var outgoingEdgesSet = new Set(outgoingEdges);

            // elementsを更新
            return currentElements.map(function(el) {
                var newEl = JSON.parse(JSON.stringify(el));
                var data = newEl.data;

                // ノードの場合
                if (!data.source) {
                    if (data.id === selectedNodeId) {
                        newEl.classes = 'selected';
                        newEl.selected = true;
                    } else if (adjacentNodesSet.has(data.id)) {
                        newEl.classes = 'connected';
                        newEl.selected = false;
                    } else {
                        newEl.classes = 'faded';
                        newEl.selected = false;
                    }
                }
                // エッジの場合
                else {
                    if (incomingEdgesSet.has(data.id)) {
                        newEl.classes = 'incoming-edge';
                    } else if (outgoingEdgesSet.has(data.id)) {
                        newEl.classes = 'outgoing-edge';
                    } else {
                        newEl.classes = 'faded';
                    }
                }

                return newEl;
            });
        }
        """,
        Output("group-to-group-network-graph", "elements", allow_duplicate=True),
        Input("group-selector-dropdown", "value"),
        State("group-to-group-network-graph", "elements"),
        prevent_initial_call=True,
    )

    # ===== Group-to-Group Networkノードタップ → エッジハイライト更新（クライアントサイド） =====
    app.clientside_callback(
        """
        function(tapNodeData, currentElements) {
            // tapNodeDataまたはelementsがない場合は更新しない
            if (!tapNodeData || !currentElements || currentElements.length === 0) {
                return window.dash_clientside.no_update;
            }

            // タップされたノードのID
            var selectedNodeId = 'group_' + tapNodeData.group_id;

            // タップされたノードを探す
            var selectedNode = null;
            for (var i = 0; i < currentElements.length; i++) {
                if (currentElements[i].data && currentElements[i].data.id === selectedNodeId) {
                    selectedNode = currentElements[i];
                    break;
                }
            }

            // 選択ノードが見つからない場合は更新しない
            if (!selectedNode) {
                return window.dash_clientside.no_update;
            }

            // 隣接情報を取得
            var adjacentNodes = selectedNode.data.adjacent_nodes || [];
            var incomingEdges = selectedNode.data.incoming_edges || [];
            var outgoingEdges = selectedNode.data.outgoing_edges || [];

            // セットに変換（高速検索用）
            var adjacentNodesSet = new Set(adjacentNodes);
            var incomingEdgesSet = new Set(incomingEdges);
            var outgoingEdgesSet = new Set(outgoingEdges);

            // elementsを更新
            return currentElements.map(function(el) {
                var newEl = JSON.parse(JSON.stringify(el));
                var data = newEl.data;

                // ノードの場合
                if (!data.source) {
                    if (data.id === selectedNodeId) {
                        newEl.classes = 'selected';
                    } else if (adjacentNodesSet.has(data.id)) {
                        newEl.classes = 'connected';
                    } else {
                        newEl.classes = 'faded';
                    }
                }
                // エッジの場合
                else {
                    if (incomingEdgesSet.has(data.id)) {
                        newEl.classes = 'incoming-edge';
                    } else if (outgoingEdgesSet.has(data.id)) {
                        newEl.classes = 'outgoing-edge';
                    } else {
                        newEl.classes = 'faded';
                    }
                }

                return newEl;
            });
        }
        """,
        Output("group-to-group-network-graph", "elements", allow_duplicate=True),
        Input("group-to-group-network-graph", "tapNodeData"),
        State("group-to-group-network-graph", "elements"),
        prevent_initial_call=True,
    )

    # ===== Group-to-Group Network背景クリック → ハイライト解除（クライアントサイド） =====
    app.clientside_callback(
        """
        function(selectedNodeData, currentElements) {
            // elementsがない場合は更新しない
            if (!currentElements || currentElements.length === 0) {
                return window.dash_clientside.no_update;
            }

            // selectedNodeDataが空配列の場合（ノード選択解除 = 背景クリック等）
            if (!selectedNodeData || selectedNodeData.length === 0) {
                // 全elementsのclassesをクリアして初期状態に戻す
                return currentElements.map(function(el) {
                    var newEl = JSON.parse(JSON.stringify(el));
                    newEl.classes = '';
                    return newEl;
                });
            }

            // ノードが選択されている場合は更新しない（tapNodeDataのコールバックで処理）
            return window.dash_clientside.no_update;
        }
        """,
        Output("group-to-group-network-graph", "elements", allow_duplicate=True),
        Input("group-to-group-network-graph", "selectedNodeData"),
        State("group-to-group-network-graph", "elements"),
        prevent_initial_call=True,
    )
