import streamlit as st
import json
import os
import tempfile
from datetime import datetime
from extractor import extract_invoice_data
from matcher import match_invoice
from decision import make_decision, load_history

st.set_page_config(
    page_title="Invoice Processor",
    page_icon="🧾",
    layout="wide"
)

st.title("🧾 Invoice Processing System")
st.caption("Automated invoice validation and PO matching")

tab1, tab2 = st.tabs(["📤 Process Invoice", "📊 Dashboard"])

# ─── TAB 1 — PROCESS ───
with tab1:
    st.subheader("Upload an Invoice PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file:
        st.info(f"📄 File received: **{uploaded_file.name}**")

        if st.button("▶️ Run Invoice Processing", type="primary"):

            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            st.markdown("---")
            st.subheader("⚙️ Processing Steps")

            # Step 1 — Extract
            with st.status("📖 Step 1 — Extracting invoice data...", expanded=True) as s:
                invoice_data = extract_invoice_data(tmp_path)
                if invoice_data.get("extraction_error"):
                    s.update(label="❌ Step 1 — Extraction failed", state="error")
                    st.error(invoice_data["extraction_error"])
                    st.stop()
                else:
                    s.update(label="✅ Step 1 — Extraction complete", state="complete")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Invoice No.", invoice_data.get("invoice_number") or "MISSING")
                    col2.metric("Vendor", invoice_data.get("vendor_name") or "MISSING")
                    col3.metric("Grand Total", f"INR {invoice_data.get('grand_total', 0):,.2f}")

            # Step 2 — Match
            with st.status("🔍 Step 2 — Matching against PO database...", expanded=True) as s:
                match_result = match_invoice(invoice_data)
                checks = match_result.get("checks", {})
                s.update(label="✅ Step 2 — PO matching complete", state="complete")

                col1, col2, col3 = st.columns(3)
                col1.metric("PO Found", "✅ Yes" if checks.get("po_found") else "❌ No")
                col2.metric("Vendor Match", "✅ Yes" if checks.get("vendor_match") else "❌ No")
                col3.metric("Amount OK", "✅ Yes" if checks.get("amount_within_tolerance") else "❌ No")

            # Step 3 — Decision
            with st.status("⚖️ Step 3 — Making decision...", expanded=True) as s:
                result = make_decision(match_result)
                s.update(label="✅ Step 3 — Decision made", state="complete")

            # Final Decision
            st.markdown("---")
            st.subheader("📋 Final Decision")

            decision = result["decision"]

            if decision == "APPROVED":
                st.success(f"✅ APPROVED")
            elif decision == "REJECTED":
                st.error(f"❌ REJECTED")
            else:
                st.warning(f"⚠️ FLAGGED FOR REVIEW")

            for reason in result["reasons"]:
                st.write(f"→ {reason}")

            # Full details expander
            with st.expander("🔎 View Full Extraction Details"):
                st.json(invoice_data)

            with st.expander("🔎 View Full Match Details"):
                st.json(match_result)

            os.unlink(tmp_path)

# ─── TAB 2 — DASHBOARD ───
with tab2:
    st.subheader("📊 Processing History")

    history = load_history()

    if not history:
        st.info("No invoices processed yet. Upload one in the Process tab!")
    else:
        # Summary metrics
        total = len(history)
        approved = sum(1 for r in history if r["decision"] == "APPROVED")
        rejected = sum(1 for r in history if r["decision"] == "REJECTED")
        flagged = sum(1 for r in history if r["decision"] == "FLAGGED")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Processed", total)
        col2.metric("✅ Approved", approved)
        col3.metric("❌ Rejected", rejected)
        col4.metric("⚠️ Flagged", flagged)

        st.markdown("---")

        # History table
        for item in reversed(history):
            decision = item["decision"]
            if decision == "APPROVED":
                icon = "✅"
            elif decision == "REJECTED":
                icon = "❌"
            else:
                icon = "⚠️"

            with st.expander(
                f"{icon} {item['timestamp']} — {item.get('invoice_number', 'N/A')} "
                f"| {item.get('vendor_name', 'N/A')} "
                f"| INR {item.get('grand_total', 0):,.2f} "
                f"| {decision}"
            ):
                for reason in item.get("reasons", []):
                    st.write(f"→ {reason}")
                st.json(item)