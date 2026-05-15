import json
import os
from datetime import datetime

HISTORY_FILE = "data/run_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_to_history(record):
    history = load_history()
    history.append(record)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def make_decision(match_result):
    checks = match_result.get("checks", {})
    reasons = []
    decision = "APPROVED"

    # Rule 1 — Missing fields → Reject
    missing = checks.get("missing_fields", [])
    if missing:
        decision = "REJECTED"
        reasons.append(f"Missing required fields: {', '.join(missing)}")

    # Rule 2 — Duplicate → Reject
    if checks.get("is_duplicate"):
        decision = "REJECTED"
        reasons.append(f"Duplicate invoice — already processed before")

    # Rule 3 — PO not found → Reject
    if not checks.get("po_found"):
        decision = "REJECTED"
        reasons.append(f"No matching PO found for {match_result.get('po_number')}")

    # Rule 4 — PO is closed → Reject
    if checks.get("po_found") and not checks.get("po_is_open"):
        decision = "REJECTED"
        reasons.append(f"{match_result.get('po_number')} is closed — no further invoices accepted")

    # Rule 5 — Vendor mismatch → Flag
    if checks.get("po_found") and checks.get("po_is_open") and not checks.get("vendor_match"):
        decision = "FLAGGED"
        reasons.append(f"Vendor name does not match PO record")

    # Rule 6 — Amount outside tolerance → Flag
    if checks.get("po_found") and checks.get("po_is_open") and not checks.get("amount_within_tolerance"):
        decision = "FLAGGED"
        po_amount = checks.get("po_amount", 0)
        invoice_total = checks.get("invoice_total", 0)
        diff = abs(invoice_total - po_amount)
        reasons.append(
            f"Amount mismatch — Invoice: INR {invoice_total:,.2f}, "
            f"PO: INR {po_amount:,.2f}, "
            f"Difference: INR {diff:,.2f}"
        )

    if not reasons:
        reasons.append("All checks passed — invoice matches PO within tolerance")

    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "invoice_number": match_result.get("invoice_number"),
        "vendor_name": match_result.get("vendor_name"),
        "po_number": match_result.get("po_number"),
        "grand_total": match_result.get("grand_total"),
        "decision": decision,
        "reasons": reasons,
        "checks": checks
    }

    save_to_history(record)
    return record

if __name__ == "__main__":
    from extractor import extract_invoice_data
    from matcher import match_invoice

    invoice = extract_invoice_data("invoice_001_happy.pdf")
    match = match_invoice(invoice)
    result = make_decision(match)

    print("\n" + "="*50)
    print(f"DECISION: {result['decision']}")
    print("="*50)
    for r in result["reasons"]:
        print(f"→ {r}")
    print("="*50)
