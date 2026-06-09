"""Dataset file reading utilities with automatic format detection."""

import csv
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import HTTPException, status

# File extensions we accept
ALLOWED_SUFFIXES = {".csv", ".xlsx", ".txt", ".dat", ".data"}

# Common delimiters to try (in order of preference)
COMMON_DELIMITERS = [",", "\t", ";", r"\s+", "|"]


def read_dataframe(file_path: Path) -> pd.DataFrame:
    """Read a dataframe from a file, auto-detecting format."""
    suffix = file_path.suffix.lower()

    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {suffix}. Supported: {', '.join(sorted(ALLOWED_SUFFIXES))}",
        )

    if suffix == ".xlsx":
        return pd.read_excel(file_path)

    if suffix == ".csv":
        return _read_delimited(file_path)

    # .txt / .dat / .data — auto-detect delimiter and header
    return _read_delimited(file_path)


def detect_delimiter(file_path: Path) -> str:
    """Detect the most likely delimiter by reading the first few lines."""
    try:
        with open(file_path, encoding="utf-8") as fh:
            sample = "".join(fh.readline() for _ in range(5))
    except UnicodeDecodeError:
        # Try common encodings
        for enc in ["gbk", "gb2312", "latin-1", "cp1252"]:
            try:
                with open(file_path, encoding=enc) as fh:
                    sample = "".join(fh.readline() for _ in range(5))
                break
            except (UnicodeDecodeError, LookupError):
                continue
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to detect file encoding. Please use UTF-8 or GBK.",
            )

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters="".join(COMMON_DELIMITERS))
        return dialect.delimiter or ","
    except csv.Error:
        # Fallback: try each delimiter and pick the one that produces the most consistent columns
        best_delimiter = ","
        best_score = 0
        for delim in COMMON_DELIMITERS:
            try:
                if delim == r"\s+":
                    # Use str.split() for whitespace
                    rows = [line.split() for line in sample.strip().split("\n") if line.strip()]
                else:
                    rows = [list(csv.reader([line], delimiter=delim))[0]
                            for line in sample.strip().split("\n") if line.strip()]
            except Exception:
                continue
            if not rows:
                continue
            col_counts = [len(row) for row in rows]
            if len(set(col_counts)) == 1 and col_counts[0] > 1:
                return delim
            avg_cols = sum(col_counts) / len(col_counts)
            if avg_cols > best_score:
                best_score = avg_cols
                best_delimiter = delim
        return best_delimiter


def _read_delimited(file_path: Path) -> pd.DataFrame:
    """Read a delimited text file with auto-detection of delimiter and header."""
    delimiter = detect_delimiter(file_path)

    # Try reading with header first
    try:
        df = pd.read_csv(
            file_path,
            sep=delimiter,
            encoding="utf-8",
            engine="python" if delimiter == r"\s+" else "c",
        )
    except UnicodeDecodeError:
        # Try alternate encodings
        df = None
        for enc in ["gbk", "gb2312", "latin-1", "cp1252"]:
            try:
                df = pd.read_csv(
                    file_path,
                    sep=delimiter,
                    encoding=enc,
                    engine="python" if delimiter == r"\s+" else "c",
                )
                break
            except (UnicodeDecodeError, LookupError):
                continue
        if df is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to read file encoding. Please use UTF-8 or GBK.",
            )

    # Detect if first row is actually a header or data
    if _looks_like_header_free(df):
        # Re-read without header
        df = pd.read_csv(
            file_path,
            sep=delimiter,
            header=None,
            encoding="utf-8",
            engine="python" if delimiter == r"\s+" else "c",
        )
        # Assign default column names
        df.columns = [f"col_{i}" for i in range(len(df.columns))]

    return df


def _looks_like_header_free(df: pd.DataFrame) -> bool:
    """Heuristic: check if the file likely has NO header row.

    Returns True if the first row was probably data (no real header).
    We check column names (what pandas treated as headers) to decide.
    """
    if df.empty or len(df.columns) == 0:
        return False

    # Check column names — if they look like data values, the file has no header
    col_numeric_count = 0
    col_long_count = 0
    for col in df.columns:
        col_str = str(col)
        try:
            float(col_str)
            col_numeric_count += 1
        except (ValueError, TypeError):
            pass
        if len(col_str) > 50:
            col_long_count += 1

    # If > 50% of column names are numeric → they're data, not headers
    if len(df.columns) > 0 and col_numeric_count / len(df.columns) > 0.5:
        return True

    # If any column name is very long → likely a data row, not a header
    if col_long_count > 0:
        return True

    # If column names look like auto-generated 0, 1, 2... → no header
    if all(str(col).isdigit() for col in df.columns):
        return True

    return False


def detect_has_header(file_path: Path) -> bool:
    """Quick check: does the file have a header row?"""
    delimiter = detect_delimiter(file_path)
    try:
        test_df = pd.read_csv(
            file_path,
            sep=delimiter,
            nrows=0,
            encoding="utf-8",
            engine="python" if delimiter == r"\s+" else "c",
        )
    except UnicodeDecodeError:
        return True  # Assume yes if encoding issues

    # Check a small sample
    try:
        sample_df = pd.read_csv(
            file_path,
            sep=delimiter,
            nrows=5,
            encoding="utf-8",
            engine="python" if delimiter == r"\s+" else "c",
        )
        return not _looks_like_header_free(sample_df)
    except Exception:
        return True
