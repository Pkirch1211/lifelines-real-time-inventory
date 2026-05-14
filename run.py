"""
run.py
Entry point. Fetches inventory from all available sources and exports to Excel.
Run: python run.py
"""

from connectors import extensiv
from pipeline.aggregate import build_inventory, summarize_by_sku
from output.export_excel import export


def main():
    print("Fetching Extensiv inventory...")
    extensiv_records = extensiv.fetch_inventory()
    print(f"  → {len(extensiv_records)} records retrieved")

    # Amazon and SharePoint placeholders — uncomment as each connector is ready
    # from connectors import amazon
    # amazon_records = amazon.fetch_inventory()

    # from connectors import sharepoint
    # po_records = sharepoint.fetch_po_tracking()

    print("Building unified inventory...")
    df = build_inventory(extensiv_records=extensiv_records)
    summary = summarize_by_sku(df)

    print("Exporting to Excel...")
    path = export(df, summary)
    print(f"  → Saved to: {path}")


if __name__ == "__main__":
    main()
