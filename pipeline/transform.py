"""
pipeline/transform.py
Normalizes raw records from each source into a common schema before aggregation.

Common schema fields:
  sku           - normalized SKU string (uppercased, stripped)
  description   - product name/description
  qty_on_hand   - current physical quantity
  qty_available - quantity available to sell (on_hand minus holds/reserved)
  location      - warehouse or fulfillment center identifier
  source        - "extensiv" | "amazon" | "po_tracking"
  raw           - original record (for debugging)
"""

import pandas as pd


def normalize_extensiv(records: list[dict]) -> pd.DataFrame:
    rows = []
    for r in records:
        rows.append({
            "sku": str(r.get("itemIdentifier", {}).get("sku", "")).strip().upper(),
            "description": r.get("itemIdentifier", {}).get("description", ""),
            "qty_on_hand": r.get("onHand", 0),
            "qty_available": r.get("available", 0),
            "qty_allocated": r.get("allocated", 0),
            "qty_on_hold": r.get("onHold", 0),
            "location": r.get("facilityId", ""),
            "source": "extensiv",
            "raw": r,
        })
    return pd.DataFrame(rows)


def normalize_amazon(records: list[dict]) -> pd.DataFrame:
    rows = []
    for r in records:
        rows.append({
            "sku": str(r.get("sellerSku", "")).strip().upper(),
            "description": r.get("productName", ""),
            "qty_on_hand": r.get("totalQuantity", 0),
            "qty_available": r.get("fulfillableQuantity", 0),
            "location": r.get("fnSku", ""),   # Amazon fulfillment center SKU
            "source": "amazon",
            "raw": r,
        })
    return pd.DataFrame(rows)


def normalize_po_tracking(records: list[dict]) -> pd.DataFrame:
    """
    PO tracking doesn't represent on-hand inventory — it represents
    inbound/ordered quantities. Included here for in-transit visibility.
    Column names will depend on your actual Excel headers; update the
    mapping below once you share the file structure.
    """
    rows = []
    for r in records:
        rows.append({
            "sku": str(r.get("SKU", r.get("Sku", r.get("sku", "")))).strip().upper(),
            "description": r.get("Description", r.get("Product", "")),
            "qty_on_hand": 0,                          # POs are not yet received
            "qty_available": 0,
            "qty_inbound": r.get("Qty Ordered", r.get("QtyOrdered", 0)),
            "eta": r.get("ETA", r.get("Expected Date", "")),
            "po_number": r.get("PO Number", r.get("PO#", "")),
            "location": "Inbound",
            "source": "po_tracking",
            "raw": r,
        })
    return pd.DataFrame(rows)
