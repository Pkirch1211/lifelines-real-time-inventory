"""
connectors/sharepoint.py

Reads and writes files from SharePoint via Microsoft Graph API.
Uses Azure AD App-Only auth (client credentials flow).
"""

import os
import io
import time
import requests
import pandas as pd


GRAPH_BASE = "https://graph.microsoft.com/v1.0"
TOKEN_URL_TEMPLATE = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

_token_cache = {"access_token": None, "expires_at": 0}


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def get_token() -> str:
    """
    Get a Microsoft Graph access token using Azure app-only auth.

    Required env vars:
      - SHAREPOINT_TENANT_ID
      - SHAREPOINT_CLIENT_ID
      - SHAREPOINT_CLIENT_SECRET
    """
    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    tenant_id = _require_env("SHAREPOINT_TENANT_ID")
    client_id = _require_env("SHAREPOINT_CLIENT_ID")
    client_secret = _require_env("SHAREPOINT_CLIENT_SECRET")

    url = TOKEN_URL_TEMPLATE.format(tenant_id=tenant_id)

    resp = requests.post(
        url,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://graph.microsoft.com/.default",
        },
        timeout=15,
    )
    resp.raise_for_status()

    data = resp.json()
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + data.get("expires_in", 3600) - 60

    return _token_cache["access_token"]


def _get_site_id(token: str) -> str:
    """
    Resolve the SharePoint site ID from SHAREPOINT_SITE_URL.

    Example SHAREPOINT_SITE_URL:
      https://lifelines.sharepoint.com/sites/Operations

    Microsoft Graph site lookup format:
      /sites/{hostname}:/{site_path}:
    """
    site_url = _require_env("SHAREPOINT_SITE_URL").rstrip("/")

    parts = site_url.split("/")
    if len(parts) < 5:
        raise ValueError(
            "SHAREPOINT_SITE_URL must look like "
            "https://lifelines.sharepoint.com/sites/Operations"
        )

    hostname = parts[2]
    site_path = "/".join(parts[3:])

    site_resp = requests.get(
        f"{GRAPH_BASE}/sites/{hostname}:/{site_path}:",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )

    try:
        site_resp.raise_for_status()
    except requests.HTTPError as exc:
        raise requests.HTTPError(
            f"Failed to resolve SharePoint site. "
            f"SHAREPOINT_SITE_URL={site_url} | "
            f"Graph URL={GRAPH_BASE}/sites/{hostname}:/{site_path}: | "
            f"Response={site_resp.text}"
        ) from exc

    return site_resp.json()["id"]


def fetch_po_tracking() -> list[dict]:
    """
    Downloads the PO Tracking Excel file from SharePoint and returns
    its contents as a list of row dicts.

    Required env vars:
      - SHAREPOINT_SITE_URL
      - SHAREPOINT_FILE_PATH
    """
    token = get_token()
    site_id = _get_site_id(token)
    file_path = _require_env("SHAREPOINT_FILE_PATH")

    if not file_path.startswith("/"):
        file_path = "/" + file_path

    file_resp = requests.get(
        f"{GRAPH_BASE}/sites/{site_id}/drive/root:{file_path}:/content",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )

    try:
        file_resp.raise_for_status()
    except requests.HTTPError as exc:
        raise requests.HTTPError(
            f"Failed to download SharePoint file. "
            f"SHAREPOINT_FILE_PATH={file_path} | "
            f"Response={file_resp.text}"
        ) from exc

    df = pd.read_excel(io.BytesIO(file_resp.content))
    return df.to_dict(orient="records")


def upload_file(local_path: str, sharepoint_path: str) -> dict:
    """
    Uploads/replaces a file in SharePoint using Microsoft Graph.

    local_path:
      Local file path on the GitHub runner.

    sharepoint_path:
      Path relative to the SharePoint document library root.

      For your synced folder:
        C:\\Users\\PaulKirchner\\LifeLines\\Operations - Documents\\Planning\\5) Supply\\16) Data Mart

      Use:
        /Planning/5) Supply/16) Data Mart/latest_inventory.xlsx
    """
    if not local_path:
        raise ValueError("Missing local_path")

    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Local file does not exist: {local_path}")

    if not sharepoint_path:
        raise ValueError("Missing sharepoint_path")

    if not sharepoint_path.startswith("/"):
        sharepoint_path = "/" + sharepoint_path

    token = get_token()
    site_id = _get_site_id(token)

    with open(local_path, "rb") as f:
        upload_resp = requests.put(
            f"{GRAPH_BASE}/sites/{site_id}/drive/root:{sharepoint_path}:/content",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            },
            data=f,
            timeout=60,
        )

    try:
        upload_resp.raise_for_status()
    except requests.HTTPError as exc:
        raise requests.HTTPError(
            f"Failed to upload file to SharePoint. "
            f"local_path={local_path} | "
            f"sharepoint_path={sharepoint_path} | "
            f"Response={upload_resp.text}"
        ) from exc

    return upload_resp.json()
