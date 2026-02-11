"""Citation extractor for PEP files.

This module provides functionality to extract PEP citations from RST content.
"""

import re
from typing import List


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

    def extract_citations(self, content: str) -> List[int]:
        """Extract cited PEP numbers from content.

        Supports the following patterns:
        - Simple :pep:`NNN` pattern
        - Custom text :pep:`text <NNN>` pattern
        - Custom text with anchor :pep:`text <NNN#anchor>` pattern
        - Plain text PEP NNN pattern (case-insensitive)

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

        return citations
