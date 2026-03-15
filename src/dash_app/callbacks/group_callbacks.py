"""Groupタブのコールバック関数"""

import copy

from dash import Input, Output, State, no_update
from src.dash_app.components.pep_info import (
    create_network_initial_info_message,
    create_pep_info_display,
)
from src.dash_app.utils.data_loader import (
    get_peps_by_group,
    get_pep_by_number,
    generate_pep_url,
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
    )
    def update_pep_info_from_tap(tap_data):
        """
        ノードタップ時にPEP情報を更新する

        Args:
            tap_data: クリックされたノードのデータ

        Returns:
            html.Div: PEP情報表示コンテンツ
        """
        if tap_data is None:
            return create_network_initial_info_message()

        pep_number = tap_data.get("pep_number")
        if pep_number is None:
            return create_network_initial_info_message()

        pep_data = get_pep_by_number(pep_number)
        if pep_data is None:
            return create_network_initial_info_message()

        return create_pep_info_display(pep_data)

    # ===== グループ選択 → グラフハイライト更新（サーバーサイド） =====
    @app.callback(
        Output("group-network-graph", "elements"),
        Input("group-selector-dropdown", "value"),
        State("group-network-graph", "elements"),
        prevent_initial_call=True,
    )
    def update_graph_highlight(selected_group, current_elements):
        """
        グループ選択時にグラフのハイライトを更新する
        """
        if current_elements is None:
            return no_update

        # "all"または未選択の場合は全ノードを通常表示
        if selected_group is None or selected_group == "all":
            new_elements = []
            for el in current_elements:
                new_el = copy.deepcopy(el)
                new_el["classes"] = ""
                new_el["selected"] = False  # ノードの選択状態をクリア
                new_elements.append(new_el)
            return new_elements

        # 選択されたグループIDを数値に変換
        selected_group_id = int(selected_group)

        # 選択グループに所属するノードIDのセットを作成
        selected_node_ids = set()
        for el in current_elements:
            data = el.get("data", {})
            if "source" not in data and data.get("group_id") == selected_group_id:
                selected_node_ids.add(data.get("id"))

        # elementsを更新
        new_elements = []
        for el in current_elements:
            new_el = copy.deepcopy(el)
            new_el["selected"] = False  # ノードの選択状態をクリア
            data = new_el.get("data", {})

            # ノードの場合
            if "source" not in data:
                node_group_id = data.get("group_id")
                if node_group_id == selected_group_id:
                    new_el["classes"] = "group-selected"
                else:
                    new_el["classes"] = "group-faded"
            # エッジの場合
            else:
                source = data.get("source")
                target = data.get("target")
                if source in selected_node_ids and target in selected_node_ids:
                    new_el["classes"] = "group-selected-edge"
                else:
                    new_el["classes"] = "group-faded"

            new_elements.append(new_el)

        return new_elements

    # ===== グループ選択 → テーブルデータ更新（サーバーサイド） =====
    @app.callback(
        Output("group-pep-table", "data"),
        Output("group-pep-table-title", "children"),
        Input("group-selector-dropdown", "value"),
    )
    def update_group_table(selected_group):
        """
        グループ選択時にテーブルデータとタイトルを更新する

        Args:
            selected_group: 選択されたグループ（"all" または グループID）

        Returns:
            tuple: (テーブルデータ, タイトル)
        """
        if selected_group is None or selected_group == "all":
            return [], "Select a group to view PEPs"

        group_id = int(selected_group)
        df = get_peps_by_group(group_id)

        if df.empty:
            if group_id == -1:
                title = "Isolated PEPs (no data)"
            else:
                title = f"Group {group_id} (no data)"
            return [], title

        # ソート: PageRank降順 > In-degree降順 > Out-degree降順 > Degree降順 > PEP番号昇順
        df = df.sort_values(
            by=["pagerank_group", "in-degree_group", "out-degree_group", "degree_group", "PEP"],
            ascending=[False, False, False, False, True],
        ).reset_index(drop=True)

        # テーブルデータに変換
        table_data = []
        for _, row in df.iterrows():
            pep_num = int(row["PEP"])
            pep_url = generate_pep_url(pep_num)
            table_data.append({
                "pep": f"[PEP {pep_num}]({pep_url})",
                "title": row["title"],
                "in_degree": int(row["in-degree_group"]),
                "out_degree": int(row["out-degree_group"]),
                "degree": int(row["degree_group"]),
                "pagerank": f"{row['pagerank_group']:.4f}",
            })

        # タイトルを設定
        count = len(table_data)
        if group_id == -1:
            title = f"Isolated PEPs ({count} PEPs)"
        else:
            title = f"Group {group_id} ({count} PEPs)"

        return table_data, title

    # ===== ノードクリック → グループ選択更新 + 選択ソース更新（サーバーサイド） =====
    @app.callback(
        Output("group-selector-dropdown", "value"),
        Output("group-selection-source", "data"),
        Input("group-network-graph", "tapNodeData"),
        prevent_initial_call=True,
    )
    def update_group_from_node_tap(tap_data):
        """
        ノードクリック時にそのグループを選択する

        Args:
            tap_data: クリックされたノードのデータ

        Returns:
            tuple: (グループID, 選択ソース)
        """
        if tap_data is None:
            return no_update, no_update

        group_id = tap_data.get("group_id")
        if group_id is not None:
            return group_id, "node_tap"

        return no_update, no_update

    # ===== グループ選択 → スタイルシート切り替え（サーバーサイド） =====
    @app.callback(
        Output("group-network-graph", "stylesheet"),
        Output("group-selection-source", "data", allow_duplicate=True),
        Input("group-selector-dropdown", "value"),
        State("group-selection-source", "data"),
        prevent_initial_call=True,
    )
    def update_stylesheet(selected_group, selection_source):
        """
        グループ選択時にスタイルシートを切り替える

        選択ソースに基づいてスタイルシートを選択し、使用後はソースをリセットする。
        - "node_tap": ノードタップからの選択 → 赤枠を表示
        - "dropdown": ドロップダウンからの選択 → 赤枠を非表示

        Args:
            selected_group: 選択されたグループ（"all" または グループID）
            selection_source: 選択ソース（"node_tap" または "dropdown"）

        Returns:
            tuple: (スタイルシート, リセットされた選択ソース)
        """
        from src.dash_app.components.group_network_graph import (
            get_group_base_stylesheet,
            get_group_selected_stylesheet,
        )

        if selected_group is None or selected_group == "all":
            return get_group_base_stylesheet(), "dropdown"

        # ノードタップからの選択: 赤枠を表示（基本スタイルシート）
        if selection_source == "node_tap":
            stylesheet = get_group_base_stylesheet()
        # ドロップダウンからの選択: 赤枠を非表示（選択スタイルシート）
        else:
            stylesheet = get_group_selected_stylesheet()

        # 使用後は "dropdown" にリセット（次の操作に備える）
        return stylesheet, "dropdown"
