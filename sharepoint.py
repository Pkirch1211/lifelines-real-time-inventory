"""
connectors/sharepoint.py
Reads the PO Tracking Excel file from SharePoint via Microsoft Graph API.
Uses Azure AD App-Only auth (client credentials flow).
"""

import os
import io
import requests
import pandas as pd

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
TOKEN_URL_TEMPLATE = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

_token_cache = {"access_token": None, "expires_at": 0}


def get_token() -> str:
    import time
    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    tenant_id = os.getenv("SHAREPOINT_TENANT_ID")
    url = TOKEN_URL_TEMPLATE.format(tenant_id=tenant_id)

    resp = requests.post(url, data={
        "grant_type": "client_credentials",
        "client_id": os.getenv("SHAREPOINT_CLIENT_ID"),
        "client_secret": os.getenv("SHAREPOINT_CLIENT_SECRET"),
        "scope": "https://graph.microsoft.com/.default",
    }, timeout=15)
    resp.raise_for_status()

    data = resp.json()
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + data.get("expires_in", 3600) - 60

    return _token_cache["access_token"]


def fetch_po_tracking() -> list[dict]:
    """
    Downloads the PO Tracking Excel file from SharePoint and returns
    its contents as a list of row dicts.
    """
    token = get_token()
    site_url = os.getenv("SHAREPOINT_SITE_URL")
    file_path = os.getenv("SHAREPOINT_FILE_PATH")

    # Resolve site ID from URL
    hostname = site_url.split("/")[2]
    site_path = "/".join(site_url.split("/")[3:])
    site_resp = requests.get(
        f"{GRAPH_BASE}/sites/{hostname}:/{site_path}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    site_resp.raise_for_status()
    site_id = site_resp.json()["id"]

    # Download file content
    file_resp = requests.get(
        f"{GRAPH_BASE}/sites/{site_id}/drive/root:{file_path}:/content",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    file_resp.raise_for_status()

    df = pd.read_excel(io.BytesIO(file_resp.content))
    return df.to_dict(orient="records")
