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
    "Accepted": "#40AAEF",  # 青
    "Active": "#F27398",  # 赤/ピンク
    "April Fool!": "#FFF200",  # 明るい黄色
    "Draft": "#FBA848",  # オレンジ
    "Final": "#58BE89",  # 緑
    "Provisional": "#EDE496",  # 黄色
    "Rejected": "#8A0808",  # 暗い赤
    "Superseded": "#000000",  # 黒
    "Withdrawn": "#737373",  # グレー
    "Deferred": "#5F4C0B",  # 暗い茶色
}

# デフォルトの色（未知のStatusの場合）
DEFAULT_STATUS_COLOR = "#888888"

# === Timeline グラフ定数 ===

# Y軸の位置定数
TIMELINE_Y_SELECTED = 0  # 選択中のPEP
TIMELINE_Y_CITING = 1  # 引用しているPEP
TIMELINE_Y_CITED = -1  # 引用されているPEP
TIMELINE_Y_RANGE = (-1.5, 1.5)  # Y軸の表示範囲
TIMELINE_Y_TICKVALS = [-1, 0, 1]  # Y軸の目盛り値

# グラフレイアウト
TIMELINE_MARGIN = {"l": 40, "r": 40, "t": 40, "b": 40}
TIMELINE_MARKER_SIZE = 10
TIMELINE_TEXT_FONT_SIZE = 10
TIMELINE_ZEROLINE_WIDTH = 1
TIMELINE_ZEROLINE_COLOR = "#ddd"

# アノテーション（空グラフ用）
TIMELINE_ANNOTATION_FONT_SIZE = 14
TIMELINE_ANNOTATION_FONT_COLOR = "#999"
