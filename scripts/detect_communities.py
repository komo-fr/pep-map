"""Detect communities in the PEP citation graph using Louvain method."""

import json
import logging
import pickle
import sys
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx

from src.dash_app.utils.constants import STATUS_COLOR_MAP
from src.graph.community_detector import (
    run_louvain_detection,
    create_pep_group_metrics,
    create_group_metrics,
    calculate_detection_stats,
    generate_subgraph_images,
    save_subgraphs,
    save_group_csvs,
)

logger = logging.getLogger(__name__)

# データパス設定
PROJECT_ROOT = Path(__file__).parent.parent
GRAPH_FILE = PROJECT_ROOT / "data/processed/pep_graph.pkl"
METADATA_FILE = PROJECT_ROOT / "data/processed/peps_metadata.csv"
OUTPUT_DIR = PROJECT_ROOT / "data/processed/groups"

# Louvainパラメータ（固定値）
RESOLUTION = 4
SEED = 42


def load_graph(graph_path: Path) -> nx.DiGraph:
    """グラフをpickleから読み込む"""
    logger.info(f"Loading graph from {graph_path}")
    with open(graph_path, "rb") as f:
        G = pickle.load(f)
    logger.info(
        f"Loaded graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges"
    )
    return G


def save_detection_metadata(
    output_path: Path,
    resolution: float,
    seed: int,
    stats: dict,
) -> None:
    """検出メタデータをJSONで保存"""
    metadata = {
        "algorithm": "louvain",
        "parameters": {
            "resolution": resolution,
            "seed": seed,
        },
        "statistics": stats,
        "detected_at": datetime.now(timezone.utc).isoformat(),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved detection metadata to {output_path}")


def main() -> int:
    """メイン処理"""
    # ロガー設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("Starting community detection")

    # 必須ファイルの存在確認
    if not GRAPH_FILE.exists():
        logger.error(f"Graph file not found: {GRAPH_FILE}")
        return 1

    if not METADATA_FILE.exists():
        logger.error(f"Metadata file not found: {METADATA_FILE}")
        return 1

    # グラフ読み込み
    G = load_graph(GRAPH_FILE)

    # コミュニティ検出
    communities = run_louvain_detection(G, resolution=RESOLUTION, seed=SEED)

    # 出力ディレクトリ作成
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # PEPごとのグループメトリクスを保存
    pep_group_df = create_pep_group_metrics(communities, G, METADATA_FILE)
    pep_group_path = OUTPUT_DIR / "pep_group_metrics.csv"
    pep_group_df.to_csv(pep_group_path, index=False)
    logger.info(f"Saved PEP group metrics to {pep_group_path}")

    # グループごとのメトリクスを保存
    group_df = create_group_metrics(communities, G)
    group_path = OUTPUT_DIR / "group_metrics.csv"
    group_df.to_csv(group_path, index=False)
    logger.info(f"Saved group metrics to {group_path}")

    # 検出統計を計算してメタデータを保存
    stats = calculate_detection_stats(communities, G)
    metadata_path = OUTPUT_DIR / "detection_metadata.json"
    save_detection_metadata(metadata_path, RESOLUTION, SEED, stats)

    # サブグラフをpickle形式で保存
    graphs_dir = OUTPUT_DIR / "subgraphs" / "graphs"
    saved_graphs = save_subgraphs(communities, G, graphs_dir)
    logger.info(f"Saved {len(saved_graphs)} subgraphs")

    # グループごとのCSVを保存
    metrics_dir = OUTPUT_DIR / "subgraphs" / "metrics"
    saved_csvs = save_group_csvs(pep_group_df, metrics_dir)
    logger.info(f"Saved {len(saved_csvs)} group CSVs")

    # サブグラフ画像を生成
    images_dir = OUTPUT_DIR / "subgraphs" / "images"
    generated_images = generate_subgraph_images(
        communities, G, images_dir, STATUS_COLOR_MAP
    )
    logger.info(f"Generated {len(generated_images)} subgraph images")

    logger.info("Community detection completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
