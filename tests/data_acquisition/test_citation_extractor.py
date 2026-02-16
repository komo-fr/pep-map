"""Tests for citation extractor module."""

from pathlib import Path

import pandas as pd
import pytest

from src.data_acquisition.citation_extractor import CitationExtractor


class TestCitationExtractor:
    """Test cases for CitationExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create a CitationExtractor instance for testing."""
        return CitationExtractor()

    @pytest.fixture
    def fixtures_dir(self):
        """Get the fixtures directory path."""
        return Path(__file__).parent.parent / "fixtures"

    # Phase 2: Basic citation extraction - :pep: pattern tests (Red)

    def test_extract_single_pep_role_citation(self, extractor):
        """Test extracting a single :pep: citation."""
        content = "PEP: 1234\n\nSee :pep:`8` for details."
        result = extractor.extract_citations(content)
        assert result == [8]

    def test_extract_multiple_pep_role_citations(self, extractor):
        """Test extracting multiple :pep: citations."""
        content = "PEP: 1234\n\nSee :pep:`8` and :pep:`257`."
        result = extractor.extract_citations(content)
        assert result == [8, 257]

    def test_extract_no_citations(self, extractor):
        """Test extracting from content with no citations."""
        content = "PEP: 1234\n\nThis is a PEP without any citations."
        result = extractor.extract_citations(content)
        assert result == []

    def test_extract_citations_exclude_self(self, extractor):
        """Test extracting citations and excluding self-references."""
        content = "PEP: 8\n\nSee :pep:`8` and PEP 123for details."
        result = extractor.extract_citations(content, exclude_self=True)
        assert result == [123]

        result = extractor.extract_citations(content, exclude_self=False)
        assert result == [8, 123]

    # Phase 3: Additional citation patterns - Custom text PEP role tests (Red)

    def test_extract_pep_role_with_custom_text(self, extractor):
        """Test extracting :pep: citation with custom text."""
        content = "PEP: 1234\n\n:pep:`the style guide <8>` for details."
        result = extractor.extract_citations(content)
        assert result == [8]

    def test_extract_pep_role_with_anchor(self, extractor):
        """Test extracting :pep: citation with custom text and anchor."""
        content = "PEP: 1234\n\n:pep:`PEP 1 <1#discussing-a-pep>` section"
        result = extractor.extract_citations(content)
        assert result == [1]

    def test_extract_multiple_custom_pep_roles(self, extractor):
        """Test extracting multiple :pep: citations with custom text."""
        content = "PEP: 1234\n\n:pep:`style <8>` and :pep:`Type Hints <484>`"
        result = extractor.extract_citations(content)
        assert result == [8, 484]

    # Phase 3: Additional citation patterns - PEP NNN plain text tests (Red)

    def test_extract_pep_number_format(self, extractor):
        """Test extracting PEP citation in 'PEP NNN' format."""
        content = "PEP: 1234\n\nSee PEP 8 for guidelines."
        result = extractor.extract_citations(content)
        assert result == [8]

    def test_extract_pep_case_insensitive(self, extractor):
        """Test extracting PEP citation with case-insensitive matching."""
        content = "PEP: 1234\n\nSee pep 8 for guidelines."
        result = extractor.extract_citations(content)
        assert result == [8]

    def test_extract_mixed_pep_role_and_plain_text(self, extractor):
        """Test that plain text PEP citations are extracted but not from within :pep: roles."""
        content = "PEP: 1234\n\nSee :pep:`style guide <8>` and PEP 257 for details."
        result = extractor.extract_citations(content)
        assert result == [8, 257]

    # Phase 3: Additional citation patterns - URL PEP number tests (Red)

    def test_extract_pep_from_url(self, extractor):
        """Test extracting PEP citation from URL."""
        content = "PEP: 1234\n\nSee https://peps.python.org/pep-0257/ for details."
        result = extractor.extract_citations(content)
        assert result == [257]

        content = "PEP: 1234\n\nSee https://peps.python.org/pep-8001/ for details."
        result = extractor.extract_citations(content)
        assert result == [8001]

    def test_extract_pep_from_url_with_anchor(self, extractor):
        """Test extracting PEP citation from URL with anchor."""
        content = "PEP: 1234\n\n.. _link: https://peps.python.org/pep-0445/#gil-free"
        result = extractor.extract_citations(content)
        assert result == [445]

    def test_extract_multiple_peps_from_urls(self, extractor):
        """Test extracting multiple PEP citations from URLs."""
        content = "PEP: 1234\n\nSee https://peps.python.org/pep-0008/ and https://peps.python.org/pep-0257/#specification for details."
        result = extractor.extract_citations(content)
        assert result == [8, 257]

    # Phase 3: Additional citation patterns - Requires field tests (Red)

    def test_extract_requires_single(self, extractor):
        """Test extracting single PEP from Requires field."""
        content = """PEP: 1234
Title: Test PEP
Author: Test Author
Status: Draft
Type: Standards Track
Created: 01-Jan-2020
Requires: 532

Content here."""
        result = extractor._extract_requires_field(content)
        assert result == [532]

    def test_extract_requires_multiple(self, extractor):
        """Test extracting multiple PEPs from Requires field."""
        content = """PEP: 1234
Title: Test PEP
Author: Test Author
Status: Draft
Type: Standards Track
Created: 01-Jan-2020
Requires: 489, 573, 630

Content here."""
        result = extractor._extract_requires_field(content)
        assert result == [489, 573, 630]

    def test_extract_requires_none(self, extractor):
        """Test extracting from content without Requires field."""
        content = """PEP: 1234
Title: Test PEP
Author: Test Author
Status: Draft
Type: Standards Track
Created: 01-Jan-2020

Content here."""
        result = extractor._extract_requires_field(content)
        assert result == []

    # Phase 3: Additional citation patterns - Replaces field tests (Red)

    def test_extract_replaces_single(self, extractor):
        """Test extracting single PEP from Replaces field."""
        content = """PEP: 1234
Title: Test PEP
Author: Test Author
Status: Draft
Type: Standards Track
Created: 01-Jan-2020
Replaces: 123

Content here."""
        result = extractor._extract_replaces_field(content)
        assert result == [123]

    def test_extract_replaces_multiple(self, extractor):
        """Test extracting multiple PEPs from Replaces field."""
        content = """PEP: 1234
Title: Test PEP
Author: Test Author
Status: Draft
Type: Standards Track
Created: 01-Jan-2020
Replaces: 123, 456, 789

Content here."""
        result = extractor._extract_replaces_field(content)
        assert result == [123, 456, 789]

    def test_extract_replaces_none(self, extractor):
        """Test extracting from content without Replaces field."""
        content = """PEP: 1234
Title: Test PEP
Author: Test Author
Status: Draft
Type: Standards Track
Created: 01-Jan-2020

Content here."""
        result = extractor._extract_replaces_field(content)
        assert result == []

    # Phase 4: File-based citation extraction tests (Red)

    def test_extract_from_file(self, extractor, fixtures_dir):
        """Test extracting citations from a file."""
        file_path = fixtures_dir / "pep-with-citations.rst"
        result = extractor.extract_from_file(file_path)

        # Expected citations from pep-with-citations.rst (PEP 9999):
        # - Requires: 489, 573
        # - Replaces: 123, 456
        # - Body citations: 8, 257, 20, 1, 3107, 484, 526, 445
        expected_peps = [1, 8, 20, 123, 257, 445, 456, 484, 489, 526, 573, 3107]

        assert 9999 in result
        # Check that all expected PEPs are present
        assert sorted(result[9999].keys()) == sorted(expected_peps)
        # Each PEP should have a count >= 1
        for pep in expected_peps:
            assert result[9999][pep] >= 1

    def test_exclude_self_reference(self, extractor, fixtures_dir):
        """Test that self-references are excluded from citations."""
        file_path = fixtures_dir / "pep-0008.rst"
        result = extractor.extract_from_file(file_path)

        # PEP 8 should not cite itself even if "PEP 8" appears in the text
        assert 8 in result
        # Check that 8 is not in the cited PEPs (dict keys)
        assert 8 not in result[8].keys()

    # Phase 5: Citation counting tests (Red)

    def test_count_multiple_citations_to_same_pep(self, extractor):
        """Test counting multiple citations to the same PEP."""
        content = """PEP: 123
See :pep:`8` and :pep:`257`. Also PEP 8.
"""
        result = extractor.count_citations(content)

        # PEP 8 is cited twice, PEP 257 once
        assert result == {8: 2, 257: 1}

    def test_count_citations_exclude_self(self, extractor):
        """Test counting citations and excluding self-references."""
        content = """PEP: 8\n\nSee :pep:`8` and PEP 123 for details."""
        result = extractor.count_citations(content, exclude_self=True)
        assert result == {123: 1}

        result = extractor.count_citations(content, exclude_self=False)
        assert result == {8: 1, 123: 1}

    def test_count(self, extractor):
        content = """
PEP: 1234
Title: Test PEP
Author: Test Author
Status: Draft
Type: Standards Track
Created: 01-Jan-2020
Requires: 8, 573
Replaces: 8, 456

See :pep:`8` and :pep:`8`. Also PEP 8.
:pep:`PEP 8 <8#discussing-a-pep>` section
See :pep:`style guide <8>` for details.
See https://peps.python.org/pep-0008/ and https://peps.python.org/pep-0008/#specification for details.
".. _link: https://peps.python.org/pep-0008/#gil-free"
See https://peps.python.org/pep-0008/ for details.
"""
        result = extractor.count_citations(content)
        assert result == {8: 11, 573: 1, 456: 1}

    # Phase 6: Multiple file processing tests (Red)

    def test_extract_from_multiple_files(self, extractor, fixtures_dir):
        """Test extracting citations from multiple files."""
        file_paths = [
            fixtures_dir / "pep-with-citations.rst",
            fixtures_dir / "pep-0008.rst",
        ]
        result = extractor.extract_from_multiple_files(file_paths)

        # Result should be a DataFrame
        assert isinstance(result, pd.DataFrame)

        # DataFrame should have the expected columns
        assert list(result.columns) == ["citing", "cited", "count"]

        # DataFrame should contain data from both files
        assert len(result) > 0

        # Check that PEP 9999 citations are included
        pep_9999_citations = result[result["citing"] == 9999]
        assert len(pep_9999_citations) > 0

    def test_dataframe_structure(self, extractor, fixtures_dir):
        """Test that the DataFrame has correct structure."""
        file_paths = [fixtures_dir / "pep-with-citations.rst"]
        result = extractor.extract_from_multiple_files(file_paths)

        # Check column names
        assert list(result.columns) == ["citing", "cited", "count"]

        # Check data types - all should be integers
        assert result["citing"].dtype == int
        assert result["cited"].dtype == int
        assert result["count"].dtype == int

        # Check that all counts are positive
        assert (result["count"] > 0).all()

    def test_extract_from_empty_file_list(self, extractor):
        """Test extracting from an empty file list."""
        result = extractor.extract_from_multiple_files([])

        # Result should be an empty DataFrame
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

        # But should still have the correct columns
        assert list(result.columns) == ["citing", "cited", "count"]

    # Phase 7: CSV output tests (Red)

    def test_save_to_csv(self, extractor, fixtures_dir, tmp_path):
        """Test saving citations to CSV file."""
        # Extract citations from a file
        file_paths = [fixtures_dir / "pep-with-citations.rst"]
        df = extractor.extract_from_multiple_files(file_paths)

        # Save to CSV
        output_path = tmp_path / "citations.csv"
        extractor.save_to_csv(df, output_path)

        # Check that file was created
        assert output_path.exists()

        # Read the CSV file and verify content
        saved_df = pd.read_csv(output_path)
        assert len(saved_df) == len(df)
        assert list(saved_df.columns) == ["citing", "cited", "count"]

    def test_csv_format(self, extractor, fixtures_dir, tmp_path):
        """Test CSV file format."""
        # Create a simple DataFrame
        file_paths = [fixtures_dir / "pep-with-citations.rst"]
        df = extractor.extract_from_multiple_files(file_paths)

        # Save to CSV
        output_path = tmp_path / "citations.csv"
        extractor.save_to_csv(df, output_path)

        # Read the file as text to check format
        with output_path.open("r") as f:
            lines = f.readlines()

        # Check header line
        assert lines[0].strip() == "citing,cited,count"

        # Check that there's no index column (no leading numbers)
        if len(lines) > 1:
            # Data lines should not start with a number followed by comma
            # They should start with citing PEP number
            assert not lines[1].startswith("0,")

    def test_save_to_csv_create_directory(self, extractor, tmp_path):
        """Test that parent directory is created if it doesn't exist."""
        # Create a nested path that doesn't exist
        output_path = tmp_path / "nested" / "dir" / "citations.csv"

        # Create an empty DataFrame
        df = pd.DataFrame(columns=["citing", "cited", "count"])

        # Save should create the directory
        extractor.save_to_csv(df, output_path)

        # Check that file and directories were created
        assert output_path.exists()
        assert output_path.parent.exists()
