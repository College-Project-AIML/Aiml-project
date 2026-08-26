#!/usr/bin/env python3
"""
seed_faqs.py — Seed FAQ entries for the AI-powered chatbot.

Each FAQ entry maps a natural-language question to the correct
government scheme from the Karnataka seed dataset.  The scheme_id
column links the FAQ to a specific schemes row so the chatbot can
return the full scheme card on a match.

Scheme IDs are derived with uuid.uuid5 exactly the same way
seed_schemes.py generates them:
    uuid.uuid5(uuid.NAMESPACE_URL, f"scheme:{scheme_name}")

Usage:
    python -m scripts.seed_faqs
      -- or --
    python scripts/seed_faqs.py

Connection:
    Reads DATABASE_URL env-var first; same logic as seed_schemes.py.
"""

import os
import sys
import uuid
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")


def get_conn():
    return psycopg2.connect(DATABASE_URL)


def _scheme_id(name: str) -> str:
    """Reproduce the deterministic UUID used by seed_schemes.py."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"scheme:{name}"))


# ── FAQ seed data ────────────────────────────────────────────────────────────
# Each entry: (question, answer, scheme_name)
# scheme_name must match the exact string used in seed_schemes.py.
# Set scheme_name to None for generic FAQs not tied to a specific scheme.

FAQ_SEED = [
    # ── Post-Matric SC ────────────────────────────────────────────────────
    (
        "Is there a scholarship for SC students after 10th class?",
        "Yes — the Post-Matric Scholarship for SC Students covers tuition fees up to "
        "₹50,000/year and a ₹1,200/month maintenance allowance for Scheduled Caste "
        "students in post-matriculation courses.  Family income must be below ₹2.5 lakh.",
        "Post-Matric Scholarship for SC Students",
    ),
    (
        "What documents do I need for the SC post-matric scholarship?",
        "You need: Caste Certificate, Income Certificate, Marksheet (Class 10), "
        "Bank Account Details, and Institution Verification letter.  Apply at "
        "scholarships.gov.in before the state deadline.",
        "Post-Matric Scholarship for SC Students",
    ),
    # ── Post-Matric ST ────────────────────────────────────────────────────
    (
        "Scholarship available for Scheduled Tribe students in college?",
        "The Post-Matric Scholarship for ST Students provides full tuition coverage "
        "and a ₹1,500/month stipend for Scheduled Tribe students pursuing Class XI "
        "onwards, including professional and technical courses.  Income limit: ₹2.5 lakh.",
        "Post-Matric Scholarship for ST Students",
    ),
    # ── NMMSS ─────────────────────────────────────────────────────────────
    (
        "Which scholarship helps Class 8 students from low-income families continue school?",
        "The National Means-cum-Merit Scholarship (NMMSS) pays ₹12,000/year to "
        "students who scored 55% in Class VII and whose family income is below "
        "₹3.5 lakh.  Available for government/aided school students up to Class XII.",
        "National Means-cum-Merit Scholarship (NMMSS)",
    ),
    # ── PMSS ─────────────────────────────────────────────────────────────
    (
        "My father is an ex-army officer — are there scholarships for his children?",
        "Yes!  The Prime Minister's Scholarship Scheme (PMSS) gives ₹3,000/month "
        "to boys and ₹3,600/month to girls who are wards/widows of ex-servicemen or "
        "ex-coast-guard personnel, enrolled in first professional degree courses.",
        "Prime Minister's Scholarship Scheme (PMSS)",
    ),
    # ── INSPIRE ───────────────────────────────────────────────────────────
    (
        "I scored in the top 1% in my board exams and want to study science — any scholarship?",
        "The INSPIRE Scholarship for Higher Education (DST) pays ₹80,000/year to "
        "students in the top 1% of Class XII board results who pursue BSc/MSc in natural "
        "or basic sciences at recognised institutions.",
        "INSPIRE Scholarship for Higher Education",
    ),
    # ── Maulana Azad Fellowship ───────────────────────────────────────────
    (
        "Fellowship for minority community students doing PhD?",
        "The Maulana Azad National Fellowship for Minorities covers JRF (₹31,000/month) "
        "and an annual contingency grant of ₹20,000 for Muslim, Christian, Sikh, Buddhist, "
        "Jain, or Parsi students with NET/JRF qualification pursuing MPhil/PhD.",
        "Maulana Azad National Fellowship for Minorities",
    ),
    # ── Begum Hazrat Mahal ────────────────────────────────────────────────
    (
        "Scholarship for minority girls studying in Class 9 to 12?",
        "The Begum Hazrat Mahal National Scholarship supports meritorious minority "
        "community girls in Classes IX–XII: ₹5,000/year for Class IX–X and "
        "₹6,000/year for Class XI–XII.  Requires 50% marks and family income below ₹2 lakh.",
        "Begum Hazrat Mahal National Scholarship for Minority Girls",
    ),
    # ── PMKVY ────────────────────────────────────────────────────────────
    (
        "Free skill training courses for unemployed youth?",
        "Pradhan Mantri Kaushal Vikas Yojana (PMKVY) offers free, industry-relevant "
        "short-term skill training with government-recognised certification and a "
        "₹8,000 monetary reward on passing.  Open to Indian youth aged 15–45 with "
        "no minimum education requirement for most courses.",
        "Pradhan Mantri Kaushal Vikas Yojana (PMKVY)",
    ),
    # ── Karnataka Vidyasiri ───────────────────────────────────────────────
    (
        "State-level scholarship for SC/ST students in Karnataka colleges?",
        "Karnataka Vidyasiri Scholarship for SC/ST reimburses full tuition (up to "
        "₹30,000/year) and provides ₹1,000/month maintenance allowance for SC/ST "
        "students domiciled in Karnataka pursuing UG/PG courses.  Income limit: ₹2.5 lakh.",
        "Karnataka Vidyasiri Scholarship for SC/ST",
    ),
    # ── Karnataka Bhagyalakshmi ───────────────────────────────────────────
    (
        "Government scheme for girl child born in a BPL family in Karnataka?",
        "Karnataka Bhagyalakshmi Scheme gives a ₹19,300 bond at birth that matures "
        "to ₹1,00,034 at age 18.  The girl child must be born in a BPL family and "
        "registered with the BPL ration card within one year of birth.",
        "Karnataka Bhagyalakshmi Scheme",
    ),
    # ── Karnataka Arivu ───────────────────────────────────────────────────
    (
        "Interest-free education loan for minority students in Karnataka?",
        "Karnataka Arivu Educational Loan provides up to ₹2 lakh interest-free for "
        "minority community students pursuing engineering, medicine, law, or management "
        "in Karnataka.  Family income must be below ₹2.5 lakh.",
        "Karnataka Arivu Educational Loan for Minorities",
    ),
    # ── Karnataka Sanchi Honnamma ─────────────────────────────────────────
    (
        "Merit scholarship for girl students entering degree college in Karnataka?",
        "Karnataka Sanchi Honnamma Scholarship awards ₹10,000/year to girl students "
        "who scored first class in PUC II and are enrolling in a first-year degree "
        "course (Arts/Science/Commerce) in Karnataka.  Family income limit: ₹2 lakh.",
        "Karnataka Sanchi Honnamma Scholarship for Girls",
    ),
    # ── Karnataka Devaraj Urs ─────────────────────────────────────────────
    (
        "Scholarship for OBC / backward class students in Karnataka from Class 1 to PG?",
        "Karnataka Devaraj Urs Backward Classes Scholarship covers pre-matric "
        "(₹3,000/year) and post-matric (₹10,000/year) levels for backward class "
        "students domiciled in Karnataka.  Income limits: ₹1 lakh (pre-matric), "
        "₹2 lakh (post-matric).",
        "Karnataka Devaraj Urs Backward Classes Scholarship",
    ),
    # ── Karnataka Arogya Sanjeevini ───────────────────────────────────────
    (
        "Free health insurance for families in Karnataka?",
        "Karnataka Arogya Sanjeevini provides cashless treatment up to ₹5 lakh per "
        "family per year across empanelled hospitals.  Open to all Karnataka families "
        "with annual income below ₹5 lakh; BPL card holders are automatically eligible.",
        "Karnataka Arogya Sanjeevini Health Insurance",
    ),
    # ── Karnataka Udyogini ────────────────────────────────────────────────
    (
        "Loan scheme for women to start a small business in Karnataka?",
        "Karnataka Udyogini Scheme provides subsidised loans up to ₹3 lakh for women "
        "aged 18–45 from Karnataka to start or expand micro/small enterprises.  "
        "Income limit: ₹1.5 lakh (general) / ₹2 lakh (SC/ST).",
        "Karnataka Udyogini Scheme for Women Entrepreneurs",
    ),
    # ── Karnataka Ambedkar Overseas ───────────────────────────────────────
    (
        "Scholarship to study abroad for SC/ST students from Karnataka?",
        "Karnataka Ambedkar Overseas Scholarship covers tuition (up to ₹20 lakh/year), "
        "living expenses (₹1 lakh/year), and air travel (₹1.5 lakh one-time) for "
        "SC/ST students admitted to top-500 QS-ranked universities for masters or PhD.  "
        "Income limit: ₹6 lakh.  Must have lived in Karnataka for 10+ years.",
        "Karnataka Ambedkar Overseas Scholarship",
    ),
    # ── PRAGATI ───────────────────────────────────────────────────────────
    (
        "Scholarship for girl students in engineering or technical diploma?",
        "PRAGATI Scholarship for Girls in Technical Education pays ₹50,000/year to "
        "girl students in the first year of AICTE-approved degree/diploma programmes.  "
        "Family income must be below ₹8 lakh.",
        "PRAGATI Scholarship for Girls in Technical Education",
    ),
    # ── Swanath ───────────────────────────────────────────────────────────
    (
        "Is there a scholarship for orphan students doing engineering?",
        "Swanath Scholarship supports orphan students and wards of martyred defence/CAPF "
        "personnel in AICTE-approved technical institutions with ₹50,000/year.  Income "
        "limit: ₹8 lakh.",
        "Swanath Scholarship for Orphan Students",
    ),
    # ── Karnataka PhD Fellowship ───────────────────────────────────────────
    (
        "Monthly stipend for SC/ST researchers doing PhD in Karnataka?",
        "Karnataka PhD Fellowship for SC/ST Researchers provides ₹25,000/month stipend "
        "and ₹15,000/year contingency grant (up to 5 years) for SC/ST scholars in NET/"
        "KSET-qualified PhD programmes at Karnataka state universities.  Income limit: ₹3 lakh.",
        "Karnataka PhD Fellowship for SC/ST Researchers",
    ),
    # ── Karnataka Skill Development ───────────────────────────────────────
    (
        "Free skill training in Karnataka for youth aged 18-35?",
        "Karnataka Skill Development (PMKVY State Component) offers free training in "
        "IT, healthcare, construction, retail, and manufacturing with "
        "government-recognised certification and placement support.  Requires "
        "10th pass; open to Karnataka residents aged 18–35.",
        "Karnataka Skill Development - PMKVY State Component",
    ),
    # ── Post-Matric OBC ───────────────────────────────────────────────────
    (
        "National scholarship for OBC students in post-matric courses?",
        "Post-Matric Scholarship for OBC Students gives ₹750/month maintenance allowance "
        "plus academic fee reimbursement (up to ₹15,000/year) for Other Backward Classes "
        "students.  Family income must be below ₹1.5 lakh.",
        "Post-Matric Scholarship for OBC Students",
    ),
    # ── Karnataka CM Housing ──────────────────────────────────────────────
    (
        "Government housing subsidy for low-income families in Karnataka?",
        "Karnataka CM Housing Scheme for EWS provides up to ₹2.5 lakh subsidy for "
        "economically weaker section families (income below ₹3 lakh) to build or "
        "buy a dwelling.  Priority for SC/ST and women-headed households without "
        "an existing pucca house.",
        "Karnataka CM Housing Scheme for EWS",
    ),
    # ── Karnataka Mathrushree ─────────────────────────────────────────────
    (
        "Cash benefit for pregnant women from BPL families in Karnataka?",
        "Karnataka Mathrushree Maternity Benefit gives ₹6,000 in installments to BPL "
        "pregnant women who register at a government health facility and deliver "
        "institutionally.  Applicable for the first two live births.",
        "Karnataka Mathrushree Maternity Benefit",
    ),
    # ── Generic / cross-scheme ────────────────────────────────────────────
    (
        "How do I apply for a government scholarship in India?",
        "Most central scholarships are applied for through the National Scholarship "
        "Portal at scholarships.gov.in.  State-level schemes (like Karnataka ones) have "
        "separate portals — check sw.karnataka.gov.in, dce.karnataka.gov.in, or "
        "bcwd.karnataka.gov.in depending on the category.  You will need Aadhaar, "
        "income certificate, caste certificate (if applicable), and latest marksheet.",
        None,   # no single scheme linked
    ),
    (
        "What is the income limit for most government scholarships?",
        "Income limits vary by scheme.  Most central scholarships for SC/ST/OBC cap "
        "family income at ₹1.5–₹2.5 lakh/year.  Merit-based science scholarships "
        "(INSPIRE, PRAGATI) allow up to ₹6–8 lakh.  Karnataka state schemes generally "
        "use ₹2–₹3 lakh as the upper limit.  Always check the specific scheme for "
        "the exact figure.",
        None,
    ),
]


# ── Seeder ──────────────────────────────────────────────────────────────────

def seed_faqs(conn) -> None:
    cur = conn.cursor()
    inserted = 0
    skipped = 0

    for question, answer, scheme_name in FAQ_SEED:
        scheme_id = _scheme_id(scheme_name) if scheme_name else None

        # Verify the scheme actually exists before linking
        if scheme_id:
            cur.execute("SELECT 1 FROM schemes WHERE id = %s", (scheme_id,))
            if not cur.fetchone():
                print(f"  ⚠️  Scheme not found, skipping link: {scheme_name}")
                scheme_id = None

        # Upsert: avoid duplicates if run twice (match on question text)
        cur.execute(
            """
            INSERT INTO faqs (question, answer, scheme_id)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (question, answer, scheme_id),
        )
        if cur.rowcount:
            print(f"  💬 FAQ inserted: {question[:70]}...")
            inserted += 1
        else:
            skipped += 1

    conn.commit()
    cur.close()
    print(f"\n✅ FAQs seeded: {inserted} inserted, {skipped} skipped (already existed)")


def print_summary(conn) -> None:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM faqs")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM faqs WHERE scheme_id IS NOT NULL")
    linked = cur.fetchone()[0]
    print(f"\n📊 FAQ table: {total} rows total, {linked} linked to a scheme")
    cur.close()


if __name__ == "__main__":
    print("🚀 Seeding FAQ data...\n")
    conn = get_conn()
    try:
        seed_faqs(conn)
        print_summary(conn)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
    print("\n🏁 Done!")
