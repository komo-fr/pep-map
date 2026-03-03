"""Utility functions for calculating file hashes."""

import hashlib
from pathlib import Path


def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA256 hash of a file.

    Args:
        file_path: Path to the file

    Returns:
        Hexadecimal string of the SHA256 hash (64 characters)

    Raises:
        FileNotFoundError: If the file doesn't exist

    Examples:
        >>> from pathlib import Path
        >>> file_path = Path("data/processed/peps_metadata.csv")
        >>> hash_value = calculate_file_hash(file_path)
        >>> len(hash_value)
        64
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256 = hashlib.sha256()

    # メモリ効率的にファイルを読み込む（4KBずつ）
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)

    return sha256.hexdigest()
