import pdfplumber
import re
import json

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

def parse_invoice_text(raw_text):
    data = {
        "invoice_number": "",
        "vendor_name": "",
        "invoice_date": "",
        "po_number": "",
        "subtotal": 0.0,
        "tax_amount": 0.0,
        "grand_total": 0.0,
        "currency": "INR",
        "line_items": [],
        "notes": "",
        "raw_text": raw_text
    }

    for line in raw_text.split("\n"):
        line = line.strip()

        if "Invoice Number:" in line:
            data["invoice_number"] = line.split("Invoice Number:")[-1].strip()

        elif "Date:" in line:
            data["invoice_date"] = line.split("Date:")[-1].strip()

        elif "Vendor:" in line:
            data["vendor_name"] = line.split("Vendor:")[-1].strip()

        elif "PO Reference:" in line:
            data["po_number"] = line.split("PO Reference:")[-1].strip()

        elif "Subtotal:" in line:
            amount = re.sub(r"[^\d.]", "", line.split("Subtotal:")[-1])
            data["subtotal"] = float(amount) if amount else 0.0

        elif "Tax" in line and "%" in line:
            amount = re.sub(r"[^\d.]", "", line.split(":")[-1])
            data["tax_amount"] = float(amount) if amount else 0.0

        elif "Grand Total:" in line:
            amount = re.sub(r"[^\d.]", "", line.split("Grand Total:")[-1])
            data["grand_total"] = float(amount) if amount else 0.0

        elif "Notes:" in line:
            data["notes"] = line.split("Notes:")[-1].strip()

    return data

def extract_invoice_data(pdf_path):
    raw_text = extract_text_from_pdf(pdf_path)
    return parse_invoice_text(raw_text)

if __name__ == "__main__":
    result = extract_invoice_data("sample_invoices/invoice_001_happy.pdf")
    print(json.dumps(result, indent=2))