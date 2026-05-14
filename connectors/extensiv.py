"""
connectors/extensiv.py
Handles OAuth2 authentication and inventory fetching from Extensiv (3PL Warehouse Manager).
"""

import base64
import time
import os
import requests

BASE_URL = "https://secure-wms.com"
TOKEN_URL = f"{BASE_URL}/AuthServer/api/Token"
INVENTORY_URL = f"{BASE_URL}/inventory/stocksummaries"

_token_cache = {"access_token": None, "expires_at": 0}


def _build_auth_header() -> str:
    """Base64-encode ClientID:ClientSecret for the Basic auth header."""
    client_id = os.getenv("EXTENSIV_CLIENT_ID")
    client_secret = os.getenv("EXTENSIV_CLIENT_SECRET")
    raw = f"{client_id}:{client_secret}"
    return base64.b64encode(raw.encode()).decode()


def get_token() -> str:
    """
    Fetch a Bearer token, using the cache if still valid.
    Extensiv tokens expire in 30-60 min; we refresh after 29 min to be safe.
    """
    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json",
        "Authorization": f"Basic {_build_auth_header()}",
    }
    payload = {
        "grant_type": "client_credentials",
        "user_login": os.getenv("EXTENSIV_USER_LOGIN"),
    }

    resp = requests.post(TOKEN_URL, json=payload, headers=headers, timeout=15)
    resp.raise_for_status()

    data = resp.json()
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + (29 * 60)  # refresh after 29 min

    return _token_cache["access_token"]


def fetch_inventory(page_size: int = 500) -> list[dict]:
    """
    Pull stock summaries from Extensiv for the configured customer.
    Handles pagination automatically and returns a flat list of records.
    """
    token = get_token()
    tpl_id = os.getenv("EXTENSIV_TPL_ID")
    customer_id = os.getenv("EXTENSIV_CUSTOMER_ID")

    headers = {
        "Accept": "application/hal+json",
        "Authorization": f"Bearer {token}",
    }
    params = {
        "tpl": tpl_id,
        "customerid": customer_id,
        "pgsiz": page_size,
        "pgnum": 1,
    }

    all_records = []

    while True:
        resp = requests.get(INVENTORY_URL, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        records = data.get("ResourceList", [])
        all_records.extend(records)

        # Stop if we received fewer records than page_size (last page)
        if len(records) < page_size:
            break

        params["pgnum"] += 1

    return all_records
