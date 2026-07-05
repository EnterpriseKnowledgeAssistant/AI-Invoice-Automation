import sqlite3

DB_NAME = "invoices.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        vendor TEXT,
        vendor_uid TEXT,
        vendor_iban TEXT,

        invoice_number TEXT,
        invoice_date TEXT,
        due_date TEXT,

        net_amount REAL,
        vat_amount REAL,
        vat_percent REAL,
        gross_amount REAL,

        currency TEXT,
        cost_center TEXT,

        line_items TEXT,

        confidence_score REAL,
        anomalies TEXT,

        department TEXT,
        approval_required INTEGER DEFAULT 0,

        status TEXT DEFAULT 'Draft',

        pdf_path TEXT
    )
    """)
    conn.commit()
    conn.close()

def save_invoice(
    vendor,
    vendor_uid,
    vendor_iban,
    invoice_number,
    invoice_date,
    due_date,
    net_amount,
    vat_amount,
    vat_percent,
    gross_amount,
    currency,
    cost_center,
    line_items,
    confidence_score,
    anomalies,
    department,
    approval_required,
    status,
    pdf_path
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO invoices(
        vendor,
        vendor_uid,
        vendor_iban,
        invoice_number,
        invoice_date,
        due_date,
        net_amount,
        vat_amount,
        vat_percent,
        gross_amount,
        currency,
        cost_center,
        line_items,
        confidence_score,
        anomalies,
        department,
        approval_required,
        status,
        pdf_path
    )
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """,(
        vendor,
        vendor_uid,
        vendor_iban,
        invoice_number,
        invoice_date,
        due_date,
        net_amount,
        vat_amount,
        vat_percent,
        gross_amount,
        currency,
        cost_center,
        line_items,
        confidence_score,
        anomalies,
        department,
        int(approval_required),
        status,
        pdf_path
    ))

    conn.commit()
    conn.close()
def get_invoices():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        id,
        vendor,
        invoice_number,
        gross_amount,
        department,
        approval_required,
        status,
        pdf_path
    FROM invoices
    ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


def approve_invoice(invoice_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE invoices
    SET status = 'Approved'
    WHERE id = ?
    """, (invoice_id,))

    conn.commit()
    conn.close()


def reject_invoice(invoice_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE invoices
    SET status = 'Rejected'
    WHERE id = ?
    """, (invoice_id,))

    conn.commit()
    conn.close()