"""テーブル関連のヘルパー関数"""

import pandas as pd

from src.dash_app.components.pep_info import parse_pep_number
from src.dash_app.utils.data_loader import get_pep_by_number


def data_bars(df: pd.DataFrame, column: str) -> list[dict]:
    """
    AG Gridの列に数値に応じたデータバー（棒グラフ）スタイル条件を生成

    Args:
        df: データフレーム
        column: データバーを適用する列名

    Returns:
        list[dict]: cellStyle.styleConditionsに使用する条件リスト
    """
    n_bins = 30
    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    ranges = [
        ((df[column].max() - df[column].min()) * i) + df[column].min() for i in bounds
    ]
    conditions = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]
        max_bound_percentage = bounds[i] * 100
        if i < len(bounds) - 1:
            condition = f"params.value >= {min_bound} && params.value < {max_bound}"
        else:
            condition = f"params.value >= {min_bound}"
        conditions.append(
            {
                "condition": condition,
                "style": {
                    "backgroundImage": (
                        f"linear-gradient(90deg, "
                        f"rgba(25, 118, 210, 0.35) 0%, "
                        f"rgba(25, 118, 210, 0.35) {max_bound_percentage}%, "
                        f"white {max_bound_percentage}%, "
                        f"white 100%)"
                    ),
                },
            }
        )

    return conditions


def gradient_backgrounds(df: pd.DataFrame, column: str) -> list[dict]:
    """
    AG Gridの列に数値に応じたグラデーション背景色の条件を生成
    セル全体の背景色が値に応じて濃淡が変わる

    Args:
        df: データフレーム
        column: グラデーション背景を適用する列名

    Returns:
        list[dict]: cellStyle.styleConditionsに使用する条件リスト
    """
    n_bins = 30
    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    ranges = [
        ((df[column].max() - df[column].min()) * i) + df[column].min() for i in bounds
    ]
    conditions = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]
        # 値の大きさに応じて不透明度を変化（0.05〜0.4の範囲）
        opacity = 0.05 + (bounds[i] * 0.35)
        if i < len(bounds) - 1:
            condition = f"params.value >= {min_bound} && params.value < {max_bound}"
        else:
            condition = f"params.value >= {min_bound}"
        conditions.append(
            {
                "condition": condition,
                "style": {
                    "backgroundColor": f"rgba(156, 39, 176, {opacity:.3f})",
                },
            }
        )

    return conditions


def compute_table_titles(pep_number_input) -> tuple[str, str]:
    """
    テーブルタイトルを計算する

    Args:
        pep_number_input: 入力されたPEP番号（str, int または None）

    Returns:
        tuple: (citing_title, cited_title)
    """
    pep_number = parse_pep_number(pep_number_input)

    if pep_number is None:
        return "PEP N is cited by...", "PEP N cites..."

    if get_pep_by_number(pep_number) is None:
        return "PEP N is cited by...", "PEP N cites..."

    return f"PEP {pep_number} is cited by...", f"PEP {pep_number} cites..."
