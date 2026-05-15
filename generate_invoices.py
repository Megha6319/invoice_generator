from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os

output_dir = "sample_invoices"

def create_invoice(filename, invoice_number, vendor_name, po_number, line_items, tax_rate, notes=""):
    filepath = os.path.join(output_dir, filename)
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4

    # Header
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, "INVOICE")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 80, f"Invoice Number: {invoice_number}")
    c.drawString(50, height - 95, f"Date: 2026-05-10")
    c.drawString(50, height - 110, f"Vendor: {vendor_name}")
    c.drawString(50, height - 125, f"PO Reference: {po_number}")

    # Line items header
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, height - 170, "Description")
    c.drawString(300, height - 170, "Qty")
    c.drawString(370, height - 170, "Unit Price (INR)")
    c.drawString(480, height - 170, "Total (INR)")
    c.line(50, height - 175, 550, height - 175)

    # Line items
    c.setFont("Helvetica", 10)
    y = height - 195
    subtotal = 0
    for item in line_items:
        desc, qty, unit_price = item
        total = qty * unit_price
        subtotal += total
        c.drawString(50, y, desc)
        c.drawString(300, y, str(qty))
        c.drawString(370, y, f"{unit_price:,.2f}")
        c.drawString(480, y, f"{total:,.2f}")
        y -= 20

    # Totals
    tax = subtotal * tax_rate
    grand_total = subtotal + tax
    c.line(50, y - 5, 550, y - 5)
    c.drawString(370, y - 20, "Subtotal:")
    c.drawString(480, y - 20, f"INR {subtotal:,.2f}")
    c.drawString(370, y - 35, f"Tax ({int(tax_rate*100)}%):")
    c.drawString(480, y - 35, f"INR {tax:,.2f}")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(370, y - 50, "Grand Total:")
    c.drawString(480, y - 50, f"INR {grand_total:,.2f}")

    if notes:
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(50, y - 80, f"Notes: {notes}")

    c.save()
    print(f"Created: {filepath}")

# --- INVOICE 1 --- Happy path, matches PO-1001 perfectly
create_invoice(
    filename="invoice_001_happy.pdf",
    invoice_number="INV-2026-001",
    vendor_name="Zamp.ai",
    po_number="PO-1001",
    line_items=[
        ("AI Platform Subscription", 2, 100000.00),
        ("Onboarding Services", 1, 75000.00),
    ],
    tax_rate=0.18,
    notes="Payment due within 30 days."
)

# --- INVOICE 2 --- Amount over tolerance → FLAGGED
create_invoice(
    filename="invoice_002_over_tolerance.pdf",
    invoice_number="INV-2026-002",
    vendor_name="IBM",
    po_number="PO-1006",
    line_items=[
        ("IT Consulting", 10, 60000.00),
        ("Software Development", 5, 95000.00),
    ],
    tax_rate=0.18,
    notes="Prices reflect additional resource allocation."
)

# --- INVOICE 3 --- Missing invoice number → REJECTED
create_invoice(
    filename="invoice_003_missing_fields.pdf",
    invoice_number="",
    vendor_name="Swiggy",
    po_number="PO-1003",
    line_items=[
        ("Food Delivery Services", 1, 225000.00),
    ],
    tax_rate=0.18,
    notes=""
)

# --- INVOICE 4 --- Duplicate of invoice 1 → REJECTED
create_invoice(
    filename="invoice_004_duplicate.pdf",
    invoice_number="INV-2026-001",
    vendor_name="Zamp.ai",
    po_number="PO-1001",
    line_items=[
        ("AI Platform Subscription", 2, 100000.00),
        ("Onboarding Services", 1, 75000.00),
    ],
    tax_rate=0.18,
    notes="Duplicate submission."
)

# --- INVOICE 5 --- Closed PO → REJECTED
create_invoice(
    filename="invoice_005_closed_po.pdf",
    invoice_number="INV-2026-005",
    vendor_name="Infosys Limited",
    po_number="PO-1002",
    line_items=[
        ("IT Consulting Services", 5, 150000.00),
        ("Software Licenses", 3, 45000.00),
    ],
    tax_rate=0.18,
    notes="Monthly retainer invoice."
)

print("All invoices generated!")