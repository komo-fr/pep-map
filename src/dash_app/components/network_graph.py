"""ネットワークグラフ構築モジュール"""

from src.dash_app.utils.constants import DEFAULT_STATUS_COLOR, STATUS_COLOR_MAP
from src.dash_app.utils.data_loader import load_citations, load_peps_metadata


def build_cytoscape_elements() -> list[dict]:
    """
    PEPメタデータと引用関係からCytoscape用のelementsを構築する

    Returns:
        list[dict]: Cytoscape elementsのリスト(ノードとエッジ)
    """
    elements = []

    # ノードを生成
    nodes = _build_nodes()
    elements.extend(nodes)

    # エッジを生成
    edges = _build_edges()
    elements.extend(edges)

    return elements


def _build_nodes() -> list[dict]:
    """
    PEPメタデータからノードを生成する

    Returns:
        list[dict]: ノードのリスト
    """
    peps_df = load_peps_metadata()
    nodes = []

    for _, row in peps_df.iterrows():
        pep_number = row["pep_number"]
        status = row["status"]
        color = STATUS_COLOR_MAP.get(status, DEFAULT_STATUS_COLOR)

        node = {
            "data": {
                "id": f"pep_{pep_number}",
                "label": str(pep_number),
                "pep_number": pep_number,
                "color": color,
                "status": status,
            }
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
            },
        },
        # エッジ基本スタイル
        {
            "selector": "edge",
            "style": {
                "width": 0.5,
                "line-color": "#ccc",
                "target-arrow-color": "#ccc",
                "target-arrow-shape": "triangle",
                "arrow-scale": 0.5,
                "curve-style": "bezier",
                "opacity": 0.6,
            },
        },
    ]


def get_cose_layout_options() -> dict:
    """
    coseレイアウトのオプションを取得する

    Returns:
        dict: レイアウトオプション
    """
    return {
        "name": "cose",
        "animate": False,  # 初期表示時はアニメーションなし
        "fit": True,  # グラフを画面に収める
        "padding": 30,  # 余白
        "nodeRepulsion": 8000,  # ノード間の反発力
        "idealEdgeLength": 50,  # 理想的なエッジの長さ
        "edgeElasticity": 100,  # エッジの弾性
        "nestingFactor": 1.2,
        "gravity": 1,
        "numIter": 1000,  # イテレーション回数
        "randomize": True,  # 初期位置をランダムに
    }
