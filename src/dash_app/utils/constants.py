"""定数定義モジュール"""

import colorsys
from pathlib import Path

# プロジェクトルートディレクトリ
# constants.py の位置: src/dash_app/utils/constants.py
# プロジェクトルート: 4階層上
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# データディレクトリ
DATA_DIR = PROJECT_ROOT / "data" / "processed"
STATIC_DIR = PROJECT_ROOT / "data" / "static"

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
TIMELINE_ANNOTATION_FONT_SIZE = 30
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

# === Citation Changes タブ定数 ===

# Change Type ごとの背景色定義
CHANGE_TYPE_COLOR_MAP = {
    "Added": "#58BE89",  # 緑 (Final と同じ)
    "Changed": "#EDE496",  # 黄色 (Provisional と同じ)
    "Deleted": "#8A0808",  # 暗い赤 (Rejected と同じ)
}

# Change Type ごとのフォント色定義
CHANGE_TYPE_FONT_COLOR_MAP = {
    "Added": "#FAFAFA",  # 白
    "Changed": BASE_FONT_COLOR,  # #545454
    "Deleted": "#FAFAFA",  # 白
}

# === Group（コミュニティ検出）タブ定数 ===

# グループカラーパレット（32色）
# D3.jsのcategory20 + category20b + category20cから選択
GROUP_COLOR_PALETTE = [
    "#1f77b4",  # Group 0 - 青
    "#ff7f0e",  # Group 1 - オレンジ
    "#2ca02c",  # Group 2 - 緑
    "#d62728",  # Group 3 - 赤
    "#9467bd",  # Group 4 - 紫
    "#8c564b",  # Group 5 - 茶
    "#e377c2",  # Group 6 - ピンク
    "#7f7f7f",  # Group 7 - グレー
    "#bcbd22",  # Group 8 - 黄緑
    "#17becf",  # Group 9 - シアン
    "#aec7e8",  # Group 10 - 薄い青
    "#ffbb78",  # Group 11 - 薄いオレンジ
    "#98df8a",  # Group 12 - 薄い緑
    "#ff9896",  # Group 13 - 薄い赤
    "#c5b0d5",  # Group 14 - 薄い紫
    "#c49c94",  # Group 15 - 薄い茶
    "#f7b6d2",  # Group 16 - 薄いピンク
    "#c7c7c7",  # Group 17 - 薄いグレー
    "#dbdb8d",  # Group 18 - 薄い黄緑
    "#9edae5",  # Group 19 - 薄いシアン
    "#393b79",  # Group 20 - 濃い青紫
    "#5254a3",  # Group 21 - 青紫
    "#6b6ecf",  # Group 22 - 明るい青紫
    "#9c9ede",  # Group 23 - 薄い青紫
    "#637939",  # Group 24 - 濃い黄緑
    "#8ca252",  # Group 25 - オリーブ
    "#b5cf6b",  # Group 26 - 明るい黄緑
    "#cedb9c",  # Group 27 - 薄い黄緑
    "#8c6d31",  # Group 28 - 濃い茶
    "#bd9e39",  # Group 29 - 金色
    "#e7ba52",  # Group 30 - 明るい金色
    "#e7cb94",  # Group 31 - 薄い金色
]

# 孤立ノード（group_id = -1）の色
ISOLATED_NODE_COLOR = "#CCCCCC"


def get_group_color(group_id: int) -> str:
    """
    グループIDに対応する色を取得する

    パレット内（0〜31）は事前定義された色を使用し、
    パレットを超えた場合は黄金比を使って動的に色を生成する。

    Args:
        group_id: グループID（-1は孤立ノード、0以上はコミュニティ）

    Returns:
        str: 色コード（例: "#1f77b4"）
    """
    if group_id < 0:
        return ISOLATED_NODE_COLOR

    if group_id < len(GROUP_COLOR_PALETTE):
        return GROUP_COLOR_PALETTE[group_id]

    # パレットを超えた場合は黄金比で色相を分散させて動的生成
    # 黄金比（φ - 1 ≈ 0.618）を使うと隣接グループでも色が離れる
    golden_ratio_conjugate = 0.618033988749895
    hue = (group_id * golden_ratio_conjugate) % 1.0
    saturation = 0.6
    lightness = 0.5
    r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


# === テキスト視認性向上のための縁取りスタイル ===
# 暗い背景色でも文字が見えるように白い縁取りを適用
TEXT_OUTLINE_WIDTH = 1
TEXT_OUTLINE_COLOR = "#ffffff"
