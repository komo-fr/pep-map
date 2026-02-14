"""Citation extractor for PEP files.

This module provides functionality to extract PEP citations from RST content.
"""

import re
from collections import Counter
from pathlib import Path

import pandas as pd

from src.data_acquisition.rst_parser import RSTParser


class CitationExtractor:
    """Extract PEP citations from RST content.

    This class provides methods to extract PEP-to-PEP citations from
    reStructuredText files, identifying various citation patterns.
    """

    def __init__(self):
        """Initialize the CitationExtractor."""
        # Compile regex pattern for :pep:`NNN` format
        self.simple_pep_role_pattern = re.compile(r":pep:`(\d+)`")
        # Compile regex pattern for :pep:`custom text <NNN>` or :pep:`text <NNN#anchor>` format
        self.custom_text_pep_role_pattern = re.compile(
            r":pep:`[^`]*<(\d+)(?:#[^>]*)?>`"
        )
        # Compile regex pattern for plain text PEP NNN format (case-insensitive)
        # Use negative lookbehind to avoid matching within :pep: roles
        self.plain_text_pep_pattern = re.compile(r"(?<!`)PEP\s+(\d+)", re.IGNORECASE)
        # Compile regex pattern for URL PEP format
        self.url_pep_pattern = re.compile(r"https://peps\.python\.org/pep-0*(\d+)")

    def extract_citations(self, content: str, exclude_self: bool = True) -> list[int]:
        """Extract cited PEP numbers from content.

        Supports the following patterns:
        - Simple :pep:`NNN` pattern
        - Custom text :pep:`text <NNN>` pattern
        - Custom text with anchor :pep:`text <NNN#anchor>` pattern
        - Plain text PEP NNN pattern (case-insensitive)
        - URL https://peps.python.org/pep-NNN/ pattern
        - Requires field
        - Replaces field

        Args:
            content: RST content to extract citations from
            exclude_self: Whether to exclude self-references

        Returns:
            List of cited PEP numbers as integers
        """
        citations = []

        # Match simple :pep:`NNN` pattern
        for match in self.simple_pep_role_pattern.finditer(content):
            pep_number = int(match.group(1))
            citations.append(pep_number)

        # Match custom text :pep:`text <NNN>` or :pep:`text <NNN#anchor>` pattern
        for match in self.custom_text_pep_role_pattern.finditer(content):
            pep_number = int(match.group(1))
            citations.append(pep_number)

        # Match plain text PEP NNN pattern (case-insensitive)
        for match in self.plain_text_pep_pattern.finditer(content):
            pep_number = int(match.group(1))
            citations.append(pep_number)

        # Match URL https://peps.python.org/pep-NNN/ pattern
        for match in self.url_pep_pattern.finditer(content):
            pep_number = int(match.group(1))
            citations.append(pep_number)

        citations += self._extract_requires_field(content)
        citations += self._extract_replaces_field(content)

        # Exclude self-references
        parser = RSTParser()
        source_pep = parser.extract_pep_number(content)
        if exclude_self and source_pep in citations:
            citations.remove(source_pep)

        return citations

    def _extract_requires_field(self, content: str) -> list[int]:
        """Extract PEP numbers from the Requires header field.

        Args:
            content: RST content to extract Requires field from

        Returns:
            List of required PEP numbers as integers, or empty list if no Requires field
        """
        parser = RSTParser()
        requires_value = parser.parse_header_field(content, "Requires")

        if requires_value is None:
            return []

        return parser.parse_requires_peps(requires_value)

    def _extract_replaces_field(self, content: str) -> list[int]:
        """Extract PEP numbers from the Replaces header field.

        Args:
            content: RST content to extract Replaces field from

        Returns:
            List of replaced PEP numbers as integers, or empty list if no Replaces field
        """
        parser = RSTParser()
        replaces_value = parser.parse_header_field(content, "Replaces")

        if replaces_value is None:
            return []

        return parser.parse_replaces_peps(replaces_value)

    def count_citations(
        self, content: str, exclude_self: bool = True
    ) -> dict[int, int]:
        """Count citations in content.

        Args:
            content: RST content to count citations from
            exclude_self: Whether to exclude self-references

        Returns:
            Dictionary mapping PEP numbers to citation counts
        """
        citations = self.extract_citations(content, exclude_self=exclude_self)
        return dict(Counter(citations))

    def extract_from_file(
        self, file_path: Path, exclude_self: bool = True
    ) -> dict[int, dict[int, int]]:
        """Extract citations from a PEP file with counts.

        Args:
            file_path: Path to the PEP RST file

        Returns:
            Dictionary mapping source PEP number to dictionary of cited PEP numbers
            and their counts (excluding self-references)
        """
        # Read file content
        content = file_path.read_text(encoding="utf-8")

        # Extract source PEP number from the file
        parser = RSTParser()
        source_pep = parser.extract_pep_number(content)

        # Extract citations
        citations = self.extract_citations(content, exclude_self)

        # Count citations using Counter
        citation_counts = Counter(citations)

        return {source_pep: dict(citation_counts)}

    def extract_from_multiple_files(self, file_paths: list[Path]) -> pd.DataFrame:
        """Extract citations from multiple PEP files.

        Args:
            file_paths: List of paths to PEP RST files

        Returns:
            DataFrame with columns: source, target, count
        """
        # Prepare list to collect all citation records
        records = []

        # Process each file
        for file_path in file_paths:
            # Extract citations from the file
            file_citations = self.extract_from_file(file_path)

            # Convert to DataFrame records
            for source_pep, citations in file_citations.items():
                for target_pep, count in citations.items():
                    records.append(
                        {"source": source_pep, "target": target_pep, "count": count}
                    )

        # Create DataFrame
        if records:
            df = pd.DataFrame(records)
        else:
            # Return empty DataFrame with correct columns
            df = pd.DataFrame(columns=["source", "target", "count"])

        # Ensure correct data types
        if len(df) > 0:
            df = df.astype({"source": int, "target": int, "count": int})

        return df

    def save_to_csv(self, citations_df: pd.DataFrame, output_path: Path) -> None:
        """Save citations DataFrame to CSV file.

        Args:
            citations_df: DataFrame with columns: source, target, count
            output_path: Path where the CSV file should be saved

        Note:
            Creates parent directories if they don't exist.
        """
        # Create parent directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save to CSV without index
        citations_df.to_csv(output_path, index=False)
