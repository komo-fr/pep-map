"""Generate group descriptions using LLM."""

import argparse
import logging
import os
import sys
from pathlib import Path

from src.llm.group_profile import save_profiles_to_csv

logger = logging.getLogger(__name__)

# データパス設定
PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data/processed/groups"


def parse_args() -> argparse.Namespace:
    """コマンドライン引数をパース"""
    parser = argparse.ArgumentParser(
        description="Generate group descriptions using LLM"
    )
    parser.add_argument(
        "--model",
        default=os.getenv("LLM_MODEL", "gpt-4o"),
        help="LLM model name (default: env LLM_MODEL or gpt-4o)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Data directory containing pep_group_metrics.csv",
    )
    return parser.parse_args()


def main() -> int:
    """メイン処理"""
    # ロガー設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    args = parse_args()
    logger.info(f"Starting group description generation with model={args.model}")

    # 必須ファイルの存在確認
    pep_group_file = args.data_dir / "pep_group_metrics.csv"
    if not pep_group_file.exists():
        logger.error(f"PEP group metrics file not found: {pep_group_file}")
        return 1

    images_dir = args.data_dir / "subgraphs" / "images"
    if not images_dir.exists():
        logger.error(f"Subgraph images directory not found: {images_dir}")
        return 1

    # グループ名や説明文などのプロファイルを生成して保存
    try:
        save_profiles_to_csv(args.model, args.data_dir)
    except Exception as e:
        logger.error(f"Failed to generate group profiles: {e}")
        return 1

    logger.info("Group profiles generation completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
