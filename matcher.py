import pandas as pd
import json
import os

PO_FILE = "purchase_orders.csv"
HISTORY_FILE = "data/run_history.json"

def load_pos():
    return pd.read_csv(PO_FILE)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def is_duplicate(invoice_number, history):
    if not invoice_number:
        return False
    for run in history:
        if run.get("invoice_number") == invoice_number:
            return True
    return False

def match_invoice(invoice_data):
    po_df = load_pos()
    history = load_history()
    result = {
        "invoice_number": invoice_data.get("invoice_number"),
        "vendor_name": invoice_data.get("vendor_name"),
        "po_number": invoice_data.get("po_number"),
        "grand_total": invoice_data.get("grand_total"),
        "checks": {}
    }

    # Check 1 — Missing critical fields
    missing = []
    if not invoice_data.get("invoice_number"):
        missing.append("invoice_number")
    if not invoice_data.get("vendor_name"):
        missing.append("vendor_name")
    if not invoice_data.get("grand_total"):
        missing.append("grand_total")
    if not invoice_data.get("po_number"):
        missing.append("po_number")

    result["checks"]["missing_fields"] = missing

    # Check 2 — Duplicate detection
    result["checks"]["is_duplicate"] = is_duplicate(
        invoice_data.get("invoice_number"), history
    )

    # Check 3 — PO match
    po_match = po_df[po_df["po_number"] == invoice_data.get("po_number")]

    if po_match.empty:
        result["checks"]["po_found"] = False
        result["checks"]["po_is_open"] = False
        result["checks"]["vendor_match"] = False
        result["checks"]["amount_within_tolerance"] = False
        result["checks"]["tolerance_percent"] = None
        result["checks"]["po_amount"] = None
        result["checks"]["po_status"] = None
        return result

    po = po_match.iloc[0]
    result["checks"]["po_found"] = True
    result["checks"]["po_amount"] = float(po["po_amount"])
    result["checks"]["tolerance_percent"] = float(po["tolerance_percent"])

    # Check 4 — PO status open or closed
    po_status = po["status"].strip().lower()
    result["checks"]["po_status"] = po_status
    result["checks"]["po_is_open"] = po_status == "open"

    # Check 5 — Vendor name match
    result["checks"]["vendor_match"] = (
        invoice_data.get("vendor_name", "").strip().lower() ==
        po["vendor_name"].strip().lower()
    )

    # Check 6 — Amount within tolerance
    po_amount = float(po["po_amount"])
    invoice_total = float(invoice_data.get("grand_total", 0))
    tolerance = float(po["tolerance_percent"]) / 100
    lower = po_amount * (1 - tolerance)
    upper = po_amount * (1 + tolerance)
    result["checks"]["amount_within_tolerance"] = lower <= invoice_total <= upper
    result["checks"]["invoice_total"] = invoice_total

    return result

if __name__ == "__main__":
    from extractor import extract_invoice_data
    invoice = extract_invoice_data("invoice_001_happy.pdf")
    result = match_invoice(invoice)
    print(json.dumps(result, indent=2))
