"""scripts/detect_communities.py のテスト"""

import json
import pickle

import networkx as nx
import pytest


class TestDetectCommunitiesMain:
    """detect_communities.py のmain関数のテスト"""

    @pytest.fixture
    def sample_graph_file(self, temp_dir):
        """テスト用のグラフファイルを作成（サイズ2以上のコミュニティが形成されるデータ）"""
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
