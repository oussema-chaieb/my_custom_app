import csv
from typing import Dict, List, Any

import frappe

CSV_FILENAME = "tunisia_coa.csv"


def _get_csv_rows() -> List[Dict[str, Any]]:
    """Read the bundled CSV file and return the rows as dictionaries."""
    csv_path = frappe.get_app_path("my_custom_app", "setup", "tunisia_coa", CSV_FILENAME)
    with open(csv_path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _ensure_parent(account_row: Dict[str, str], mapping: Dict[str, str], company: str):
    """Make sure the parent account exists and return its full name (or None)."""
    parent_name = account_row.get("Parent Account")
    if not parent_name:
        return None

    # Parent should have already been created since CSV is in hierarchical order
    full_parent = mapping.get(parent_name)
    if not full_parent:
        # Fallback: try to fetch directly from DB (handles reruns)
        parent_doc = frappe.db.get_value(
            "Account",
            {
                "account_name": parent_name,
                "company": company,
            },
            "name",
        )
        if parent_doc:
            full_parent = parent_doc
            mapping[parent_name] = full_parent
    return full_parent


def _create_account(row: Dict[str, str], company: str, mapping: Dict[str, str]):
    """Create an individual Account based on the CSV row for the given company."""

    account_name = row.get("Account Name")
    if not account_name:
        return  # skip malformed lines

    # Skip if account already exists (idempotent)
    if frappe.db.exists("Account", {"account_name": account_name, "company": company}):
        existing_full_name = frappe.db.get_value(
            "Account", {"account_name": account_name, "company": company}, "name"
        )
        mapping.setdefault(account_name, existing_full_name)
        return

    parent_account = _ensure_parent(row, mapping, company)

    doc = frappe.get_doc({
        "doctype": "Account",
        "account_name": account_name,
        "company": company,
        "parent_account": parent_account,
        "is_group": int(row.get("Is Group") or 0),
        "account_number": row.get("Account Number") or None,
        "root_type": row.get("Root Type") or None,
        "account_type": row.get("Account Type") or None,
        "account_currency": row.get("Account Currency") or None,
    })

    # Insert while ignoring duplicates arising in race-conditions during parallel installs
    try:
        doc.insert(ignore_if_duplicate=True)
        mapping[account_name] = doc.name
    except frappe.DuplicateEntryError:
        frappe.db.rollback()
        existing_full_name = frappe.db.get_value(
            "Account", {"account_name": account_name, "company": company}, "name"
        )
        if existing_full_name:
            mapping[account_name] = existing_full_name


def import_chart_for_all_companies():
    """Import the bundled Tunisian chart of accounts for every company.

    This function is meant to be hooked into the `after_migrate` event so that
    freshly migrated sites automatically receive the full Tunisian chart of
    accounts without any manual steps.
    """
    rows = _get_csv_rows()

    for company in frappe.get_all("Company", pluck="name"):
        _import_for_company(company, rows)

    frappe.db.commit()


def _import_for_company(company: str, rows: List[Dict[str, str]]):
    # Heuristic: if company already has any GL Entry we skip importing to avoid conflicts
    if frappe.db.exists("GL Entry", {"company": company}):
        return

    mapping: Dict[str, str] = {}

    for row in rows:
        _create_account(row, company, mapping)


# Allow manual execution via bench execute if required

def run():  # noqa: D401 – simple name for bench execute convenience
    """CLI helper – `bench execute my_custom_app.setup.tunisia_coa.import_coa.run`"""
    import_chart_for_all_companies() 