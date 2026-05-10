"""Detect communities in the PEP citation graph using Louvain method."""

import json
import logging
import pickle
import sys
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx

from src.graph.community_detector import (
    run_louvain_detection,
    create_pep_group_metrics,
    create_group_metrics,
    calculate_detection_stats,
    generate_subgraph_images,
    generate_full_network_highlight_images,
    save_subgraphs,
    save_full_network_positions,
    save_subgraph_positions,
    save_group_to_group_network,
)

logger = logging.getLogger(__name__)

# データパス設定
PROJECT_ROOT = Path(__file__).parent.parent
GRAPH_FILE = PROJECT_ROOT / "data/processed/pep_graph.pkl"
METADATA_FILE = PROJECT_ROOT / "data/processed/peps_metadata.csv"
CITATIONS_FILE = PROJECT_ROOT / "data/processed/citations.csv"
OUTPUT_DIR = PROJECT_ROOT / "data/processed/groups"
GROUP_TO_GROUP_DIR = OUTPUT_DIR / "group_to_group"

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

    # 全体ネットワーク座標を計算・保存
    full_positions_path = OUTPUT_DIR.parent / "node_positions.json"
    full_positions = save_full_network_positions(G, full_positions_path)
    logger.info(f"Saved full network positions to {full_positions_path}")

    # サブグラフ座標を保存
    positions_dir = OUTPUT_DIR / "subgraphs" / "positions"
    saved_positions = save_subgraph_positions(communities, G, positions_dir)
    logger.info(f"Saved {len(saved_positions)} subgraph position files")

    # サブグラフ画像を生成
    images_dir = OUTPUT_DIR / "subgraphs" / "images"
    generated_images = generate_subgraph_images(communities, G, images_dir)
    logger.info(f"Generated {len(generated_images)} subgraph images")

    # 全体ネットワークハイライト画像を生成（計算済み座標を渡す）
    full_images_dir = OUTPUT_DIR / "subgraphs" / "full_images"
    generated_full_images = generate_full_network_highlight_images(
        communities, G, full_images_dir, positions=full_positions
    )
    logger.info(f"Generated {len(generated_full_images)} full network highlight images")

    # グループ間ネットワークを生成・保存
    citations_csv, network_pkl, positions_json = save_group_to_group_network(
        pep_group_metrics_path=pep_group_path,
        citations_path=CITATIONS_FILE,
        output_dir=GROUP_TO_GROUP_DIR,
    )
    logger.info(
        f"Saved group-to-group network: {citations_csv}, {network_pkl}, {positions_json}"
    )

    logger.info("Community detection completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
