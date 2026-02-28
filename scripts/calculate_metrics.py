"""Calculate PageRank and other metrics for PEP citation graph."""

import json
import logging
import pickle
import sys
from pathlib import Path

import networkx as nx
import pandas as pd

logger = logging.getLogger(__name__)


def build_pep_graph(
    citations_path: Path,
    metadata_path: Path | None = None,
    peps_metadata_path: Path | None = None,
) -> nx.DiGraph:
    """
    引用関係から有向グラフを構築

    Args:
        citations_path: citations.csvのパス
        metadata_path: metadata.jsonのパス（Noneならメタデータなし）
        peps_metadata_path: peps_metadata.csvのパス（Noneなら全PEPを許可、指定時は有効PEPでフィルタ・孤立ノード追加）

    Returns:
        NetworkX DiGraph (メタデータ付き)
    """
    logger.info(f"Building PEP graph from {citations_path}")

    # 有効なPEP番号を取得（peps_metadata.csvから）
    valid_peps: set[int] | None = None
    if peps_metadata_path is not None:
        if peps_metadata_path.exists():
            peps_df = pd.read_csv(peps_metadata_path)
            valid_peps = set(peps_df["pep_number"])
            logger.info(
                f"Loaded {len(valid_peps)} valid PEP numbers from {peps_metadata_path}"
            )
        else:
            logger.warning(
                f"PEP metadata file not found: {peps_metadata_path}. "
                "All PEPs in citations will be included."
            )

    # 1. citations.csvを読み込み
    citations_df = pd.read_csv(citations_path)
    logger.info(f"Loaded {len(citations_df)} citation records")

    # 2. 自己ループを除外
    citations_df = citations_df[citations_df["citing"] != citations_df["cited"]]
    logger.info(f"After excluding self-loops: {len(citations_df)} records")

    # 3. valid_pepsに含まれないPEPを除外
    if valid_peps is not None:
        citations_df = citations_df[
            citations_df["citing"].isin(valid_peps)
            & citations_df["cited"].isin(valid_peps)
        ]
        logger.info(f"After filtering by valid PEPs: {len(citations_df)} records")

    # 4. DiGraphを構築（エッジリストから）
    G = nx.from_pandas_edgelist(
        citations_df,
        source="citing",
        target="cited",
        edge_attr="count" if "count" in citations_df.columns else None,
        create_using=nx.DiGraph,
    )

    # 5. 孤立ノード（引用関係のないPEP）を追加
    if valid_peps is not None:
        G.add_nodes_from(valid_peps)
        logger.info("Added all valid PEPs as nodes (including isolated nodes)")

    logger.info(
        f"Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges"
    )

    # 6. metadata.jsonを読み込んでG.graphに設定
    if metadata_path is not None and metadata_path.exists():
        with open(metadata_path, encoding="utf-8") as f:
            metadata = json.load(f)

        if "fetched_at" in metadata:
            G.graph["fetched_at"] = metadata["fetched_at"]
            logger.info(f"Graph metadata: fetched_at={metadata['fetched_at']}")

        if "source_url" in metadata:
            G.graph["source_url"] = metadata["source_url"]
            logger.info(f"Graph metadata: source_url={metadata['source_url']}")

    return G


def calculate_node_metrics(G: nx.DiGraph) -> pd.DataFrame:
    """
    有向グラフから各ノードのメトリクスを計算

    Args:
        G: NetworkX DiGraph

    Returns:
        DataFrame with columns: pep_number, in_degree, out_degree, degree, pagerank
    """
    logger.info("Calculating node metrics")

    # 各メトリクスを辞書で一括取得
    in_degrees = dict(G.in_degree())
    out_degrees = dict(G.out_degree())
    pagerank_dict = nx.pagerank(G, alpha=0.85)

    nodes = list(G.nodes())
    metrics_df = pd.DataFrame(
        {
            "pep_number": nodes,
            "in_degree": [in_degrees[n] for n in nodes],
            "out_degree": [out_degrees[n] for n in nodes],
            "degree": [in_degrees[n] + out_degrees[n] for n in nodes],
            "pagerank": [pagerank_dict[n] for n in nodes],
        }
    )

    logger.info(f"Calculated metrics for {len(metrics_df)} PEPs")
    logger.info(f"PageRank sum: {metrics_df['pagerank'].sum():.6f}")

    return metrics_df


def save_graph(G: nx.DiGraph, output_path: Path) -> None:
    """
    DiGraphをpickleで保存

    Args:
        G: NetworkX DiGraph
        output_path: 保存先パス
    """
    logger.info(f"Saving graph to {output_path}")

    # ディレクトリが存在しない場合は作成
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "wb") as f:
        pickle.dump(G, f)

    logger.info(f"Successfully saved graph to {output_path}")


def save_metrics(metrics_df: pd.DataFrame, output_path: Path) -> None:
    """
    メトリクスをCSVで保存

    Args:
        metrics_df: メトリクスDataFrame
        output_path: 保存先パス
    """
    logger.info(f"Saving metrics to {output_path}")

    # ディレクトリが存在しない場合は作成
    output_path.parent.mkdir(parents=True, exist_ok=True)

    metrics_df.to_csv(output_path, index=False)

    logger.info(f"Successfully saved metrics to {output_path}")


def main() -> int:
    """メイン処理"""
    # ロガー設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("Starting metrics calculation")

    # データパス設定
    project_root = Path(__file__).parent.parent
    peps_metadata_path = project_root / "data/processed/peps_metadata.csv"
    citations_path = project_root / "data/processed/citations.csv"
    metadata_path = project_root / "data/processed/metadata.json"
    graph_output_path = project_root / "data/processed/pep_graph.pkl"
    metrics_output_path = project_root / "data/processed/node_metrics.csv"

    # 必須ファイルの存在確認
    if not citations_path.exists():
        logger.error(f"Citations file not found: {citations_path}")
        return 1

    # グラフ構築（メタデータ付き）
    G = build_pep_graph(
        citations_path,
        metadata_path=metadata_path,
        peps_metadata_path=peps_metadata_path,
    )

    # メトリクス計算
    metrics_df = calculate_node_metrics(G)

    # 保存
    save_graph(G, graph_output_path)
    save_metrics(metrics_df, metrics_output_path)

    logger.info("Metrics calculation completed successfully")

    return 0


if __name__ == "__main__":
    sys.exit(main())
