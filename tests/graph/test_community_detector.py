"""src/graph/community_detector.py のテスト"""

import networkx as nx
import pytest

from src.graph.community_detector import (
    run_louvain_detection,
    create_pep_group_metrics,
    create_group_metrics,
    calculate_detection_stats,
    generate_subgraph_images,
)


@pytest.fixture
def sample_graph():
    """テスト用のサンプルグラフ（コミュニティが形成されるデータ）"""
    G = nx.DiGraph()
    # コミュニティ1: PEP 1, 8, 20, 234, 257（相互に引用）
    G.add_edge(1, 8)
    G.add_edge(1, 20)
    G.add_edge(1, 257)
    G.add_edge(8, 20)
    G.add_edge(8, 234)
    G.add_edge(20, 234)
    G.add_edge(234, 8)
    G.add_edge(234, 257)
    G.add_edge(257, 1)
    # コミュニティ2: PEP 484, 3107, 3119, 3141（typing関連）
    G.add_edge(484, 3107)
    G.add_edge(484, 3119)
    G.add_edge(3107, 484)
    G.add_edge(3119, 3107)
    G.add_edge(3119, 3141)
    G.add_edge(3141, 3119)
    # 孤立ノード: PEP 3100
    G.add_node(3100)
    return G


@pytest.fixture
def sample_metadata_csv(tmp_path):
    """テスト用のメタデータCSV"""
    csv_path = tmp_path / "peps_metadata.csv"
    csv_path.write_text(
        "pep_number,title,status,type,created,authors,topic,requires,replaces\n"
        "1,PEP Purpose,Active,Process,2000-06-13,Barry Warsaw,,,\n"
        "8,Style Guide,Active,Process,2001-07-05,Guido van Rossum,,,\n"
        "20,Zen of Python,Active,Informational,2004-08-19,Tim Peters,,,\n"
        "234,Iterators,Final,Standards Track,2000-03-03,Ka-Ping Yee,,,\n"
        "257,Docstring,Active,Informational,2001-05-29,David Goodger,,,\n"
        "484,Type Hints,Final,Standards Track,2014-09-29,Guido van Rossum,typing,,\n"
        "3100,Python 3.0,Final,Process,2006-04-17,Brett Cannon,,,\n"
        "3107,Annotations,Final,Standards Track,2006-12-02,Collin Winter,typing,,\n"
        "3119,ABCs,Final,Standards Track,2007-04-04,Guido van Rossum,typing,,\n"
        "3141,Numbers,Final,Standards Track,2007-04-23,Jeffrey Yasskin,typing,,\n"
        "9999,Not in Graph,Draft,Process,2025-01-01,Test Author,,,\n"
    )
    return csv_path


class TestRunLouvainDetection:
    """run_louvain_detection関数のテスト"""

    def test_results_sorted_by_size_descending(self, sample_graph):
        """結果がサイズ降順でソートされている"""
        # When
        communities = run_louvain_detection(sample_graph)

        # Then
        sizes = [len(c) for c in communities]
        assert sizes == sorted(sizes, reverse=True)


class TestCreatePepGroupMetrics:
    """create_pep_group_metrics関数のテスト"""

    def test_isolated_peps_have_group_id_minus_one(
        self, sample_graph, sample_metadata_csv
    ):
        """孤立点（サイズ1のコミュニティ）は group_id=最大値のグループID+1"""
        # Given
        communities = run_louvain_detection(sample_graph)

        # When
        df = create_pep_group_metrics(communities, sample_graph, sample_metadata_csv)

        # Then
        # PEP 3100 は孤立ノード
        pep_3100 = df[df["PEP"] == 3100]
        assert len(pep_3100) == 1
        assert pep_3100.iloc[0]["group_id"] == 3


class TestCreateGroupMetrics:
    """create_group_metrics関数のテスト"""

    def test_isolated_communities_excluded(self, sample_graph):
        """孤立点（サイズ1）は除外される"""
        # Given
        communities = run_louvain_detection(sample_graph)

        # When
        df = create_group_metrics(communities, sample_graph)

        # Then
        # 全てのコミュニティのpep_countが2以上
        assert (df["pep_count"] >= 2).all()
        # 孤立ノード（PEP 3100）を含むコミュニティは除外されている
        assert len(df) < len(communities)


class TestCalculateDetectionStats:
    """calculate_detection_stats関数のテスト"""

    def test_stats_include_modularity_and_size_statistics(self, sample_graph):
        """モジュラリティとサイズ統計が含まれる"""
        # Given
        communities = run_louvain_detection(sample_graph)

        # When
        stats = calculate_detection_stats(communities, sample_graph)

        # Then
        assert "modularity" in stats
        assert "total_communities" in stats
        assert "max_community_size" in stats
        assert "min_community_size" in stats
        assert "avg_community_size" in stats
        assert isinstance(stats["modularity"], float)


class TestGenerateSubgraphImages:
    """generate_subgraph_images関数のテスト"""

    def test_generates_images_for_non_isolated_communities(
        self, sample_graph, tmp_path
    ):
        """孤立点以外のコミュニティに対して group_{id}.png が生成される"""
        # Given
        communities = run_louvain_detection(sample_graph)
        output_dir = tmp_path / "subgraphs" / "images"
        status_color_map = {
            "Active": "#F27398",
            "Final": "#58BE89",
            "Draft": "#FBA848",
        }

        # When
        generated_paths = generate_subgraph_images(
            communities, sample_graph, output_dir, status_color_map
        )

        # Then
        # 孤立点以外のコミュニティ数だけ画像が生成される
        non_isolated_count = sum(1 for c in communities if len(c) > 1)
        assert len(generated_paths) == non_isolated_count
        # ファイル名が group_{id}.png 形式
        for path in generated_paths:
            assert path.name.startswith("group_")
            assert path.name.endswith(".png")
            assert path.exists()
