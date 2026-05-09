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
from src.dash_app.layouts.group_tab import _create_subgraph_placeholder_with_dummy
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
)


# PEP番号とメタデータのキャッシュ
_pep_numbers_cache: set[int] | None = None
_pep_metadata_cache: dict[int, dict[str, str]] | None = None


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

    # ===== ドロップダウン直接操作 → 初期メッセージ表示（サーバーサイド） =====
    @app.callback(
        Output("group-pep-info-display", "children", allow_duplicate=True),
        Input("group-selector-dropdown", "value"),
        State("group-selection-source", "data"),
        prevent_initial_call=True,
    )
    def update_pep_info_from_dropdown(selected_group, selection_source):
        """
        ドロップダウン直接操作時に初期メッセージを表示する

        Args:
            selected_group: 選択されているグループ
            selection_source: 選択ソース ("dropdown", "node_tap", "pep_input")

        Returns:
            html.Div: 初期メッセージまたは no_update
        """
        # PEP番号入力またはノードタップからのトリガーの場合は何もしない
        if selection_source == "pep_input" or selection_source == "node_tap":
            return no_update
        # ドロップダウン直接操作の場合は初期メッセージを表示
        return create_group_initial_info_message()

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

    # ===== グループ選択 → テーブルデータ更新（サーバーサイド） =====
    @app.callback(
        Output("group-pep-table", "data"),
        Output("group-pep-table-title", "children"),
        Output("group-name-display", "children"),
        Output("group-description-display", "children"),
        Output("group-description-display", "style"),
        Output("adjacent-groups-display", "children"),
        Output("adjacent-groups-display", "style"),
        Input("group-selector-dropdown", "value"),
    )
    def update_group_table(selected_group):
        """
        グループ選択時にテーブルデータ、タイトル、グループ名、説明、隣接グループを更新する

        Args:
            selected_group: 選択されたグループ（"all" または グループID）

        Returns:
            tuple: (テーブルデータ, タイトル, グループ名, グループ説明, 説明スタイル,
                    隣接グループ, 隣接グループスタイル)
        """
        # 説明文が空の時のスタイル（非表示）
        empty_style = {"display": "none"}

        # 説明文がある時のスタイル（背景色付き）
        filled_style = {
            "marginBottom": "8px",
            "marginTop": "0",
            "backgroundColor": "#EAEAEA",
            "padding": "8px",
            "borderRadius": "4px",
        }

        if selected_group is None or selected_group == "all":
            return (
                [],
                "Select a group to view PEPs",
                "",
                "",
                empty_style,
                "",
                empty_style,
            )

        group_id = int(selected_group)
        df = get_peps_by_group(group_id)

        # グループ名と説明を取得
        group_info = get_group_name_info(group_id)
        group_name = group_info["group_name"]
        group_description = group_info["description"]

        # 説明文が空かどうかでスタイルと内容を切り替え
        if not group_description:
            description_children = ""
            description_style = empty_style
        else:
            # 段落を分割（空行で区切る）
            paragraphs = group_description.split("\n\n")
            first_paragraph = paragraphs[0]
            last_paragraph = paragraphs[-1] if len(paragraphs) > 1 else None
            # 中間段落（第2・第3段落）を折りたたみ対象とする
            middle_paragraphs = paragraphs[1:-1] if len(paragraphs) > 2 else []

            # 注意書き（常に表示） + 説明文を生成
            description_children = [
                # 注意書き（常に表示、上部）
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
                        "padding": "8px",
                        "marginBottom": "8px",
                        "borderRadius": "4px",
                    },
                ),
                # 最初の段落（常に表示）
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

            # 中間段落があれば折りたたみで追加
            if middle_paragraphs:
                middle_text = "\n\n".join(middle_paragraphs)
                description_children.append(
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
                                    "listStyle": "none",  # デフォルトの三角マーカーを非表示
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

            # 最終段落（常に表示）
            if last_paragraph:
                description_children.append(
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

            description_style = filled_style

        # 隣接グループ情報を取得
        adjacent_info = get_adjacent_groups(group_id)
        citing_groups = adjacent_info["citing_groups"]
        cited_groups = adjacent_info["cited_groups"]

        # 隣接グループ表示コンポーネントを作成
        adjacent_style = {
            "marginBottom": "8px",
            "marginTop": "0",
            "backgroundColor": "#F5F5F5",
            "padding": "12px",
            "borderRadius": "4px",
        }

        # グループボタンのスタイル
        button_style = {
            "display": "inline-block",
            "padding": "4px 10px",
            "margin": "2px 4px 2px 0",
            "backgroundColor": "#E8E8E8",
            "border": "1px solid #CCC",
            "borderRadius": "16px",
            "fontSize": "12px",
            "cursor": "pointer",
            "color": "#333",
        }

        def create_group_button_with_tooltip(grp_id: int, weight: int, direction: str):
            """ツールチップ付きのグループボタンを作成

            Args:
                grp_id: グループID
                weight: 引用数
                direction: "citing" または "cited"（IDの一意性のため）
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

        adjacent_children = []

        # 選択中のグループを引用しているグループ
        if citing_groups:
            citing_buttons = []
            for grp_id, weight in citing_groups:
                citing_buttons.append(
                    create_group_button_with_tooltip(grp_id, weight, "citing")
                )
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
        adjacent_children.append(
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
            )
        )

        # 選択中のグループが引用しているグループ
        if cited_groups:
            cited_buttons = []
            for grp_id, weight in cited_groups:
                cited_buttons.append(
                    create_group_button_with_tooltip(grp_id, weight, "cited")
                )
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
        adjacent_children.append(
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
            )
        )

        if df.empty:
            title = f"Group {group_id} (no data)"
            return (
                [],
                title,
                group_name,
                description_children,
                description_style,
                adjacent_children,
                adjacent_style,
            )

        # ソート: PageRank降順 > In-degree降順 > Out-degree降順 > Degree降順 > PEP番号昇順
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

        # テーブルデータに変換（pandasを使って効率的に処理）
        # created列を文字列にフォーマット（日付型への変換はload_group_dataで実施済み）
        df["created_str"] = df["created"].dt.strftime("%Y-%m-%d").fillna("")

        # PEP列にMarkdownリンクを追加
        df["pep_markdown"] = df["PEP"].apply(
            lambda pep_num: f"[PEP {pep_num}]({generate_pep_url(pep_num)})"
        )

        # PageRank列をフォーマット
        df["pagerank_str"] = df["pagerank_group"].apply(lambda x: f"{x:.4f}")

        # テーブルデータ用の辞書リストを作成
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

        # タイトルを設定
        count = len(table_data)
        title = f"Group {group_id} ({count} PEPs)"

        return (
            table_data,
            title,
            group_name,
            description_children,
            description_style,
            adjacent_children,
            adjacent_style,
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

        # ctx.triggered から実際にクリックがあったボタンを探す
        for triggered in ctx.triggered:
            value = triggered.get("value")
            # 実際にクリックがあった場合のみ処理（value が 1 以上）
            if value is not None and value >= 1:
                # prop_id から group_id を抽出
                prop_id = triggered.get("prop_id", "")
                # prop_id の形式:
                # {"direction":"citing","group_id":7,"type":"adjacent-group-button"}.n_clicks
                if "adjacent-group-button" in prop_id:
                    import json

                    try:
                        # .n_clicks を除去してJSONをパース
                        id_json = prop_id.rsplit(".", 1)[0]
                        id_dict = json.loads(id_json)
                        group_id = id_dict.get("group_id")
                        if group_id is not None:
                            return group_id, "dropdown", ""
                    except (json.JSONDecodeError, IndexError):
                        pass

        return no_update, no_update, no_update

    # ===== グループ選択 → スタイルシート切り替え（クライアントサイド） =====
    # NOTE: このコールバックでは selection_source を変更しない
    # selection_source の管理は update_group_from_pep_input で行う
    # これにより、コールバック間の競合状態を回避する
    app.clientside_callback(
        f"""
        function(selectedGroup, selectionSource, elements, pepInput) {{
            // 基本スタイルシート
            var baseStylesheet = [
                // ノード基本スタイル
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
                // エッジ基本スタイル
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
                // グループ選択時のハイライト
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
                // グループ選択時の非選択ノード（減衰）
                {{
                    selector: '.group-faded',
                    style: {{
                        'opacity': 0.15
                    }}
                }},
                // グループ選択時のエッジ（グループ内のエッジ）
                {{
                    selector: '.group-selected-edge',
                    style: {{
                        'opacity': 1,
                        'line-color': '#666',
                        'target-arrow-color': '#666',
                        'width': 2
                    }}
                }},
                // ノードタップ時の選択スタイル
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
                // PEP番号入力からの選択スタイル（pep-highlightedクラス）
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
            ];

            // 赤枠を非表示にするオーバーライドスタイル
            var overrideStyles = [
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
                }},
                // pep-highlightedクラスの赤枠も非表示にする
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
            ];

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

    # ===== ドロップダウン変更 → selection_source・PEP入力欄リセット（サーバーサイド） =====
    @app.callback(
        Output("group-selection-source", "data", allow_duplicate=True),
        Output("group-pep-input", "value", allow_duplicate=True),
        Input("group-selector-dropdown", "value"),
        State("group-selection-source", "data"),
        State("group-pep-input", "value"),
        prevent_initial_call=True,
    )
    def reset_on_dropdown_change(selected_group, selection_source, pep_input):
        """
        ドロップダウンが変更された時に selection_source と PEP入力欄をリセットする

        ノードタップ/PEP入力からドロップダウンが更新された場合は何もしない（入力値を維持）
        ユーザーがドロップダウンを直接操作した場合はリセット（入力値をクリア）

        Args:
            selected_group: 選択されたグループ
            selection_source: 現在の選択ソース
            pep_input: PEP入力欄の値

        Returns:
            tuple: (selection_source, pep_input) or no_update
        """
        # PEP入力欄が空の場合は何もしない
        pep_number = parse_pep_number(pep_input)
        if pep_number is None:
            # selection_source が "pep_input" の場合のみリセット
            if selection_source == "pep_input":
                return "dropdown", no_update
            return no_update, no_update

        # PEP入力欄の値に対応するグループIDを取得
        target_group_id = get_group_id_by_pep(pep_number)
        if target_group_id is None:
            # 無効なPEP番号の場合はリセット
            if selection_source == "pep_input":
                return "dropdown", ""
            return no_update, ""

        # 現在のドロップダウンの値と対象グループIDが一致する場合は何もしない
        # （ノードタップ/PEP入力からの変更なので入力値を維持）
        if str(selected_group) == str(target_group_id):
            return no_update, no_update

        # 異なる場合はリセット（ユーザーがドロップダウンを操作した）
        if selection_source == "pep_input":
            return "dropdown", ""
        return no_update, ""

    # ===== グループ選択 → サブグラフ更新（サーバーサイド） =====
    @app.callback(
        Output("subgraph-container", "children"),
        Input("group-selector-dropdown", "value"),
    )
    def update_subgraph(selected_group):
        """
        グループ選択時にサブグラフを更新する

        Args:
            selected_group: 選択されたグループ（"all" または グループID）

        Returns:
            サブグラフコンポーネント または プレースホルダー（常にCytoscapeを含む）
        """
        # "all"または未選択の場合はプレースホルダーを表示
        if selected_group is None or selected_group == "all":
            return _create_subgraph_placeholder_with_dummy()

        # 孤立グループ(-1)の場合もプレースホルダーを表示
        group_id = int(selected_group)
        if group_id < 0:
            return _create_subgraph_placeholder_with_dummy()

        # サブグラフのelementsを構築
        elements = build_subgraph_cytoscape_elements(group_id)
        if elements is None:
            return _create_subgraph_placeholder_with_dummy()

        # Cytoscapeコンポーネントを返す
        return cyto.Cytoscape(
            id="group-subgraph-network-graph",
            elements=elements,
            layout=get_subgraph_layout_options(),
            style={
                "width": "100%",
                "height": "600px",
                "border": "1px solid #ddd",
                "backgroundColor": "#fafafa",
            },
            stylesheet=get_subgraph_base_stylesheet(),
        )

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

            // 基本スタイルシート
            var baseStylesheet = [
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
            ];

            // :selectedの赤枠を非表示にするスタイル
            var overrideStyles = [
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
            ];

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
                    newEl.selected = false;
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
