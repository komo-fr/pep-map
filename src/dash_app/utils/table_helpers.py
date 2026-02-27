"""テーブル関連のヘルパー関数"""

import pandas as pd

from src.dash_app.components.pep_info import parse_pep_number
from src.dash_app.utils.data_loader import get_pep_by_number


def data_bars(df: pd.DataFrame, column: str) -> list[dict]:
    """
    DataTableの列に数値に応じたデータバー（棒グラフ）スタイルを生成

    Args:
        df: データフレーム
        column: データバーを適用する列名

    Returns:
        list[dict]: style_data_conditionalに追加するスタイルのリスト
    """
    n_bins = 30
    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    ranges = [
        ((df[column].max() - df[column].min()) * i) + df[column].min() for i in bounds
    ]
    styles = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]
        max_bound_percentage = bounds[i] * 100
        styles.append(
            {
                "if": {
                    "filter_query": (
                        "{{{column}}} >= {min_bound}"
                        + (
                            " && {{{column}}} < {max_bound}"
                            if (i < len(bounds) - 1)
                            else ""
                        )
                    ).format(column=column, min_bound=min_bound, max_bound=max_bound),
                    "column_id": column,
                },
                "background": (
                    """
                    linear-gradient(90deg,
                    #0074D9 0%,
                    #0074D9 {max_bound_percentage}%,
                    white {max_bound_percentage}%,
                    white 100%)
                """.format(max_bound_percentage=max_bound_percentage)
                ),
                "paddingBottom": 2,
                "paddingTop": 2,
            }
        )

    return styles


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
