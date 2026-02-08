"""RST parser for extracting PEP metadata from RST files."""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PEPMetadata:
    """Metadata extracted from a PEP document."""

    pep_number: int
    title: str
    status: str
    type: str
    created: Optional[str]  # ISO format date string, or None if empty
    authors: List[str]


class RSTParser:
    """Parser for extracting metadata from PEP RST files."""

    def __init__(self):
        """Initialize RSTParser."""
        pass

    def extract_pep_number(self, file_path: Path) -> int:
        """
        Extract PEP number from filename.

        Args:
            file_path: Path to the PEP file (e.g., pep-0001.rst)

        Returns:
            PEP number as integer

        Raises:
            ValueError: If filename doesn't match expected pattern
            IndexError: If filename structure is invalid
        """
        # Expected format: pep-NNNN.rst
        filename = file_path.stem  # Get filename without extension
        parts = filename.split("-")

        if len(parts) != 2 or parts[0] != "pep":
            raise ValueError(f"Invalid PEP filename format: {file_path.name}")

        try:
            pep_number = int(parts[1])
            return pep_number
        except ValueError as e:
            raise ValueError(f"Could not parse PEP number from {file_path.name}") from e

    def parse_header_field(self, content: str, field_name: str) -> Optional[str]:
        """
        Parse a specific header field from RST content.

        Args:
            content: The RST file content
            field_name: Name of the field to extract (e.g., "Title", "Author")

        Returns:
            The field value as a string, or None if not found

        Note:
            Handles multi-line field values that are indented with spaces.
        """
        lines = content.split("\n")
        field_value_lines = []
        in_field = False
        field_pattern = re.compile(rf"^{re.escape(field_name)}:\s*(.*)$", re.IGNORECASE)

        for i, line in enumerate(lines):
            # Check if this line starts the field we're looking for
            match = field_pattern.match(line)
            if match:
                in_field = True
                # Get the value on the same line as the field name
                value = match.group(1).strip()
                if value:
                    field_value_lines.append(value)
                continue

            # If we're in a field, check for continuation lines
            if in_field:
                # Continuation lines start with whitespace
                if line and (line[0] == " " or line[0] == "\t"):
                    field_value_lines.append(line.strip())
                else:
                    # We've reached the end of this field
                    break

        if not field_value_lines:
            return None

        # Join multi-line values
        return " ".join(field_value_lines)

    def _parse_authors(self, author_string: str) -> List[str]:
        """
        Parse author string into a list of author names.

        Args:
            author_string: String containing one or more authors

        Returns:
            List of author names (without email addresses)

        Example:
            "Barry Warsaw <barry@python.org>, Jeremy Hylton <jeremy@alum.mit.edu>"
            -> ["Barry Warsaw", "Jeremy Hylton"]
        """
        # Remove email addresses (text in angle brackets)
        author_string = re.sub(r"<[^>]+>", "", author_string)

        # Split by comma
        authors = [author.strip() for author in author_string.split(",")]

        # Filter out empty strings
        authors = [author for author in authors if author]

        return authors

    def parse_pep_file(self, file_path: Path) -> PEPMetadata:
        """
        Parse a PEP RST file and extract metadata.

        Args:
            file_path: Path to the PEP RST file

        Returns:
            PEPMetadata object containing extracted metadata

        Raises:
            ValueError: If required fields are missing or file is malformed
            KeyError: If required fields cannot be found
        """
        logger.info(f"Parsing PEP file: {file_path}")

        # Read file content
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            raise

        # Extract PEP number from filename
        pep_number = self.extract_pep_number(file_path)

        # Extract required fields
        title = self.parse_header_field(content, "Title")
        status = self.parse_header_field(content, "Status")
        pep_type = self.parse_header_field(content, "Type")
        created = self.parse_header_field(content, "Created")
        author_string = self.parse_header_field(content, "Author")

        # Validate required fields
        if not title:
            raise ValueError(
                f"Missing required field 'Title' in PEP {pep_number} ({file_path})"
            )
        if not status:
            raise ValueError(
                f"Missing required field 'Status' in PEP {pep_number} ({file_path})"
            )
        if not pep_type:
            raise ValueError(
                f"Missing required field 'Type' in in PEP {pep_number} ({file_path})"
            )
        if not author_string:
            raise ValueError(
                f"Missing required field 'Author' in in PEP {pep_number} ({file_path})"
            )

        # Parse authors
        authors = self._parse_authors(author_string)

        # Handle empty Created field
        if created is not None and created.strip() == "":
            created = None

        metadata = PEPMetadata(
            pep_number=pep_number,
            title=title,
            status=status,
            type=pep_type,
            created=created,
            authors=authors,
        )

        logger.debug(f"Successfully parsed PEP {pep_number}: {title}")
        return metadata

    def parse_multiple_peps(self, file_paths: List[Path]) -> List[PEPMetadata]:
        """
        Parse multiple PEP files and return a list of metadata.

        Args:
            file_paths: List of paths to PEP RST files

        Returns:
            List of PEPMetadata objects for successfully parsed files

        Note:
            If a file fails to parse, it will be skipped and logged as an error.
            The parsing continues with the remaining files.
        """
        results = []
        errors = 0

        for file_path in file_paths:
            try:
                metadata = self.parse_pep_file(file_path)
                results.append(metadata)
            except Exception as e:
                logger.error(f"Failed to parse {file_path}: {e}")
                errors += 1
                continue

        logger.info(f"Parsed {len(results)} PEPs successfully, {errors} files failed")

        return results
