"""テーブル関連のヘルパー関数"""

from src.dash_app.components.pep_info import parse_pep_number
from src.dash_app.utils.data_loader import get_pep_by_number


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
