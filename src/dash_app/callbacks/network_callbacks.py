"""Networkタブのコールバック関数"""

from dash import Input, Output, html, no_update

from src.dash_app.components import (
    parse_pep_number,
    create_pep_info_display,
    build_cytoscape_elements,
    apply_highlight_classes,
)
from src.dash_app.utils.data_loader import get_pep_by_number


def _create_initial_info_message() -> html.Div:
    """
    初期状態のPEP情報表示（説明文）を生成する

    Network専用のメッセージを表示する。

    Returns:
        html.Div: 初期説明文のコンポーネント
    """
    return html.Div(
        [
            html.P(
                "Enter a PEP number in the text box on the left (e.g., 8).",
                style={"marginBottom": "8px"},
            ),
            html.P("The selected PEP will be highlighted in the network graph."),
        ],
        style={
            "color": "#666",
        },
    )


def register_network_callbacks(app):
    """
    Networkタブのコールバックを登録する

    Args:
        app: Dashアプリケーションインスタンス
    """

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
            return _create_initial_info_message(), ""

        # PEPの存在確認
        pep_data = get_pep_by_number(pep_number)

        # 存在しない場合: エラーメッセージを表示
        if pep_data is None:
            error_message = f"Not Found: PEP {pep_number}"
            return _create_initial_info_message(), error_message

        # 存在する場合: PEP情報を表示
        return create_pep_info_display(pep_data), ""

    @app.callback(
        Output("network-pep-input", "value"),
        Input("network-graph", "tapNodeData"),
        prevent_initial_call=True,
    )
    def update_input_from_node_click(tap_data):
        """
        ノードクリック時にPEP番号入力欄を更新する

        Args:
            tap_data: クリックされたノードのデータ

        Returns:
            str: PEP番号（入力欄に設定する値）
        """
        if tap_data is None:
            return no_update

        # クリックしたノードのPEP番号を返す
        pep_number = tap_data.get("pep_number")
        if pep_number is not None:
            return str(pep_number)

        return no_update

    @app.callback(
        Output("network-graph", "elements"),
        Input("network-pep-input", "value"),
    )
    def update_graph_highlight(pep_number):
        """
        PEP番号入力に連動してグラフのハイライトを更新する

        Args:
            pep_number: 入力されたPEP番号

        Returns:
            list[dict]: ハイライトが適用されたelements
        """
        # 全elementsを取得
        elements = build_cytoscape_elements()

        # PEP番号を解析
        pep_number = parse_pep_number(pep_number)

        # ハイライトを適用
        highlighted_elements = apply_highlight_classes(elements, pep_number)

        return highlighted_elements
