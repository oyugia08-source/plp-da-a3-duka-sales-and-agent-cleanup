"""Cleaning and enrichment pipeline for mobile money agent transaction data."""

from __future__ import annotations

from typing import Any
import pandas as pd


def clean_agent_data(
    txns: pd.DataFrame,
    agents: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Clean raw agent transactions and left-join agent register metadata.

    Parameters
    ----------
    txns : pd.DataFrame
        Raw transaction records.
    agents : pd.DataFrame
        Agent register table containing ``agent_id`` and ``county``.

    Returns
    -------
    tuple[pd.DataFrame, dict[str, Any]]
        Cleaned DataFrame and log dictionary containing summary counts and audit DataFrame.
    """
    df = txns.copy()
    ref_agents = agents.copy()

    raw_rows = int(len(df))

    # Deduplicate exact rows and duplicate txn_id keys
    before_dedup = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    if "txn_id" in df.columns:
        df = df.drop_duplicates(subset=["txn_id"], keep="first").reset_index(drop=True)
    dups_removed = int(before_dedup - len(df))

    # Standardise txn_type to "Deposit" or "Withdrawal"
    raw_type = df["txn_type"].astype("string").str.strip().str.lower()
    mapped_type = raw_type.map({"deposit": "Deposit", "withdrawal": "Withdrawal"})
    unstandard_type_rows = int((df["txn_type"].notna() & (df["txn_type"].astype("string") != mapped_type)).sum())
    df["txn_type"] = mapped_type.fillna("Deposit").astype("object")

    # Parse amount to numeric, flag/impute missing or non-numeric values
    amt_clean_str = (
        df["amount"]
        .astype("string")
        .str.strip()
        .str.replace(",", "", regex=False)
        .str.replace(r"[^\d.\-]", "", regex=True)
    )
    parsed_amt = pd.to_numeric(amt_clean_str, errors="coerce")
    df["amount_imputed"] = parsed_amt.isna()
    imputed_rows = int(df["amount_imputed"].sum())

    overall_med = float(parsed_amt.median())
    group_med = parsed_amt.groupby(df["txn_type"]).transform("median").fillna(overall_med)
    df["amount"] = parsed_amt.fillna(group_med).astype(float)

    # Parse mixed date separators and format as ISO YYYY-MM-DD
    parsed_dt = pd.to_datetime(df["txn_date"], format="mixed", errors="coerce")
    mixed_date_rows = int(df["txn_date"].astype("string").str.contains("/", na=False).sum())
    df["txn_date"] = parsed_dt.dt.strftime("%Y-%m-%d")

    # Flag outliers via IQR rule
    q1 = float(df["amount"].quantile(0.25))
    q3 = float(df["amount"].quantile(0.75))
    iqr = float(q3 - q1)
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    df["is_outlier"] = (df["amount"] < lower_bound) | (df["amount"] > upper_bound)
    outlier_rows = int(df["is_outlier"].sum())

    # Left-join agent register to bring in county
    clean_df = df.merge(ref_agents[["agent_id", "county"]], on="agent_id", how="left")
    unknown_agent_rows = int(clean_df["county"].isna().sum())
    clean_df["county"] = clean_df["county"].fillna("Unknown")

    audit_df = pd.DataFrame([
        {
            "issue": "Duplicate rows / duplicate txn_id values removed",
            "dimension": "Uniqueness",
            "column": "txn_id",
            "rows affected": dups_removed,
        },
        {
            "issue": "Missing or non-numeric amounts imputed with median",
            "dimension": "Completeness",
            "column": "amount",
            "rows affected": imputed_rows,
        },
        {
            "issue": "Casing/whitespace in txn_type standardised to Deposit/Withdrawal",
            "dimension": "Consistency",
            "column": "txn_type",
            "rows affected": unstandard_type_rows,
        },
        {
            "issue": "Mixed date delimiters standardised to ISO YYYY-MM-DD",
            "dimension": "Validity",
            "column": "txn_date",
            "rows affected": mixed_date_rows,
        },
        {
            "issue": "Extreme transaction amounts flagged using IQR fences",
            "dimension": "Accuracy",
            "column": "amount",
            "rows affected": outlier_rows,
        },
        {
            "issue": "Transactions referencing agent_id missing from agent register",
            "dimension": "Timeliness",
            "column": "agent_id",
            "rows affected": unknown_agent_rows,
        },
    ])

    log: dict[str, Any] = {
        "raw_rows": raw_rows,
        "clean_rows": int(len(clean_df)),
        "duplicates_removed": dups_removed,
        "amounts_imputed": imputed_rows,
        "outliers_flagged": outlier_rows,
        "unknown_agent_txns": unknown_agent_rows,
        "audit_table": audit_df,
    }

    return clean_df, log
