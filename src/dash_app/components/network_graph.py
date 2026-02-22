"""ネットワークグラフ構築モジュール"""

import networkx as nx

from src.dash_app.utils.constants import DEFAULT_STATUS_COLOR, STATUS_COLOR_MAP
from src.dash_app.utils.data_loader import load_citations, load_peps_metadata


# モジュールレベルでキャッシュ（アプリ起動時に一度だけ計算する）
_cytoscape_elements_cache: list[dict] | None = None


def build_cytoscape_elements() -> list[dict]:
    """
    PEPメタデータと引用関係からCytoscape用のelementsを構築する

    初回呼び出し時に計算し、以降はキャッシュを返す。

    Returns:
        list[dict]: Cytoscape elementsのリスト(ノードとエッジ)
    """
    global _cytoscape_elements_cache

    if _cytoscape_elements_cache is not None:
        return _cytoscape_elements_cache

    elements = []

    # ノードを生成
    nodes = _build_nodes()
    elements.extend(nodes)

    # エッジを生成
    edges = _build_edges()
    elements.extend(edges)

    _cytoscape_elements_cache = elements
    return elements


def _calculate_node_positions() -> dict[int, tuple[float, float]]:
    """
    NetworkXを使用してノードの座標を計算する

    孤立ノード(引用関係がないPEP)は左上にグリッド配置し、
    引用関係のあるノードは中央にspring_layoutで配置する。

    Returns:
        dict[int, tuple[float, float]]: PEP番号をキー、(x, y)座標を値とする辞書
    """

    peps_df = load_peps_metadata()
    citations_df = load_citations()

    # 存在するPEP番号のセット
    existing_peps = set(peps_df["pep_number"].tolist())

    # 有効なエッジのみに絞る(自己ループ・存在しないPEPへの参照を除外)
    valid = (
        (citations_df["citing"] != citations_df["cited"])
        & citations_df["citing"].isin(existing_peps)
        & citations_df["cited"].isin(existing_peps)
    )
    edges_df = citations_df.loc[valid, ["citing", "cited"]]

    # エッジリストから有向グラフを構築 (from_pandas_edgelist で一括追加)
    G = nx.from_pandas_edgelist(
        edges_df,
        source="citing",
        target="cited",
        create_using=nx.DiGraph,
    )

    # 孤立点(エッジに現れないPEP)をノードとして追加
    G.add_nodes_from(existing_peps)

    # 孤立ノードと引用関係のあるノードを分離
    isolated_nodes = [node for node in G.nodes() if G.degree(node) == 0]
    connected_nodes = [node for node in G.nodes() if G.degree(node) > 0]

    positions = {}

    # 引用関係のあるノードをspring_layoutで配置（先に計算してY座標の範囲を取得）
    if connected_nodes:
        # 引用関係のあるノードのみのサブグラフを作成
        subgraph = G.subgraph(connected_nodes)

        # 座標を計算(spring_layout = Fruchterman-Reingold力指向アルゴリズム)
        connected_positions = nx.spring_layout(
            subgraph,
            k=30,  # ノード間の理想的な距離(大きいほど広がる)
            iterations=500,  # イテレーション回数
            seed=42,  # 乱数シード(再現性のため)
            scale=900,  # 座標のスケール
            method="energy",  # 未指定でもノード数が多いため"energy"が適用されるが、明瞭さのため明示
            gravity=5,  # 重力の強さ
        )

        # connected_positionsをpositionsに追加(タプルに統一して型を揃える)
        positions.update(
            {n: (float(p[0]), float(p[1])) for n, p in connected_positions.items()}
        )

        # Y座標の範囲を取得
        y_values = [positions[n][1] for n in connected_nodes]
        y_min = min(y_values)
        y_max = max(y_values)
    else:
        # 引用関係のあるノードがない場合のデフォルト範囲
        y_min = -500
        y_max = 500

    # 孤立ノードを左端に3列で配置
    if isolated_nodes:
        isolated_nodes_sorted = sorted(isolated_nodes)  # PEP番号順にソート
        num_cols = 3  # 列数
        col_spacing = 40  # 列間の間隔
        x_start = -700  # 左端のx座標

        # 各列の行数を計算
        num_nodes = len(isolated_nodes_sorted)
        nodes_per_col = (num_nodes + num_cols - 1) // num_cols  # 切り上げ除算

        # Y座標の範囲内で均等に配置
        y_range = y_max - y_min
        if nodes_per_col > 1:
            y_spacing = y_range / (nodes_per_col - 1)
        else:
            y_spacing = 0

        for i, node in enumerate(isolated_nodes_sorted):
            col = i // nodes_per_col  # 列番号
            row_index = i % nodes_per_col  # その列内での行番号

            x = x_start + col * col_spacing
            y = y_max - row_index * y_spacing

            positions[node] = (float(x), float(y))

    return positions


def _build_nodes() -> list[dict]:
    """
    PEPメタデータからノードを生成する

    NetworkXで計算した座標をノードに付与する。

    Returns:
        list[dict]: ノードのリスト
    """
    peps_df = load_peps_metadata()

    # 座標を計算
    positions = _calculate_node_positions()

    nodes = []

    for _, row in peps_df.iterrows():
        pep_number = row["pep_number"]
        status = row["status"]
        color = STATUS_COLOR_MAP.get(status, DEFAULT_STATUS_COLOR)

        # 座標を取得(存在しない場合はデフォルト値)
        pos = positions.get(pep_number, (0, 0))

        node = {
            "data": {
                "id": f"pep_{pep_number}",
                "label": str(pep_number),
                "pep_number": pep_number,
                "color": color,
                "status": status,
            },
            "position": {
                "x": pos[0],
                "y": pos[1],
            },
        }
        nodes.append(node)

    return nodes


def _build_edges() -> list[dict]:
    """
    引用関係からエッジを生成する

    引用元(citing)→ 引用先(cited)の方向でエッジを作成する。
    同じPEP間の複数回引用は1本のエッジにまとめる(countは無視)。

    Returns:
        list[dict]: エッジのリスト
    """
    citations_df = load_citations()
    peps_df = load_peps_metadata()

    # 存在するPEP番号のセットを作成(エッジのフィルタリング用)
    existing_peps = set(peps_df["pep_number"].tolist())

    edges = []
    seen_edges = set()  # 重複エッジ防止用

    for _, row in citations_df.iterrows():
        citing = row["citing"]
        cited = row["cited"]

        # 自己ループを除外
        if citing == cited:
            continue

        # 存在しないPEPへのエッジを除外
        if citing not in existing_peps or cited not in existing_peps:
            continue

        # 重複エッジを除外
        edge_key = (citing, cited)
        if edge_key in seen_edges:
            continue
        seen_edges.add(edge_key)

        edge = {
            "data": {
                "id": f"edge_{citing}_{cited}",
                "source": f"pep_{citing}",
                "target": f"pep_{cited}",
            }
        }
        edges.append(edge)

    return edges


def get_base_stylesheet() -> list[dict]:
    """
    Cytoscapeグラフの基本スタイルシートを取得する

    ハイライト用のCSSクラススタイルも含む。

    Returns:
        list[dict]: スタイルシート定義のリスト
    """
    return [
        # ノード基本スタイル
        {
            "selector": "node",
            "style": {
                "label": "data(label)",
                "background-color": "data(color)",
                "width": 20,
                "height": 20,
                "font-size": "8px",
                "text-valign": "top",
                "text-halign": "center",
                "text-margin-y": -5,
                "border-width": 1,
                "border-color": "#999",
                "opacity": 0.5,
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
                "opacity": 0.5,
            },
        },
        # === ハイライト用スタイル ===
        # 選択中ノード（赤い太枠）
        {
            "selector": ".selected",
            "style": {
                "border-width": 4,
                "border-color": "#FF0000",
                "z-index": 9999,
                "opacity": 1,
            },
        },
        # 接続ノード（太枠）
        {
            "selector": ".connected",
            "style": {
                "border-width": 2,
                "border-color": "#333",
                "opacity": 1,
            },
        },
        # 接続エッジ（太く、色濃く）
        {
            "selector": ".connected-edge",
            "style": {
                "width": 2,
                "line-color": "#333",
                "target-arrow-color": "#333",
                "opacity": 1,
                "z-index": 9998,
            },
        },
        # 非接続（減衰）
        {
            "selector": ".faded",
            "style": {
                "opacity": 0.15,
            },
        },
    ]


def get_preset_layout_options() -> dict:
    """
    presetレイアウトのオプションを取得する

    presetレイアウトは事前計算された座標を使用するため、
    ブラウザ側でのレイアウト計算が不要で高速に描画される。

    Returns:
        dict: レイアウトオプション
    """
    return {
        "name": "preset",
        "fit": True,  # グラフを画面に収める
        "padding": 30,  # 余白
    }


def get_connected_elements(pep_number: int) -> dict:
    """
    指定されたPEP番号に接続しているノードとエッジを取得する

    Args:
        pep_number: 選択中のPEP番号

    Returns:
        dict: 接続情報
            - connected_nodes: 接続しているPEP番号のセット
            - connected_edges: 接続しているエッジIDのセット
    """
    citations_df = load_citations()
    peps_df = load_peps_metadata()

    # 存在するPEP番号のセット
    existing_peps = set(peps_df["pep_number"].tolist())

    # 指定されたPEPが存在しない場合
    if pep_number not in existing_peps:
        return {"connected_nodes": set(), "connected_edges": set()}

    # 条件でフィルタ（自己ループ・存在しないPEP・選択PEPに無関係なエッジを除外）
    no_self = citations_df["citing"] != citations_df["cited"]
    valid_peps = citations_df["citing"].isin(existing_peps) & citations_df[
        "cited"
    ].isin(existing_peps)
    involves_pep = (citations_df["citing"] == pep_number) | (
        citations_df["cited"] == pep_number
    )
    filtered = citations_df.loc[no_self & valid_peps & involves_pep]

    # 接続ノード: 選択PEPが引用元なら cited、引用先なら citing
    connected_nodes = set(
        filtered.loc[filtered["citing"] == pep_number, "cited"]
    ) | set(filtered.loc[filtered["cited"] == pep_number, "citing"])
    connected_edges = set(
        "edge_" + filtered["citing"].astype(str) + "_" + filtered["cited"].astype(str)
    )

    return {
        "connected_nodes": connected_nodes,
        "connected_edges": connected_edges,
    }


def apply_highlight_classes(
    elements: list[dict], selected_pep_number: int | None
) -> list[dict]:
    """
    elementsにハイライト用のCSSクラスを適用する

    Args:
        elements: Cytoscapeのelementsリスト
        selected_pep_number: 選択中のPEP番号（Noneの場合はハイライトなし）

    Returns:
        list[dict]: CSSクラスが適用されたelementsリスト
    """
    # PEPが選択されていない場合、クラスをクリアして返す
    if selected_pep_number is None:
        return _clear_all_classes(elements)

    # 接続情報を取得
    connection_info = get_connected_elements(selected_pep_number)
    connected_nodes = connection_info["connected_nodes"]
    connected_edges = connection_info["connected_edges"]

    updated_elements = []

    for element in elements:
        data = element["data"]
        new_element = {"data": data.copy()}

        # ノードの場合は position も保持する
        if "position" in element:
            new_element["position"] = element["position"]

        # ノードの場合
        if "source" not in data:
            pep_num = data["pep_number"]

            if pep_num == selected_pep_number:
                # 選択中ノード
                new_element["classes"] = "selected"
            elif pep_num in connected_nodes:
                # 接続ノード
                new_element["classes"] = "connected"
            else:
                # 非接続ノード
                new_element["classes"] = "faded"

        # エッジの場合
        else:
            edge_id = data["id"]

            if edge_id in connected_edges:
                # 接続エッジ
                new_element["classes"] = "connected-edge"
            else:
                # 非接続エッジ
                new_element["classes"] = "faded"

        updated_elements.append(new_element)

    return updated_elements


def _clear_all_classes(elements: list[dict]) -> list[dict]:
    """
    全elementsからCSSクラスを削除する

    Args:
        elements: Cytoscapeのelementsリスト

    Returns:
        list[dict]: クラスが削除されたelementsリスト
    """
    updated_elements = []

    for element in elements:
        new_element = {"data": element["data"].copy()}
        # ノードの場合は position も保持する
        if "position" in element:
            new_element["position"] = element["position"]
        # classesキーを含めない（クラスなし）
        updated_elements.append(new_element)

    return updated_elements
