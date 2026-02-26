"""scripts/calculate_metrics.py のテスト"""

import pickle

import networkx as nx
import pandas as pd
import pytest

from scripts.calculate_metrics import (
    build_pep_graph,
    calculate_node_metrics,
    save_graph,
    save_metrics,
)


class TestBuildPepGraph:
    """build_pep_graph関数のテスト（フェーズ2.1）"""

    def test_build_graph_from_csv(self, sample_data_dir):
        """citations.csvから有向グラフを正しく構築できるか"""
        # Given
        citations_path = sample_data_dir / "citations.csv"
        metadata_path = sample_data_dir / "metadata.json"

        # When
        G = build_pep_graph(citations_path, metadata_path=metadata_path)

        # Then
        assert isinstance(G, nx.DiGraph)
        assert len(G.nodes()) == 10  # サンプルデータのPEP数
        assert len(G.edges()) >= 15  # サンプルデータのエッジ数
        assert G.has_edge(1, 8)  # 特定のエッジが存在

    def test_graph_has_metadata(self, sample_data_dir):
        """グラフがメタデータ（fetched_at, source_url）を持つか"""
        # Given
        citations_path = sample_data_dir / "citations.csv"
        metadata_path = sample_data_dir / "metadata.json"

        # When
        G = build_pep_graph(citations_path, metadata_path=metadata_path)

        # Then
        assert "fetched_at" in G.graph
        assert "source_url" in G.graph
        assert G.graph["fetched_at"] == "2026-02-26T00:00:00+00:00"
        assert (
            G.graph["source_url"]
            == "https://github.com/python/peps/archive/refs/heads/main.zip"
        )

    def test_graph_excludes_self_loops(self, tmp_path):
        """自己ループが除外されているか"""
        # Given: citations.csvに自己ループ（例: 1→1）を含める
        citations_with_self_loop = tmp_path / "citations.csv"
        citations_with_self_loop.write_text(
            "citing,cited,count\n1,1,1\n1,8,1\n8,20,1\n"
        )

        # When
        G = build_pep_graph(citations_with_self_loop)

        # Then
        assert not any(u == v for u, v in G.edges())

    def test_graph_excludes_invalid_peps(self, tmp_path):
        """peps_metadata.csvに存在しないPEPが除外されるか"""
        # Given: citations.csvに存在しないPEP（例: 9999）への参照を含める
        citations_with_invalid = tmp_path / "citations.csv"
        citations_with_invalid.write_text(
            "citing,cited,count\n1,9999,1\n9999,8,1\n1,8,1\n"
        )

        valid_peps = {1, 8, 20, 234, 257, 484, 3100, 3107, 3119, 3141}

        # When
        G = build_pep_graph(citations_with_invalid, valid_peps=valid_peps)

        # Then
        assert 9999 not in G.nodes()
        assert 1 in G.nodes()
        assert 8 in G.nodes()


class TestCalculateNodeMetrics:
    """calculate_node_metrics関数のテスト（フェーズ2.3）"""

    @pytest.fixture
    def sample_graph(self):
        """テスト用のサンプルグラフ"""
        G = nx.DiGraph()
        # PEP 1: 引用なし、3つ引用している
        G.add_edge(1, 8)
        G.add_edge(1, 20)
        G.add_edge(1, 257)
        # PEP 8: 1つ引用されている、2つ引用している
        G.add_edge(8, 20)
        G.add_edge(8, 234)
        # PEP 234: 2つ引用されている、2つ引用している
        G.add_edge(20, 234)
        G.add_edge(234, 8)
        G.add_edge(234, 257)
        # その他のノードを追加
        G.add_node(257)
        G.add_node(484)
        G.add_node(3100)
        G.add_node(3107)
        G.add_node(3119)
        G.add_node(3141)
        return G

    def test_calculate_node_metrics(self, sample_graph):
        """各種メトリクスが正しく計算されるか"""
        # Given
        G = sample_graph

        # When
        metrics_df = calculate_node_metrics(G)

        # Then
        assert "pep_number" in metrics_df.columns
        assert "in_degree" in metrics_df.columns
        assert "out_degree" in metrics_df.columns
        assert "degree" in metrics_df.columns
        assert "pagerank" in metrics_df.columns

        # PEP 1のメトリクスを検証（サンプルデータから期待値を計算）
        pep1_metrics = metrics_df[metrics_df["pep_number"] == 1].iloc[0]
        assert pep1_metrics["in_degree"] == 0  # PEP 1は引用されていない
        assert pep1_metrics["out_degree"] == 3  # PEP 1は3つ引用している
        assert pep1_metrics["degree"] == 3
        assert 0.0 < pep1_metrics["pagerank"] < 1.0

    def test_pagerank_sum_is_one(self, sample_graph):
        """PageRankの合計が1.0であるか"""
        # Given
        G = sample_graph

        # When
        metrics_df = calculate_node_metrics(G)

        # Then
        total_pagerank = metrics_df["pagerank"].sum()
        assert abs(total_pagerank - 1.0) < 1e-6  # 浮動小数点誤差を考慮

    def test_metrics_include_all_nodes(self, sample_graph):
        """全ノードのメトリクスが含まれているか"""
        # Given
        G = sample_graph

        # When
        metrics_df = calculate_node_metrics(G)

        # Then
        assert len(metrics_df) == G.number_of_nodes()
        assert set(metrics_df["pep_number"]) == set(G.nodes())


class TestSaveGraph:
    """save_graph関数のテスト（フェーズ2.5）"""

    @pytest.fixture
    def sample_graph_with_metadata(self):
        """メタデータ付きのサンプルグラフ"""
        G = nx.DiGraph()
        G.add_edge(1, 8)
        G.add_edge(8, 20)
        G.graph["fetched_at"] = "2026-02-26T00:00:00+00:00"
        G.graph["source_url"] = (
            "https://github.com/python/peps/archive/refs/heads/main.zip"
        )
        return G

    def test_save_graph_pickle(self, sample_graph_with_metadata, tmp_path):
        """DiGraphがpickleで保存できるか"""
        # Given
        G = sample_graph_with_metadata
        output_path = tmp_path / "test_graph.pkl"

        # When
        save_graph(G, output_path)

        # Then
        assert output_path.exists()

        # 読み込んで検証
        with open(output_path, "rb") as f:
            loaded_G = pickle.load(f)
        assert isinstance(loaded_G, nx.DiGraph)
        assert G.number_of_nodes() == loaded_G.number_of_nodes()
        assert G.number_of_edges() == loaded_G.number_of_edges()

    def test_graph_metadata_preserved_after_pickle(
        self, sample_graph_with_metadata, tmp_path
    ):
        """pickle保存・読み込み後もメタデータが保持されるか"""
        # Given
        G = sample_graph_with_metadata
        output_path = tmp_path / "test_graph.pkl"

        # When
        save_graph(G, output_path)
        with open(output_path, "rb") as f:
            loaded_G = pickle.load(f)

        # Then
        assert "fetched_at" in loaded_G.graph
        assert "source_url" in loaded_G.graph
        assert loaded_G.graph["fetched_at"] == "2026-02-26T00:00:00+00:00"
        assert (
            loaded_G.graph["source_url"]
            == "https://github.com/python/peps/archive/refs/heads/main.zip"
        )


class TestSaveMetrics:
    """save_metrics関数のテスト（フェーズ2.5）"""

    @pytest.fixture
    def sample_metrics_df(self):
        """サンプルメトリクスDataFrame"""
        return pd.DataFrame(
            {
                "pep_number": [1, 8, 20],
                "in_degree": [0, 1, 2],
                "out_degree": [3, 2, 1],
                "degree": [3, 3, 3],
                "pagerank": [0.1, 0.2, 0.3],
            }
        )

    def test_save_metrics_csv(self, sample_metrics_df, tmp_path):
        """メトリクスがCSVで保存できるか"""
        # Given
        metrics_df = sample_metrics_df
        output_path = tmp_path / "test_metrics.csv"

        # When
        save_metrics(metrics_df, output_path)

        # Then
        assert output_path.exists()

        # 読み込んで検証
        loaded_df = pd.read_csv(output_path)
        assert list(loaded_df.columns) == [
            "pep_number",
            "in_degree",
            "out_degree",
            "degree",
            "pagerank",
        ]
        assert len(loaded_df) == len(metrics_df)
