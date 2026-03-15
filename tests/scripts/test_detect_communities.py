"""scripts/detect_communities.py のテスト"""

import json
import pickle

import networkx as nx
import pytest


class TestDetectCommunitiesMain:
    """detect_communities.py のmain関数のテスト"""

    @pytest.fixture
    def sample_graph_file(self, temp_dir):
        """テスト用のグラフファイルを作成"""
        G = nx.DiGraph()
        # コミュニティ1
        G.add_edge(1, 8)
        G.add_edge(8, 1)
        # コミュニティ2
        G.add_edge(484, 3107)
        G.add_edge(3107, 484)
        # 孤立ノード
        G.add_node(3100)

        # ノード属性を設定
        for node in G.nodes():
            G.nodes[node]["status"] = "Final"
            G.nodes[node]["title"] = f"PEP {node}"
            G.nodes[node]["created"] = "2000-01-01"

        graph_path = temp_dir / "pep_graph.pkl"
        with open(graph_path, "wb") as f:
            pickle.dump(G, f)
        return graph_path

    @pytest.fixture
    def sample_metadata_file(self, temp_dir):
        """テスト用のメタデータファイルを作成"""
        csv_path = temp_dir / "peps_metadata.csv"
        csv_path.write_text(
            "pep_number,title,status,type,created,authors,topic,requires,replaces\n"
            "1,PEP 1,Final,Process,2000-01-01,Author,,,\n"
            "8,PEP 8,Final,Process,2000-01-01,Author,,,\n"
            "484,PEP 484,Final,Standards Track,2014-09-29,Author,typing,,\n"
            "3100,PEP 3100,Final,Process,2006-04-17,Author,,,\n"
            "3107,PEP 3107,Final,Standards Track,2006-12-02,Author,typing,,\n"
        )
        return csv_path

    def test_exit_code_1_when_graph_not_found(self, temp_dir, monkeypatch):
        """pep_graph.pkl が存在しない場合はエラー終了（exit code 1）"""
        from scripts.detect_communities import main

        # 存在しないパスを設定
        monkeypatch.setattr(
            "scripts.detect_communities.GRAPH_FILE",
            temp_dir / "nonexistent.pkl",
        )

        # When
        result = main()

        # Then
        assert result == 1

    def test_exit_code_0_on_success(
        self, temp_dir, sample_graph_file, sample_metadata_file, monkeypatch
    ):
        """正常終了時は exit code 0"""
        from scripts.detect_communities import main

        # パスを設定
        monkeypatch.setattr(
            "scripts.detect_communities.GRAPH_FILE",
            sample_graph_file,
        )
        monkeypatch.setattr(
            "scripts.detect_communities.METADATA_FILE",
            sample_metadata_file,
        )
        monkeypatch.setattr(
            "scripts.detect_communities.OUTPUT_DIR",
            temp_dir / "groups",
        )

        # When
        result = main()

        # Then
        assert result == 0

    def test_output_files_generated(
        self, temp_dir, sample_graph_file, sample_metadata_file, monkeypatch
    ):
        """出力ファイルが正しいパスに生成される"""
        from scripts.detect_communities import main

        output_dir = temp_dir / "groups"

        # パスを設定
        monkeypatch.setattr(
            "scripts.detect_communities.GRAPH_FILE",
            sample_graph_file,
        )
        monkeypatch.setattr(
            "scripts.detect_communities.METADATA_FILE",
            sample_metadata_file,
        )
        monkeypatch.setattr(
            "scripts.detect_communities.OUTPUT_DIR",
            output_dir,
        )

        # When
        main()

        # Then
        assert (output_dir / "pep_group_metrics.csv").exists()
        assert (output_dir / "group_metrics.csv").exists()
        assert (output_dir / "detection_metadata.json").exists()
        assert (output_dir / "subgraphs" / "images").exists()

        # JSONファイルの内容を確認
        with open(output_dir / "detection_metadata.json") as f:
            metadata = json.load(f)
        assert "algorithm" in metadata
        assert "parameters" in metadata
        assert "statistics" in metadata
        assert "detected_at" in metadata
