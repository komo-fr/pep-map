"""Networkタブのコールバック関数"""

from dash import Input, Output, State, no_update, callback_context

from src.dash_app.components import (
    parse_pep_number,
    create_pep_info_display,
    create_network_initial_info_message,
    convert_df_to_table_data,
    get_base_stylesheet,
)
from src.dash_app.utils.data_loader import (
    get_pep_by_number,
    get_citing_peps,
    get_cited_peps,
)
from src.dash_app.utils.table_helpers import compute_table_titles


def register_network_callbacks(app):
    """
    Networkタブのコールバックを登録する

    Args:
        app: Dashアプリケーションインスタンス
    """

    # ===== PEP情報更新コールバック（サーバーサイド） =====
    @app.callback(
        Output("network-pep-info-display", "children"),
        Output("network-pep-error-message", "children"),
        Input("network-pep-input", "value"),
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
        pep_number = parse_pep_number(pep_number)

        # 入力が空/Noneの場合: 初期説明文を表示
        if pep_number is None:
            return create_network_initial_info_message(), ""

        # PEPの存在確認
        pep_data = get_pep_by_number(pep_number)

        # 存在しない場合: エラーメッセージを表示
        if pep_data is None:
            error_message = f"Not Found: PEP {pep_number}"
            return create_network_initial_info_message(), error_message

        # 存在する場合: PEP情報を表示
        return create_pep_info_display(pep_data), ""

    # ===== ノードタップ → 入力欄更新コールバック（サーバーサイド） =====
    @app.callback(
        Output("network-pep-input", "value"),
        Input("network-graph", "tapNodeData"),
        Input("network-clear-selection-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def update_input_from_tap(tap_node_data, n_clicks):
        """
        ノードクリック時にPEP番号を更新、クリアボタンクリック時に選択解除

        Args:
            tap_node_data: クリックされたノードのデータ
            n_clicks: クリアボタンのクリック回数

        Returns:
            str | None | no_update: PEP番号または選択解除
        """
        # どのInputがトリガーしたかを判断
        ctx = callback_context
        if not ctx.triggered:
            return no_update

        triggered_id = ctx.triggered[0]["prop_id"]

        # クリアボタンがクリックされた場合
        if "network-clear-selection-btn" in triggered_id:
            return None

        # tapNodeDataがトリガーされた場合（ノードクリック）
        if "tapNodeData" in triggered_id:
            if tap_node_data is not None:
                pep_number = tap_node_data.get("pep_number")
                if pep_number is not None:
                    return str(pep_number)

        return no_update

    # ===== ハイライト更新コールバック（クライアントサイド） =====
    app.clientside_callback(
        """
        function(inputValue, currentElements) {
            // inputValueが空の場合はクラスをクリア
            if (!inputValue || inputValue === '') {
                return currentElements.map(function(el) {
                    var newEl = JSON.parse(JSON.stringify(el));
                    newEl.classes = '';
                    return newEl;
                });
            }

            // 選択されたPEP番号を取得
            var selectedPepNumber = parseInt(inputValue, 10);
            if (isNaN(selectedPepNumber)) {
                return window.dash_clientside.no_update;
            }

            var selectedNodeId = 'pep_' + selectedPepNumber;

            // 選択ノードを探す
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
        Output("network-graph", "elements"),
        Input("network-pep-input", "value"),
        State("network-graph", "elements"),
        prevent_initial_call=True,
    )

    # ===== テーブルタイトル更新コールバック（サーバーサイド） =====
    @app.callback(
        Output("network-citing-peps-title", "children"),
        Output("network-cited-peps-title", "children"),
        Input("network-pep-input", "value"),
    )
    def update_table_titles(pep_number):
        """
        PEP番号入力に連動してテーブルタイトルを更新する

        Args:
            pep_number: 入力されたPEP番号（str, int または None）

        Returns:
            tuple: (citing_title, cited_title)
        """
        return compute_table_titles(pep_number)

    # ===== テーブルデータ更新コールバック（サーバーサイド） =====
    @app.callback(
        Output("network-citing-peps-table", "data"),
        Output("network-cited-peps-table", "data"),
        Input("network-pep-input", "value"),
    )
    def update_tables(pep_number):
        """
        PEP番号入力に連動してテーブルデータを更新する

        Args:
            pep_number: 入力されたPEP番号（str, int または None）

        Returns:
            tuple: (citing_tableのデータ, cited_tableのデータ)
        """
        pep_number = parse_pep_number(pep_number)

        if pep_number is None:
            return [], []

        pep_data = get_pep_by_number(pep_number)
        if pep_data is None:
            return [], []

        citing_peps_df = get_citing_peps(pep_number)
        citing_table_data = convert_df_to_table_data(citing_peps_df)

        cited_peps_df = get_cited_peps(pep_number)
        cited_table_data = convert_df_to_table_data(cited_peps_df)

        return citing_table_data, cited_table_data

    # ===== スタイルシート更新コールバック（サーバーサイド） =====
    @app.callback(
        Output("network-graph", "stylesheet"),
        Input("network-node-size-type", "value"),
    )
    def update_node_size_stylesheet(size_type):
        """
        ノードサイズタイプの選択に連動してスタイルシートを更新する

        Args:
            size_type: ノードサイズのタイプ ("in_degree", "out_degree", "total_degree", "pagerank", "constant")

        Returns:
            list[dict]: 更新されたスタイルシート
        """
        return get_base_stylesheet(size_type)
