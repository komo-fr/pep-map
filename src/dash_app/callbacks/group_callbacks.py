"""Groupタブのコールバック関数"""

import pandas as pd
from dash import Input, Output, State, callback_context, no_update, html
from src.dash_app.components.pep_info import (
    create_group_initial_info_message,
    create_pep_info_display,
)
from src.dash_app.components import parse_pep_number
from src.dash_app.utils.constants import TEXT_OUTLINE_COLOR, TEXT_OUTLINE_WIDTH
from src.dash_app.utils.data_loader import (
    get_peps_by_group,
    get_pep_by_number,
    get_group_id_by_pep,
    generate_pep_url,
    get_group_name_info,
)


def register_group_callbacks(app):
    """
    Groupタブのコールバックを登録する

    Args:
        app: Dashアプリケーションインスタンス
    """

    # ===== ノードタップ → PEP情報更新（サーバーサイド） =====
    @app.callback(
        Output("group-pep-info-display", "children"),
        Input("group-network-graph", "tapNodeData"),
        Input("group-network-graph", "selectedNodeData"),
        Input("group-selector-dropdown", "value"),
        State("group-selection-source", "data"),
    )
    def update_pep_info_from_tap(
        tap_data, selected_data, selected_group, selection_source
    ):
        """
        ノードタップ時にPEP情報を更新する
        選択が解除された場合やグループが変更された場合は初期メッセージを表示する

        Args:
            tap_data: クリックされたノードのデータ
            selected_data: 選択されているノードのリスト
            selected_group: 選択されているグループ
            selection_source: 選択ソース ("dropdown", "node_tap", "pep_input")

        Returns:
            html.Div: PEP情報表示コンテンツ
        """
        # どの Input がトリガーしたかを判断
        ctx = callback_context
        if ctx.triggered:
            triggered_id = ctx.triggered[0]["prop_id"]
            # ドロップダウンが変更された場合
            if "group-selector-dropdown" in triggered_id:
                # PEP番号入力またはノードタップからのトリガーの場合は、
                # それぞれのコールバックに任せる
                if selection_source == "pep_input" or selection_source == "node_tap":
                    return no_update
                # それ以外（ドロップダウン直接操作）は初期メッセージを表示
                return create_group_initial_info_message()

        # 選択されているノードがない場合は初期メッセージを表示
        if not selected_data:
            return create_group_initial_info_message()

        if tap_data is None:
            return create_group_initial_info_message()

        pep_number = tap_data.get("pep_number")
        if pep_number is None:
            return create_group_initial_info_message()

        pep_data = get_pep_by_number(pep_number)
        if pep_data is None:
            return create_group_initial_info_message()

        return create_pep_info_display(pep_data)

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
        Output("group-network-graph", "elements"),
        Input("group-selector-dropdown", "value"),
        State("group-network-graph", "elements"),
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
        Input("group-selector-dropdown", "value"),
    )
    def update_group_table(selected_group):
        """
        グループ選択時にテーブルデータ、タイトル、グループ名、説明を更新する

        Args:
            selected_group: 選択されたグループ（"all" または グループID）

        Returns:
            tuple: (テーブルデータ, タイトル, グループ名, グループ説明, 説明スタイル)
        """
        # 説明文が空の時のスタイル（非表示）
        empty_style = {"display": "none"}

        # 説明文がある時のスタイル（背景色付き）
        filled_style = {
            "fontSize": "13px",
            "color": "#333",
            "marginBottom": "8px",
            "marginTop": "0",
            "lineHeight": "1.5",
            "backgroundColor": "#EAEAEA",
            "padding": "8px",
            "borderRadius": "4px",
        }

        if selected_group is None or selected_group == "all":
            return [], "Select a group to view PEPs", "", "", empty_style

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
            # 説明文とNoteを含むコンテンツを生成
            description_children = [
                html.P(
                    group_description,
                    style={
                        "margin": "0 0 8px 0",
                        "fontSize": "13px",
                        "color": "#333",
                        "whiteSpace": "pre-line",
                    },
                ),
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
                        "marginTop": "8px",
                        "borderRadius": "4px",
                    },
                ),
            ]
            description_style = filled_style

        if df.empty:
            if group_id == -1:
                title = "Isolated PEPs (no data)"
            else:
                title = f"Group {group_id} (no data)"
            return [], title, group_name, description_children, description_style

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

        # テーブルデータに変換
        table_data = []
        for _, row in df.iterrows():
            pep_num = int(row["PEP"])
            pep_url = generate_pep_url(pep_num)
            # 日付をフォーマット（YYYY-MM-DD）
            created_str = row["created"] if pd.notna(row["created"]) else ""
            table_data.append(
                {
                    "pep": f"[PEP {pep_num}]({pep_url})",
                    "title": row["title"],
                    "status": row["status"],
                    "created": created_str,
                    "in_degree": int(row["in-degree_group"]),
                    "out_degree": int(row["out-degree_group"]),
                    "degree": int(row["degree_group"]),
                    "pagerank": f"{row['pagerank_group']:.4f}",
                }
            )

        # タイトルを設定
        count = len(table_data)
        if group_id == -1:
            title = f"Isolated PEPs ({count} PEPs)"
        else:
            title = f"Group {group_id} ({count} PEPs)"

        return table_data, title, group_name, description_children, description_style

    # ===== ノードクリック → グループ選択更新 + 選択ソース更新 + PEP入力欄更新（サーバーサイド） =====
    @app.callback(
        Output("group-selector-dropdown", "value", allow_duplicate=True),
        Output("group-selection-source", "data", allow_duplicate=True),
        Output("group-pep-input", "value", allow_duplicate=True),
        Input("group-network-graph", "tapNodeData"),
        prevent_initial_call=True,
    )
    def update_from_node_tap(tap_data):
        """
        ノードクリック時にグループ選択、選択ソース、PEP入力欄を更新する

        Args:
            tap_data: クリックされたノードのデータ

        Returns:
            tuple: (グループID, 選択ソース, PEP番号)
        """
        if tap_data is None:
            return no_update, no_update, no_update

        group_id = tap_data.get("group_id")
        pep_number = tap_data.get("pep_number")

        if group_id is not None:
            # PEP番号を文字列に変換（入力欄に表示するため）
            pep_input_value = str(pep_number) if pep_number is not None else ""
            return group_id, "node_tap", pep_input_value

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
        Output("group-network-graph", "stylesheet"),
        Input("group-selector-dropdown", "value"),
        State("group-selection-source", "data"),
        State("group-network-graph", "elements"),
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
