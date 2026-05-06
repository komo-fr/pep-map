"""グラフデータ読み込みモジュール

NetworkXグラフやノード座標などのグラフ関連データを読み込む。
src/dash_app/への依存を避けるため、共通のグラフ層に配置。
"""

import json
import pickle
from pathlib import Path

import networkx as nx
import pandas as pd

# DATA_DIRをdash_appから独立して定義
# loader.py の位置: src/graph/loader.py
# プロジェクトルート: 3階層上
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _PROJECT_ROOT / "data" / "processed"


# キャッシュ変数
_full_network_positions_cache: dict[int, tuple[float, float]] | None = None
_subgraph_positions_cache: dict[int, dict[int, tuple[float, float]]] = {}


def load_subgraph(group_id: int) -> nx.DiGraph | None:
    """
    指定されたグループIDのサブグラフを読み込む

    Args:
        group_id: グループID

    Returns:
        NetworkX DiGraph、存在しない場合はNone
    """
    subgraph_path = (
        _DATA_DIR / "groups" / "subgraphs" / "graphs" / f"subgraph_{group_id}.pkl"
    )
    if not subgraph_path.exists():
        return None

    with open(subgraph_path, "rb") as f:
        return pickle.load(f)


def load_subgraph_metrics(group_id: int) -> pd.DataFrame | None:
    """
    指定されたグループIDのメトリクスを読み込む

    Args:
        group_id: グループID

    Returns:
        DataFrame、存在しない場合はNone
    """
    metrics_path = _DATA_DIR / "groups" / "pep_group_metrics.csv"
    if not metrics_path.exists():
        return None
    df = pd.read_csv(metrics_path)
    df = df[df["group_id"] == group_id]

    return df


def load_full_network_positions() -> dict[int, tuple[float, float]]:
    """
    全体ネットワークのノード座標を読み込む

    Returns:
        dict[int, tuple[float, float]]: PEP番号をキー、(x, y)座標を値とする辞書
    """
    global _full_network_positions_cache

    if _full_network_positions_cache is not None:
        return _full_network_positions_cache

    positions_path = _DATA_DIR / "node_positions.json"
    if not positions_path.exists():
        raise FileNotFoundError(
            f"Node positions file not found: {positions_path}. "
            "Run the data pipeline to generate this file."
        )

    with open(positions_path, encoding="utf-8") as f:
        positions_json = json.load(f)

    # キーを整数に変換
    positions = {int(node): tuple(pos) for node, pos in positions_json.items()}

    _full_network_positions_cache = positions
    return positions


def load_subgraph_positions(group_id: int) -> dict[int, tuple[float, float]] | None:
    """
    指定されたグループIDのサブグラフ座標を読み込む

    Args:
        group_id: グループID

    Returns:
        dict[int, tuple[float, float]]: PEP番号をキー、(x, y)座標を値とする辞書
        存在しない場合はNone
    """
    global _subgraph_positions_cache

    if group_id in _subgraph_positions_cache:
        return _subgraph_positions_cache[group_id]

    positions_path = (
        _DATA_DIR / "groups" / "subgraphs" / "positions" / f"group_{group_id}.json"
    )
    if not positions_path.exists():
        return None

    with open(positions_path, encoding="utf-8") as f:
        positions_json = json.load(f)

    # キーを整数に変換
    positions = {int(node): tuple(pos) for node, pos in positions_json.items()}

    _subgraph_positions_cache[group_id] = positions
    return positions


def clear_cache() -> None:
    """キャッシュをクリアする（テスト用）"""
    global _full_network_positions_cache, _subgraph_positions_cache
    _full_network_positions_cache = None
    _subgraph_positions_cache = {}
