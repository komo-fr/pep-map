"""定数定義モジュール"""
from pathlib import Path

# プロジェクトルートディレクトリ
# constants.py の位置: src/dash_app/utils/constants.py
# プロジェクトルート: 4階層上
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# データディレクトリ
DATA_DIR = PROJECT_ROOT / "data" / "processed"

# PEPページのベースURL
PEP_BASE_URL = "https://peps.python.org/pep-{pep_number:04d}/"

# Statusごとの色定義
STATUS_COLOR_MAP = {
    "Accepted": "#40AAEF",      # 青
    "Active": "#F27398",        # 赤/ピンク
    "April Fool!": "#FFF200",   # 明るい黄色
    "Draft": "#FBA848",         # オレンジ
    "Final": "#58BE89",         # 緑
    "Provisional": "#EDE496",   # 黄色
    "Rejected": "#8A0808",      # 暗い赤
    "Superseded": "#000000",    # 黒
    "Withdrawn": "#737373",     # グレー
    "Deferred": "#5F4C0B",      # 暗い茶色
}

# デフォルトの色（未知のStatusの場合）
DEFAULT_STATUS_COLOR = "#888888"
