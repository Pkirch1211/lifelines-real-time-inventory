"""
pipeline/aggregate.py
Merges normalized DataFrames from all active sources into a single inventory view.
"""

import pandas as pd
from pipeline.transform import normalize_extensiv, normalize_amazon, normalize_po_tracking


def build_inventory(
    extensiv_records: list[dict] | None = None,
    amazon_records: list[dict] | None = None,
    po_records: list[dict] | None = None,
) -> pd.DataFrame:
    """
    Accepts raw records from any combination of sources.
    Returns a unified DataFrame with all inventory and inbound data.
    """
    frames = []

    if extensiv_records is not None:
        frames.append(normalize_extensiv(extensiv_records))

    if amazon_records is not None:
        frames.append(normalize_amazon(amazon_records))

    if po_records is not None:
        frames.append(normalize_po_tracking(po_records))

    if not frames:
        raise ValueError("No inventory sources provided.")

    df = pd.concat(frames, ignore_index=True)

    # Ensure expected numeric columns exist and have consistent dtypes
    numeric_cols = [
        "qty_on_hand",
        "qty_available",
        "qty_allocated",
        "qty_on_hold",
        "qty_unavailable",
        "qty_inbound",
    ]

    for col in numeric_cols:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Recalculate unavailable as the clean reconciliation column.
    # This avoids relying on WMS-specific allocated/hold definitions.
    df["qty_unavailable"] = df["qty_on_hand"] - df["qty_available"]

    return df


def summarize_by_sku(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot-ready summary: one row per SKU with qty broken out by source.
    """
    pivot = df.pivot_table(
        index="sku",
        columns="source",
        values="qty_on_hand",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    pivot.columns.name = None
    pivot["total_on_hand"] = pivot.drop(columns=["sku"]).sum(axis=1)

    return pivot.sort_values("sku")
