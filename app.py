

import os
from dotenv import load_dotenv
from google import genai
import streamlit as st
import json
import importlib

from database import (
    create_table,
    save_invoice,
    get_invoices,
    approve_invoice,
    reject_invoice
)

# Resolve PdfReader import from either PyPDF2 or pypdf (some installs use one or the other)
PdfReader = None
for pkg in ("PyPDF2", "pypdf"):
    try:
        spec = importlib.util.find_spec(pkg)
        if spec is not None:
            module = importlib.import_module(pkg)
            # both packages expose PdfReader at top-level
            PdfReader = getattr(module, "PdfReader", None)
            if PdfReader:
                break
    except Exception:
        continue


from pathlib import Path

dotenv_path = Path(__file__).parent / ".env"

st.write("Looking for .env:", dotenv_path)
st.write("File exists:", dotenv_path.exists())

load_dotenv(dotenv_path)
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

st.write("Key loaded:", GEMINI_API_KEY is not None)

if GEMINI_API_KEY:
    st.write("Length:", len(GEMINI_API_KEY))
    st.write("Starts with:", GEMINI_API_KEY[:8])

if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY is missing.")
    st.stop()

client = genai.Client(api_key=GEMINI_API_KEY)
# ----------------------------
# Database
# ----------------------------

create_table()

# ----------------------------
# Streamlit
# ----------------------------

st.set_page_config(
    page_title="AI Invoice Automation",
    layout="wide"
)

st.title("📄 AI Invoice Automation")

uploaded_file = st.file_uploader(
    "Upload Invoice PDF",
    type=["pdf"]
)

# ----------------------------
# Save uploaded PDF
# ----------------------------

pdf_path = ""

if uploaded_file:

    os.makedirs("uploads", exist_ok=True)

    pdf_path = os.path.join(
        "uploads",
        uploaded_file.name
    )

    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"Uploaded : {uploaded_file.name}")

    st.success(f"PDF Stored : {pdf_path}")

# ----------------------------
# Read PDF
# ----------------------------

if uploaded_file:

    reader = PdfReader(pdf_path)

    extracted_text = ""

    for page in reader.pages:

        text = page.extract_text()

        if text:

            extracted_text += text + "\n"

    st.subheader("Extracted Text")

    st.text_area(

        "PDF Content",

        extracted_text,

        height=300

    )

# ----------------------------
# Gemini Extraction
# ----------------------------

if uploaded_file:

    with st.spinner("Extracting Invoice..."):

        prompt = f"""
You are an AI invoice extraction assistant.

Extract the invoice information from the text below.

Return ONLY valid JSON.

{{
  "vendor": "",
  "vendor_uid": "",
  "vendor_iban": "",
  "invoice_number": "",
  "invoice_date": "",
  "due_date": "",
  "net_amount": 0,
  "vat_amount": 0,
  "vat_percent": 0,
  "gross_amount": 0,
  "currency": "",
  "cost_center": "",
  "line_items": [],
  "confidence_score": 0,
  "anomalies": ""
}}

Invoice Text:

{extracted_text}
"""
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            ai_text = response.text.strip()
            ai_text = ai_text.replace("```json", "").replace("```", "").strip()

            invoice_json = json.loads(ai_text)

            st.subheader("AI Extracted Invoice")
            st.json(invoice_json)


        except Exception as e:
            st.warning(f"Gemini Error: {e}")

            invoice_json = {
                "vendor": "",
                "invoice_number": "",
                "amount": 0
            }
else:
    invoice_json = {
        "vendor": "",
        "invoice_number": "",
        "amount": 0
    }

# ----------------------------
# Manual Review
# ----------------------------

vendor = st.text_input(
    "Vendor",
    value=invoice_json.get("vendor", "")
)

invoice_number = st.text_input(
    "Invoice Number",
    value=invoice_json.get("invoice_number", "")
)

amount_value = invoice_json.get("gross_amount", 0)

try:
    amount_value = float(amount_value)
except:
    amount_value = 0.0

amount = st.number_input(
    "Amount",
    value=amount_value,
    format="%.2f"
)

# ----------------------------
# Auto Department Routing
# ----------------------------

cost_center = invoice_json.get("cost_center", "").upper()

if "FIN" in cost_center:
    department = "Finance"
elif "HR" in cost_center:
    department = "Human Resources"
elif "IT" in cost_center:
    department = "IT"
elif "SALES" in cost_center:
    department = "Sales"
else:
    department = "General"

# ----------------------------
# Approval Rule
# ----------------------------

gross_amount = float(invoice_json.get("gross_amount", 0))

approval_required = gross_amount > 10000
confidence = float(invoice_json.get("confidence_score", 0))

if confidence < 0.90:
    st.warning("⚠️ Low confidence. Please verify the extracted invoice.")
else:
    st.success(f"✅ AI Confidence: {confidence * 100:.0f}%")
# ----------------------------
# Save Invoice
# ----------------------------
if approval_required:
    st.warning("⚠️ This invoice requires manager approval.")
else:
    st.success("✅ This invoice can be processed automatically.")

if st.button("💾 Save Invoice"):

    save_invoice(
        vendor=invoice_json.get("vendor", ""),
        vendor_uid=invoice_json.get("vendor_uid", ""),
        vendor_iban=invoice_json.get("vendor_iban", ""),
        invoice_number=invoice_json.get("invoice_number", ""),
        invoice_date=invoice_json.get("invoice_date", ""),
        due_date=invoice_json.get("due_date", ""),
        net_amount=invoice_json.get("net_amount", 0),
        vat_amount=invoice_json.get("vat_amount", 0),
        vat_percent=invoice_json.get("vat_percent", 0),
        gross_amount=invoice_json.get("gross_amount", 0),
        currency=invoice_json.get("currency", ""),
        cost_center=invoice_json.get("cost_center", ""),
        line_items=json.dumps(invoice_json.get("line_items", [])),
        confidence_score=invoice_json.get("confidence_score", 0),
        anomalies=invoice_json.get("anomalies", ""),
        department="Finance",
      approval_required=approval_required,
        status="Draft",
        pdf_path=pdf_path
    )

st.success("Invoice Saved Successfully!")
st.rerun()

# ----------------------------
# Saved Invoices
# ----------------------------

st.markdown("---")
st.header("📂 Saved Invoices")

invoices = get_invoices()

# ----------------------------
# Dashboard
# ----------------------------

total = len(invoices)
approved = len([i for i in invoices if i[6] == "Approved"])
rejected = len([i for i in invoices if i[6] == "Rejected"])
pending = len([i for i in invoices if i[6] == "Draft"])

col1, col2, col3, col4 = st.columns(4)

col1.metric("📄 Total", total)
col2.metric("✅ Approved", approved)
col3.metric("❌ Rejected", rejected)
col4.metric("⏳ Pending", pending)

if invoices:

    for invoice in invoices:
        ...