"""Citation extractor for PEP files.

This module provides functionality to extract PEP citations from RST content.
"""

import re
from collections import Counter
from pathlib import Path
from typing import Dict, List

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

    def extract_citations(self, content: str) -> List[int]:
        """Extract cited PEP numbers from content.

        Supports the following patterns:
        - Simple :pep:`NNN` pattern
        - Custom text :pep:`text <NNN>` pattern
        - Custom text with anchor :pep:`text <NNN#anchor>` pattern
        - Plain text PEP NNN pattern (case-insensitive)
        - URL https://peps.python.org/pep-NNN/ pattern

        Args:
            content: RST content to extract citations from

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

        return citations

    def extract_requires_field(self, content: str, parser: RSTParser) -> List[int]:
        """Extract PEP numbers from the Requires header field.

        Args:
            content: RST content to extract Requires field from
            parser: RSTParser instance to use for parsing

        Returns:
            List of required PEP numbers as integers, or empty list if no Requires field
        """
        requires_value = parser.parse_header_field(content, "Requires")

        if requires_value is None:
            return []

        return parser._parse_requires_peps(requires_value)

    def extract_replaces_field(self, content: str, parser: RSTParser) -> List[int]:
        """Extract PEP numbers from the Replaces header field.

        Args:
            content: RST content to extract Replaces field from
            parser: RSTParser instance to use for parsing

        Returns:
            List of replaced PEP numbers as integers, or empty list if no Replaces field
        """
        replaces_value = parser.parse_header_field(content, "Replaces")

        if replaces_value is None:
            return []

        return parser._parse_replaces_peps(replaces_value)

    def count_citations(self, content: str) -> Dict[int, int]:
        """Count citations in content.

        Args:
            content: RST content to count citations from

        Returns:
            Dictionary mapping PEP numbers to citation counts
        """
        citations = self.extract_citations(content)
        return dict(Counter(citations))

    def extract_from_file(
        self, file_path: Path, parser: RSTParser
    ) -> Dict[int, Dict[int, int]]:
        """Extract citations from a PEP file with counts.

        Args:
            file_path: Path to the PEP RST file
            parser: RSTParser instance to use for parsing

        Returns:
            Dictionary mapping source PEP number to dictionary of cited PEP numbers
            and their counts (excluding self-references)
        """
        # Read file content
        content = file_path.read_text(encoding="utf-8")

        # Extract source PEP number from the file
        source_pep = parser.extract_pep_number(content)

        # Extract citations from body
        body_citations = self.extract_citations(content)

        # Extract citations from Requires field
        requires_citations = self.extract_requires_field(content, parser)

        # Extract citations from Replaces field
        replaces_citations = self.extract_replaces_field(content, parser)

        # Combine all citations
        all_citations = body_citations + requires_citations + replaces_citations

        # Count citations using Counter
        citation_counts = Counter(all_citations)

        # Exclude self-references
        if source_pep in citation_counts:
            del citation_counts[source_pep]

        return {source_pep: dict(citation_counts)}
