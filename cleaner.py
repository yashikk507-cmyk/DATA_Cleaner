"""
cleaner.py - the cleaning engine behind the Data Cleaner app.

It takes a messy table (a pandas DataFrame) and returns:
  1. a cleaned DataFrame
  2. a report describing what was changed
"""

import pandas as pd


# ---------- helpers ----------

def _is_text(series):
    return pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series)


def clean_column_names(df):
    """'Transaction Date ' -> 'transaction_date'"""
    df = df.copy()
    df.columns = (
        pd.Index(df.columns.astype(str))
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
    )
    return df


def clean_text_columns(df, text_case=None):
    """
    Trim spaces and collapse repeated spaces in every text column.
    text_case: None (keep), "lower", "title" or "upper".
    """
    df = df.copy()
    for col in df.columns:
        if _is_text(df[col]):
            s = df[col].str.strip().str.replace(r"\s+", " ", regex=True)
            if text_case == "lower":
                s = s.str.lower()
            elif text_case == "title":
                s = s.str.title()
            elif text_case == "upper":
                s = s.str.upper()
            df[col] = s
    return df


def _to_number(series):
    """Turn '₹1,211.50', '$20', '(500)' and '  42 ' into numbers."""
    cleaned = (
        series.astype(str)
        .str.replace(r"[₹$€£,\s]", "", regex=True)
        .str.replace(r"^\((.*)\)$", r"-\1", regex=True)  # (500) -> -500
    )
    return pd.to_numeric(cleaned, errors="coerce")


def _maybe_number(series, threshold=0.8):
    """Convert a text column to numbers only if most of its values look numeric."""
    converted = _to_number(series)
    non_empty = series.notna().sum()
    if non_empty == 0:
        return series
    if converted.notna().sum() >= threshold * non_empty:
        return converted
    return series


def _to_date(series):
    """
    Year-first dates (2026-10-06) are read strictly, so they are never swapped.
    Everything else is read day-first, so 05-10-2026 means 5 October (Indian format).
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        return series  # already dates (e.g. from an Excel file)

    text = series.astype(str).str.strip()
    iso = pd.to_datetime(text, format="%Y-%m-%d", errors="coerce")
    day_first = pd.to_datetime(text, errors="coerce", dayfirst=True, format="mixed")
    return iso.fillna(day_first)


# ---------- main function ----------

def clean_dataset(df, text_case=None, drop_duplicates=True):
    report = {"rows_in": len(df), "columns_in": df.shape[1]}
    changes = []

    # 1. Column names
    df = clean_column_names(df)
    changes.append("Standardised column names (lowercase, underscores, no extra spaces)")

    # 2. Text spacing and optional case
    df = clean_text_columns(df, text_case=text_case)
    changes.append("Removed extra spaces from text values")
    if text_case:
        changes.append(f"Converted text to {text_case} case")

    # 3. Duplicates
    before = len(df)
    if drop_duplicates:
        df = df.drop_duplicates()
    report["duplicates_removed"] = before - len(df)
    if report["duplicates_removed"]:
        changes.append(f"Removed {report['duplicates_removed']} duplicate rows")

    # 4. Column types: dates and numbers
    date_cols, number_cols = [], []
    for col in df.columns:
        if "date" in col or "time" in col:
            df[col] = _to_date(df[col])
            date_cols.append(col)
        elif _is_text(df[col]):
            new = _maybe_number(df[col])
            if pd.api.types.is_numeric_dtype(new):
                df[col] = new
                number_cols.append(col)
    if date_cols:
        changes.append(f"Converted date columns to real dates: {', '.join(date_cols)}")
    if number_cols:
        changes.append(f"Converted text to numbers: {', '.join(number_cols)}")

    # 5. Completely empty rows
    before = len(df)
    df = df.dropna(how="all")
    report["empty_rows_removed"] = before - len(df)
    if report["empty_rows_removed"]:
        changes.append(f"Removed {report['empty_rows_removed']} completely empty rows")

    # 6. Summary
    report["rows_out"] = len(df)
    report["columns_out"] = df.shape[1]
    report["changes"] = changes
    report["column_summary"] = pd.DataFrame({
        "column": df.columns,
        "type": [str(t) for t in df.dtypes],
        "missing": df.isna().sum().values,
        "missing_%": (df.isna().mean().values * 100).round(1),
    })
    return df, report
