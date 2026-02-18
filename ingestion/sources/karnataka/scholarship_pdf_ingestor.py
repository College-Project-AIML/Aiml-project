# ingestion/sources/central/scholarship_pdf_ingestor.py

import requests
import pdfplumber
import psycopg2
import os
import uuid
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

PDF_URL = "https://dce.karnataka.gov.in/storage/pdf-files/Scholarship%20Information.pdf"

def get_db():
    return psycopg2.connect(DB_URL)

def init_table():
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS govt_scholarships (
            id UUID PRIMARY KEY,
            source TEXT,
            scheme_name TEXT,
            ministry TEXT,
            category TEXT,
            eligibility TEXT,
            description TEXT,
            link TEXT,
            state TEXT,
            tags TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        print("Table or type likely exists. Ignoring UniqueViolation.")
        conn.rollback()
    except Exception as e:
        print(f"Error creating table: {e}")
        conn.rollback()
        raise
    cur.close()
    conn.close()

def download_pdf():
    os.makedirs("tmp", exist_ok=True)
    path = "tmp/karnataka_scholarships.pdf"
    r = requests.get(PDF_URL)
    with open(path, "wb") as f:
        f.write(r.content)
    return path

def parse_pdf(path):
    records = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")
            for line in lines:
                if len(line.strip()) > 10:
                    records.append(line.strip())
    return records

def save_record(name):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO govt_scholarships 
    (id, source, scheme_name, ministry, category, eligibility, description, link, state, tags)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT DO NOTHING
    """, (
        str(uuid.uuid4()),
        "dce.karnataka.gov.in",
        name,
        "Government of Karnataka",
        "Scholarship",
        "Refer PDF",
        "Fetched from Karnataka DCE PDF",
        PDF_URL,
        "Karnataka",
        ["govt", "scholarship", "karnataka"]
    ))
    conn.commit()
    cur.close()
    conn.close()

def run():
    init_table()
    pdf_path = download_pdf()
    records = parse_pdf(pdf_path)

    count = 0
    for r in records:
        save_record(r)
        count += 1

    print(f"Ingested {count} records from Karnataka PDF")

if __name__ == "__main__":
    run()
