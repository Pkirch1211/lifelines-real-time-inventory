# Lifelines Inventory Automation

Aggregates live inventory data from three sources into a unified, pivot-ready Excel export. Built in Python, designed to eventually power a live inventory dashboard.

---

## Data Sources

| Source | Auth Type | Token Style |
|---|---|---|
| Extensiv (WMS) | OAuth 2.0 Client Credentials | Bearer token (short-lived) |
| Amazon SP-API | OAuth 2.0 LWA | Refresh token → access token |
| SharePoint (PO Tracking) | Azure AD App-Only (OAuth 2.0) | Bearer token via Graph API |

---

## Repo Structure

```
lifelines-inventory/
│
├── run.py                  # Entry point — fetch all sources, export to Excel
├── requirements.txt
├── .env                    # Secrets (gitignored — never commit this)
├── .env.example            # Safe template for onboarding
│
├── connectors/
│   ├── extensiv.py         # OAuth2 auth + inventory fetch
│   ├── amazon.py           # Placeholder (SP-API, pending credentials)
│   └── sharepoint.py       # PO tracking via Microsoft Graph API
│
├── pipeline/
│   ├── transform.py        # Normalizes each source to a common schema
│   └── aggregate.py        # Merges sources, builds SKU summary
│
└── output/
    ├── export_excel.py     # Writes formatted .xlsx with two sheets
    └── exports/            # Output files land here (gitignored)
```

---

## Setup

### 1. Add GitHub Secrets

Go to **Settings → Secrets and variables → Actions** in the `lifelines-real-time-inventory` repo and add the following secrets:

| Secret | Description |
|---|---|
| `EXTENSIV_CLIENT_ID` | OAuth2 Client ID |
| `EXTENSIV_CLIENT_SECRET` | OAuth2 Client Secret |
| `EXTENSIV_USER_LOGIN` | Extensiv user login email |
| `EXTENSIV_TPL_ID` | 3PL ID (1529) |
| `EXTENSIV_CUSTOMER_ID` | Extensiv customer GUID |

Amazon and SharePoint secrets are pre-commented in the workflow — add and uncomment as each connector comes online.

### 2. Run

Runs automatically at **7am ET, Mon–Fri**. To trigger manually:

Go to **Actions → Inventory Sync → Run workflow**.

### 3. Get the output

After each run, go to **Actions → [latest run] → Artifacts** and download `inventory-export`. The `.xlsx` contains two sheets: **All Inventory** and **SKU Summary**.

---

## Output

The Excel export contains two sheets:

- **All Inventory** — full normalized records from all active sources, filterable by SKU, location, and source. Paste directly into a pivot table.
- **SKU Summary** — one row per SKU, with quantity columns broken out by source and a total.

---

## Connector Status

| Connector | Status | Notes |
|---|---|---|
| Extensiv | ✅ Active | Full auth + paginated inventory pull |
| Amazon SP-API | 🔜 Pending | Awaiting SP-API app approval |
| SharePoint PO Tracking | 🔜 Pending | Awaiting column mapping confirmation |

---

## Common Schema

All sources are normalized to these fields before aggregation:

| Field | Description |
|---|---|
| `sku` | Normalized SKU (uppercased, stripped) |
| `description` | Product name |
| `qty_on_hand` | Physical quantity at location |
| `qty_available` | Quantity available to sell |
| `location` | Warehouse or fulfillment center |
| `source` | `extensiv` / `amazon` / `po_tracking` |

PO Tracking records also include `qty_inbound`, `eta`, and `po_number`.

---

## Roadmap

- [x] Extensiv connector
- [x] Excel export (pivot-ready, two sheets)
- [ ] Amazon SP-API connector
- [ ] SharePoint PO Tracking connector
- [ ] Scheduled run (GitHub Actions or cron)
- [ ] Live inventory dashboard (web app)
