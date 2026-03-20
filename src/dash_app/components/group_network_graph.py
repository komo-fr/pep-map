"""グループ用ネットワークグラフ構築モジュール"""

from src.dash_app.components.network_graph import build_cytoscape_elements
from src.dash_app.utils.constants import get_group_color
from src.dash_app.utils.data_loader import load_group_data


# モジュールレベルでキャッシュ
_group_cytoscape_elements_cache: list[dict] | None = None


def build_group_cytoscape_elements() -> list[dict]:
    """
    グループ情報を含むCytoscape用elementsを構築する

    既存のbuild_cytoscape_elements()の結果を元に、グループ情報を追加する。

    Returns:
        list[dict]: Cytoscape elementsのリスト(ノードとエッジ)
            ノードには以下のデータが追加される:
            - group_id: グループID
            - group_color: グループに対応する色
    """
    global _group_cytoscape_elements_cache

    if _group_cytoscape_elements_cache is not None:
        return _group_cytoscape_elements_cache

    # 既存のelementsを取得
    base_elements = build_cytoscape_elements()

    # グループデータを読み込み、PEP番号→グループIDのマッピングを作成
    group_df = load_group_data()
    pep_to_group = dict(zip(group_df["PEP"], group_df["group_id"]))

    # elementsにグループ情報を追加
    elements = []
    for el in base_elements:
        new_el = _deep_copy_element(el)

        # ノードの場合のみグループ情報を追加
        if "source" not in new_el["data"]:  # エッジでない = ノード
            pep_number = new_el["data"].get("pep_number")
            if pep_number is not None:
                group_id = pep_to_group.get(pep_number, -1)
                new_el["data"]["group_id"] = group_id
                new_el["data"]["group_color"] = get_group_color(group_id)

        elements.append(new_el)

    _group_cytoscape_elements_cache = elements
    return elements


def _deep_copy_element(el: dict) -> dict:
    """
    elementをディープコピーする

    Args:
        el: コピー元のelement

    Returns:
        dict: コピーされたelement
    """
    new_el = {"data": dict(el["data"])}
    if "position" in el:
        new_el["position"] = dict(el["position"])
    if "classes" in el:
        new_el["classes"] = el["classes"]
    return new_el


def get_group_base_stylesheet() -> list[dict]:
    """
    グループ用の基本スタイルシートを取得する

    ノード色はdata(group_color)を使用する。

    Returns:
        list[dict]: スタイルシート定義のリスト
    """
    return [
        # ノード基本スタイル
        {
            "selector": "node",
            "style": {
                "label": "data(label)",
                "background-color": "data(group_color)",
                "width": "data(size_pagerank)",
                "height": "data(size_pagerank)",
                "font-size": "data(font_size_pagerank)",
                "text-valign": "center",
                "text-halign": "center",
                "border-width": 1,
                "border-color": "#999",
                "opacity": 0.8,
                # テキストの視認性向上（暗い背景色でも文字が見えるように）
                "text-outline-width": 1,
                "text-outline-color": "#ffffff",
            },
        },
        # エッジ基本スタイル
        {
            "selector": "edge",
            "style": {
                "width": 2,
                "line-color": "#999",
                "target-arrow-color": "#999",
                "target-arrow-shape": "triangle",
                "arrow-scale": 1,
                "curve-style": "bezier",
                "opacity": 0.3,
            },
        },
        # === ハイライト用スタイル ===
        # グループ選択時のハイライト
        {
            "selector": ".group-selected",
            "style": {
                "opacity": 1,
                "border-width": 2,
                "border-color": "#333",
                "text-outline-width": 1,
                "text-outline-color": "#ffffff",
            },
        },
        # グループ選択時の非選択ノード（減衰）
        {
            "selector": ".group-faded",
            "style": {
                "opacity": 0.15,
            },
        },
        # グループ選択時のエッジ（グループ内のエッジ）
        {
            "selector": ".group-selected-edge",
            "style": {
                "opacity": 1,
                "line-color": "#666",
                "target-arrow-color": "#666",
                "width": 2,
            },
        },
        # ノードタップ時の選択スタイル
        {
            "selector": ":selected",
            "style": {
                "border-width": 4,
                "border-color": "#FF0000",
                "z-index": 9999,
                "opacity": 1,
                "text-outline-width": 1,
                "text-outline-color": "#ffffff",
            },
        },
    ]


def get_group_selected_stylesheet() -> list[dict]:
    """
    グループ選択時のスタイルシートを取得する

    :selectedのスタイルをオーバーライドして、赤枠を無効化する。

    Returns:
        list[dict]: スタイルシート定義のリスト
    """
    base = get_group_base_stylesheet()

    # :selectedのスタイルをオーバーライド（赤枠を無効化）
    override_styles = [
        {
            "selector": ".group-selected:selected",
            "style": {
                "border-width": 2,
                "border-color": "#333",
                "opacity": 1,
                "text-outline-width": 1,
                "text-outline-color": "#ffffff",
            },
        },
        {
            "selector": ".group-faded:selected",
            "style": {
                "border-width": 1,
                "border-color": "#999",
                "opacity": 0.15,
                "text-outline-width": 1,
                "text-outline-color": "#ffffff",
            },
        },
    ]

    return base + override_styles


def clear_cache() -> None:
    """
    キャッシュをクリアする（テスト用）
    """
    global _group_cytoscape_elements_cache
    _group_cytoscape_elements_cache = None


def get_preset_layout_options() -> dict:
    """
    presetレイアウトのオプションを取得する

    Returns:
        dict: レイアウトオプション
    """
    return {
        "name": "preset",
        "fit": True,
        "padding": 30,
    }
