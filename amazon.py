"""
connectors/amazon.py
Placeholder for Amazon SP-API FBA inventory connector.
Will use the Login With Amazon (LWA) OAuth2 flow once credentials are available.
"""


def fetch_inventory() -> list[dict]:
    """
    TODO: Implement once SP-API app is approved and credentials are in .env.

    Flow:
      1. POST to https://api.amazon.com/auth/o2/token with:
           grant_type=refresh_token
           client_id, client_secret, refresh_token
      2. Use returned access_token as Bearer on SP-API calls
      3. GET https://sellingpartnerapi-na.amazon.com/fba/inventory/v1/summaries
           with granularityType=Marketplace, granularityId=<MARKETPLACE_ID>
    """
    raise NotImplementedError("Amazon SP-API connector not yet implemented.")
