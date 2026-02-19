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

# 基本的なフォント色
BASE_FONT_COLOR = "#545454"

# Statusごとのフォント色定義
STATUS_FONT_COLOR_MAP = {
    "Accepted": "#FAFAFA",
    "Active": "#FAFAFA",
    "April Fool!": BASE_FONT_COLOR,
    "Draft": "#FAFAFA",
    "Final": "#FAFAFA",
    "Provisional": BASE_FONT_COLOR,
    "Rejected": "#FAFAFA",
    "Superseded": "#FAFAFA",
    "Withdrawn": "#FAFAFA",
    "Deferred": "#FAFAFA",
}

# デフォルトのフォント色（未知のStatusの場合）
DEFAULT_STATUS_FONT_COLOR = BASE_FONT_COLOR

# === Timeline グラフ定数 ===

# Y軸の位置定数
TIMELINE_Y_SELECTED = 0  # 選択中のPEP
TIMELINE_Y_CITING = 1  # 引用しているPEP
TIMELINE_Y_CITED = -1  # 引用されているPEP
TIMELINE_Y_RANGE = (-2.0, 2.0)  # Y軸の表示範囲（アノテーション用に拡大）
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

# === Timeline PEP情報アノテーション定数 ===
# アノテーションの位置
TIMELINE_ANNOTATION_X = 0.01  # 左端近くの固定位置（paper座標系）
TIMELINE_ANNOTATION_Y_CITING_TEXT = (
    0.55  # 上部テキスト: CITING PEP付近（Y=1）とSELECTED（Y=0）の中間より下
)
TIMELINE_ANNOTATION_Y_CITED_TEXT = (
    -0.4
)  # 下部テキスト: CITED PEP付近（Y=-1）とSELECTED（Y=0）の中間より上

# アノテーション矢印設定
TIMELINE_ANNOTATION_ARROW_AY = -50  # 矢印の縦方向オフセット（ピクセル）
TIMELINE_ANNOTATION_ARROW_SIZE = 1
TIMELINE_ANNOTATION_ARROW_WIDTH = 1.5
TIMELINE_ANNOTATION_ARROW_COLOR = "#000000"
TIMELINE_ANNOTATION_TEXT_COLOR = "#000000"
TIMELINE_ANNOTATION_TEXT_SIZE = 12

# === Python リリース日表示定数 ===

# Python リリース日の縦線色（ラベル色と統一）
PYTHON_2_LINE_COLOR = "#DDAD3E"  # 黄色
PYTHON_3_LINE_COLOR = "#2E6495"  # 青

# Pythonリリースバージョンラベルのタイムライン上Y座標
TIMELINE_Y_PYTHON2_LABEL = 1.85  # Python 2系バージョンラベル
TIMELINE_Y_PYTHON3_LABEL = 1.65  # Python 3系バージョンラベル
