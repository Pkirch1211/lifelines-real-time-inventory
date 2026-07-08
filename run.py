"""
run.py
Entry point. Fetches inventory from all available sources and exports to Excel.
Run: python run.py
"""

import os

from connectors import extensiv, sharepoint
from pipeline.aggregate import build_inventory, summarize_by_sku
from output.export_excel import export


DEFAULT_SHAREPOINT_OUTPUT_PATH = "/Planning/5) Supply/16) Data Mart/latest_inventory.xlsx"


def main():
    print("Fetching Extensiv inventory...")
    extensiv_records = extensiv.fetch_inventory()
    print(f"  -> {len(extensiv_records)} records retrieved")

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
    print(f"  -> Saved to: {path}")

    sharepoint_output_path = os.getenv(
        "SHAREPOINT_OUTPUT_PATH",
        DEFAULT_SHAREPOINT_OUTPUT_PATH,
    )

    print("Uploading latest inventory export to SharePoint...")
    upload_result = sharepoint.upload_file(path, sharepoint_output_path)

    uploaded_web_url = upload_result.get("webUrl")
    if uploaded_web_url:
        print(f"  -> Uploaded to SharePoint: {uploaded_web_url}")
    else:
        print(f"  -> Uploaded to SharePoint: {sharepoint_output_path}")


if __name__ == "__main__":
    main()
