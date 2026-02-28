"""PEP parser for extracting metadata from PEP RST files."""

import logging
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import pandas as pd


logger = logging.getLogger(__name__)


@dataclass
class PEPMetadata:
    """Metadata extracted from a PEP document."""

    pep_number: int
    title: str
    status: str
    type: str
    created: Optional[str]  # ISO format date string, or None if empty
    authors: list[str]
    topic: Optional[list[str]] = None
    requires: Optional[list[int]] = None
    replaces: Optional[list[int]] = None


class PEPParser:
    """Parser for extracting metadata from PEP RST files."""

    def extract_pep_number(self, content: str) -> int:
        """
        Extract PEP number from RST metadata (the value after "PEP:").

        Args:
            content: The RST file content (must contain a "PEP: N" header field)

        Returns:
            PEP number as integer

        Raises:
            ValueError: If "PEP:" field is missing or value is not a valid integer
        """
        pep_value = self.parse_header_field(content, "PEP")
        if pep_value is None or not pep_value.strip():
            raise ValueError("Missing or empty 'PEP:' field in document")

        try:
            pep_number = int(pep_value.strip())
            return pep_number
        except ValueError as e:
            raise ValueError(
                f"Could not parse PEP number from 'PEP:' field (got: {pep_value!r})"
            ) from e

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

    def _parse_authors(self, author_string: str) -> list[str]:
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

    def _parse_topics(self, topic_string: str) -> list[str]:
        """
        Parse topic string into a list of topics.

        Args:
            topic_string: String containing one or more topics

        Returns:
            List of topic names

        Example:
            "Governance, Packaging" -> ["Governance", "Packaging"]
            "Typing" -> ["Typing"]
            "" -> []
        """
        # 空文字列の場合は空リストを返す
        if not topic_string or not topic_string.strip():
            return []

        # カンマで分割
        topics = [topic.strip() for topic in topic_string.split(",")]

        # 空文字列を除外
        topics = [topic for topic in topics if topic]

        return topics

    def _parse_pep_numbers(self, pep_string: str, field_name: str) -> list[int]:
        """
        Parse a comma-separated string of PEP numbers into a list of integers.

        Args:
            pep_string: String containing one or more PEP numbers
            field_name: Name of the field (for error messages)

        Returns:
            List of PEP numbers as integers

        Raises:
            ValueError: If any PEP number is invalid (not a positive integer)

        Example:
            "234" -> [234]
            "440, 508, 518" -> [440, 508, 518]
            "" -> []
        """
        # 空文字列の場合は空リストを返す
        if not pep_string or not pep_string.strip():
            return []

        # カンマで分割し、空文字列を除外
        pep_strings = [pep.strip() for pep in pep_string.split(",") if pep.strip()]

        # 各PEP番号を整数に変換
        pep_numbers = []
        for pep_str in pep_strings:
            try:
                pep_num = int(pep_str)
                # PEP番号は正の整数でなければならない
                if pep_num <= 0:
                    raise ValueError("non-positive PEP number")
                pep_numbers.append(pep_num)
            except ValueError as e:
                raise ValueError(
                    f"Invalid PEP number in {field_name} field: '{pep_str}' "
                    f"(must be a positive integer)"
                ) from e

        return pep_numbers

    def parse_requires_peps(self, requires_string: str) -> list[int]:
        """
        Parse Requires field string into a list of PEP numbers.

        Args:
            requires_string: String containing one or more PEP numbers

        Returns:
            List of PEP numbers as integers

        Raises:
            ValueError: If any PEP number is invalid (not a positive integer)

        Example:
            "234" -> [234]
            "440, 508, 518" -> [440, 508, 518]
            "" -> []
        """
        return self._parse_pep_numbers(requires_string, "Requires")

    def parse_replaces_peps(self, replaces_string: str) -> list[int]:
        """
        Parse Replaces field string into a list of PEP numbers.

        Args:
            replaces_string: String containing one or more PEP numbers

        Returns:
            List of PEP numbers as integers

        Raises:
            ValueError: If any PEP number is invalid (not a positive integer)

        Example:
            "102" -> [102]
            "245, 246" -> [245, 246]
            "" -> []
        """
        return self._parse_pep_numbers(replaces_string, "Replaces")

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

        # Extract PEP number from document metadata (PEP: field)
        pep_number = self.extract_pep_number(content)

        # Extract required fields
        title = self.parse_header_field(content, "Title")
        status = self.parse_header_field(content, "Status")
        pep_type = self.parse_header_field(content, "Type")
        created = self.parse_header_field(content, "Created")
        author_string = self.parse_header_field(content, "Author")

        # Extract optional fields
        topic_string = self.parse_header_field(content, "Topic")
        requires_string = self.parse_header_field(content, "Requires")
        replaces_string = self.parse_header_field(content, "Replaces")

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
                f"Missing required field 'Type' in PEP {pep_number} ({file_path})"
            )
        if not author_string:
            raise ValueError(
                f"Missing required field 'Author' in PEP {pep_number} ({file_path})"
            )

        # Parse authors
        authors = self._parse_authors(author_string)

        # Parse topics (optional field)
        topic = None
        if topic_string is not None:
            topic = self._parse_topics(topic_string)
            # 空リストの場合はNoneとして扱う
            if not topic:
                topic = None

        # Parse required PEPs (optional field)
        requires = None
        if requires_string is not None:
            try:
                requires = self.parse_requires_peps(requires_string)
                # 空リストの場合はNoneとして扱う
                if not requires:
                    requires = None
            except ValueError as e:
                # Requires フィールドのパースエラーはPEP全体のエラーとして扱う
                raise ValueError(
                    f"Failed to parse Requires field in PEP {pep_number} ({file_path}): {e}"
                ) from e

        # Parse replaced PEPs (optional field)
        replaces = None
        if replaces_string is not None:
            try:
                replaces = self.parse_replaces_peps(replaces_string)
                # 空リストの場合はNoneとして扱う
                if not replaces:
                    replaces = None
            except ValueError as e:
                # Replaces フィールドのパースエラーはPEP全体のエラーとして扱う
                raise ValueError(
                    f"Failed to parse Replaces field in PEP {pep_number} ({file_path}): {e}"
                ) from e

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
            topic=topic,
            requires=requires,
            replaces=replaces,
        )

        logger.debug(f"Successfully parsed PEP {pep_number}: {title}")
        return metadata

    def parse_multiple_peps(self, file_paths: list[Path]) -> list[PEPMetadata]:
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

    def save_to_csv(self, metadata_list: list[PEPMetadata], output_path: Path) -> None:
        """
        Save PEP metadata to CSV file.

        Args:
            metadata_list: List of PEPMetadata objects
            output_path: Path where to save the CSV file

        Note:
            DataFrame is sorted by pep_number (ascending) before saving
            to ensure consistent output for hash-based change detection.
        """

        logger.info(f"Saving {len(metadata_list)} PEPs to {output_path}")

        # ディレクトリが存在しない場合は作成
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # DataFrameを作成
        df = pd.DataFrame([asdict(m) for m in metadata_list])

        # リストフィールドをセミコロン区切りの文字列に変換
        if "authors" in df.columns:
            df["authors"] = df["authors"].apply(
                lambda x: "; ".join(x) if isinstance(x, list) else x
            )
        if "topic" in df.columns:
            df["topic"] = df["topic"].apply(
                lambda x: "; ".join(x) if isinstance(x, list) and x else ""
            )
        if "requires" in df.columns:
            df["requires"] = df["requires"].apply(
                lambda x: (
                    "; ".join(str(r) for r in x) if isinstance(x, list) and x else ""
                )
            )
        if "replaces" in df.columns:
            df["replaces"] = df["replaces"].apply(
                lambda x: (
                    "; ".join(str(r) for r in x) if isinstance(x, list) and x else ""
                )
            )

        # NoneをNaN、そして空文字列に変換
        df = df.fillna("")

        # pep_numberでソート（昇順）
        # 空のDataFrameの場合はソートをスキップ
        if len(df) > 0 and "pep_number" in df.columns:
            df = df.sort_values("pep_number", ascending=True)
            logger.info("DataFrame sorted by pep_number (ascending)")

        # CSVに保存
        df.to_csv(output_path, index=False)

        logger.info(f"Successfully saved to {output_path}")
