#!/usr/bin/env python3
"""
seed_schemes.py — Comprehensive seed data for the Government Schemes Discovery Platform.

Populates PostgreSQL with realistic Indian government scholarship and welfare scheme data:
  • 6 providers (ministries / departments)
  • 8 categories
  • 25+ schemes with eligibility rules, benefits, and required documents

Usage:
    python scripts/seed_schemes.py

Connection:
    Reads DATABASE_URL env-var first; falls back to individual POSTGRES_* vars
    or hard-coded defaults (localhost:5433 / aiml_core / admin / securepassword).
"""

import os
import sys
import uuid
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "aiml_core"),
    "user": os.getenv("POSTGRES_USER", "admin"),
    "password": os.getenv("POSTGRES_PASSWORD", "securepassword"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5433"),
}

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL and not DB_CONFIG["password"]:
    raise ValueError("Neither DATABASE_URL nor POSTGRES_PASSWORD is set")


def get_conn():
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    return psycopg2.connect(**DB_CONFIG)


def run_schema(conn):
    schema_path = os.path.join(os.path.dirname(__file__), "..", "schemas", "postgres.sql")
    with open(schema_path, "r") as f:
        sql = f.read()
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    cur.close()
    print("✅ Schema applied")


def seed_providers(conn):
    providers = [
        ("Ministry of Education", "central_ministry", "https://www.education.gov.in"),
        ("Ministry of Social Justice and Empowerment", "central_ministry", "https://socialjustice.gov.in"),
        ("Department of Science and Technology", "central_ministry", "https://dst.gov.in"),
        ("Government of Karnataka", "state_department", "https://karnataka.gov.in"),
        ("Ministry of Tribal Affairs", "central_ministry", "https://tribal.nic.in"),
        ("Ministry of Minority Affairs", "central_ministry", "https://minorityaffairs.gov.in"),
    ]
    cur = conn.cursor()
    ids = {}
    for name, ptype, website in providers:
        pid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"provider:{name}"))
        cur.execute("""
            INSERT INTO providers (id, name, type, website)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (pid, name, ptype, website))
        ids[name] = pid
        print(f"  📌 Provider: {name}")
    conn.commit()
    cur.close()
    return ids


def seed_categories(conn):
    categories = [
        ("Scholarship", "scholarship", "Financial aid for students based on merit or need"),
        ("Fellowship", "fellowship", "Research and academic fellowships"),
        ("Grant", "grant", "Financial grants for specific purposes"),
        ("Loan", "loan", "Educational and business loans with subsidized interest"),
        ("Subsidy", "subsidy", "Government subsidies on goods and services"),
        ("Skill Program", "skill_program", "Skill development and vocational training"),
        ("Training Program", "training_program", "Professional training programs"),
        ("Welfare Scheme", "welfare_scheme", "Social welfare and protection schemes"),
    ]
    cur = conn.cursor()
    ids = {}
    for name, slug, desc in categories:
        cid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"category:{name}"))
        cur.execute("""
            INSERT INTO categories (id, name, slug, description)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (name) DO NOTHING
        """, (cid, name, slug, desc))
        ids[name] = cid
        print(f"  📂 Category: {name}")
    conn.commit()
    cur.close()
    return ids


def seed_schemes(conn, provider_ids, category_ids):
    schemes = [
        {
            "name": "Post-Matric Scholarship for SC Students",
            "description": "Scholarship for Scheduled Caste students pursuing post-matriculation courses including professional, technical, and vocational courses. Covers tuition fees, maintenance allowance, and book grants.",
            "eligibility_text": "SC students who have passed matriculation. Family income should not exceed Rs 2.5 lakh per annum. Must be enrolled in recognized institutions.",
            "state_code": None,
            "provider": "Ministry of Social Justice and Empowerment",
            "category": "Scholarship",
            "source": "scholarships.gov.in",
            "link": "https://scholarships.gov.in",
            "tags": ["sc", "post-matric", "scholarship", "national"],
            "confidence_score": 0.95,
            "eligibility": {"min_age": 15, "max_age": 35, "max_income": 250000, "gender": ["male", "female", "transgender"], "caste": ["SC"], "states": None, "education_level": "10th_pass"},
            "benefits": [
                ("tuition_fee", "Full tuition fee reimbursement", 50000, "annual"),
                ("maintenance", "Monthly maintenance allowance", 1200, "monthly"),
            ],
            "documents": ["Caste Certificate", "Income Certificate", "Marksheet", "Bank Account Details", "Institution Verification"],
        },
        {
            "name": "Post-Matric Scholarship for ST Students",
            "description": "Financial assistance to Scheduled Tribe students for post-matriculation studies. Supports students from Class XI onwards including professional and technical courses.",
            "eligibility_text": "ST students enrolled in post-matric courses. Family income must not exceed Rs 2.5 lakh per annum.",
            "state_code": None,
            "provider": "Ministry of Tribal Affairs",
            "category": "Scholarship",
            "source": "scholarships.gov.in",
            "link": "https://tribal.nic.in",
            "tags": ["st", "post-matric", "scholarship", "tribal"],
            "confidence_score": 0.95,
            "eligibility": {"min_age": 15, "max_age": 35, "max_income": 250000, "gender": ["male", "female", "transgender"], "caste": ["ST"], "states": None, "education_level": "10th_pass"},
            "benefits": [
                ("tuition_fee", "Complete tuition fee coverage", 50000, "annual"),
                ("stipend", "Monthly living stipend", 1500, "monthly"),
            ],
            "documents": ["Tribe Certificate", "Income Certificate", "Marksheet", "Bank Passbook", "Admission Letter"],
        },
        {
            "name": "National Means-cum-Merit Scholarship (NMMSS)",
            "description": "Merit-based scholarship to reduce dropout rate at Class VIII and encourage students from economically weaker sections to continue studies up to Class XII.",
            "eligibility_text": "Students scoring 55% in Class VII exam. Family income below Rs 3.5 lakh per annum. Must be studying in government/aided schools.",
            "state_code": None,
            "provider": "Ministry of Education",
            "category": "Scholarship",
            "source": "scholarships.gov.in",
            "link": "https://scholarships.gov.in",
            "tags": ["merit", "means", "scholarship", "school"],
            "confidence_score": 0.93,
            "eligibility": {"min_age": 12, "max_age": 18, "max_income": 350000, "gender": ["male", "female"], "caste": ["SC", "ST", "OBC", "general"], "states": None, "education_level": "7th_pass"},
            "benefits": [("scholarship", "Annual scholarship amount", 12000, "annual")],
            "documents": ["Income Certificate", "School Certificate", "Marksheet", "Bank Account"],
        },
        {
            "name": "Prime Minister's Scholarship Scheme (PMSS)",
            "description": "Scholarship for wards and widows of ex-servicemen and ex-coast guard personnel. Provides Rs 3,000/month for boys and Rs 3,600/month for girls in professional courses.",
            "eligibility_text": "Wards/widows of ex-servicemen/ex-coast guard. Minimum 60% in qualifying exam. For first professional degree courses only.",
            "state_code": None,
            "provider": "Ministry of Education",
            "category": "Scholarship",
            "source": "scholarships.gov.in",
            "link": "https://scholarships.gov.in",
            "tags": ["defence", "ex-servicemen", "professional", "scholarship"],
            "confidence_score": 0.94,
            "eligibility": {"min_age": 17, "max_age": 25, "max_income": 600000, "gender": ["male", "female"], "caste": ["SC", "ST", "OBC", "general"], "states": None, "education_level": "12th_pass"},
            "benefits": [
                ("stipend_male", "Monthly scholarship for boys", 3000, "monthly"),
                ("stipend_female", "Monthly scholarship for girls", 3600, "monthly"),
            ],
            "documents": ["Ex-Serviceman Certificate", "Marksheet", "Admission Letter", "Bank Account"],
        },
        {
            "name": "INSPIRE Scholarship for Higher Education",
            "description": "Innovation in Science Pursuit for Inspired Research. Scholarship for students pursuing natural and basic science courses at BSc and MSc level.",
            "eligibility_text": "Students in top 1% of Class XII board exams. Pursuing BSc/MSc in natural/basic sciences at recognized institutions.",
            "state_code": None,
            "provider": "Department of Science and Technology",
            "category": "Scholarship",
            "source": "dst.gov.in",
            "link": "https://online-inspire.gov.in",
            "tags": ["science", "research", "inspire", "merit"],
            "confidence_score": 0.92,
            "eligibility": {"min_age": 17, "max_age": 22, "max_income": None, "gender": ["male", "female"], "caste": ["SC", "ST", "OBC", "general"], "states": None, "education_level": "12th_pass"},
            "benefits": [("scholarship", "Annual scholarship for science courses", 80000, "annual")],
            "documents": ["Board Marksheet", "Admission Letter", "Institution Certificate"],
        },
        {
            "name": "Maulana Azad National Fellowship for Minorities",
            "description": "Fellowship for students from minority communities to pursue MPhil and PhD. Covers JRF and SRF with HRA and contingency grants.",
            "eligibility_text": "Minority community students (Muslim, Christian, Sikh, Buddhist, Jain, Parsi) with NET/JRF qualification for PhD programs.",
            "state_code": None,
            "provider": "Ministry of Minority Affairs",
            "category": "Fellowship",
            "source": "minorityaffairs.gov.in",
            "link": "https://minorityaffairs.gov.in",
            "tags": ["minority", "phd", "fellowship", "research"],
            "confidence_score": 0.91,
            "eligibility": {"min_age": 21, "max_age": 35, "max_income": 250000, "gender": ["male", "female"], "caste": ["SC", "ST", "OBC", "general"], "states": None, "education_level": "post_graduate"},
            "benefits": [
                ("jrf", "Junior Research Fellowship stipend", 31000, "monthly"),
                ("contingency", "Annual contingency grant", 20000, "annual"),
            ],
            "documents": ["Minority Community Certificate", "NET Score Card", "Admission Letter", "Income Certificate"],
        },
        {
            "name": "Begum Hazrat Mahal National Scholarship for Minority Girls",
            "description": "Scholarship for meritorious girls from minority communities studying in Classes IX to XII to promote higher education among minority girls.",
            "eligibility_text": "Minority community girls with 50% marks in previous exam. Family income below Rs 2 lakh. Classes IX to XII.",
            "state_code": None,
            "provider": "Ministry of Minority Affairs",
            "category": "Scholarship",
            "source": "scholarships.gov.in",
            "link": "https://scholarships.gov.in",
            "tags": ["minority", "girls", "scholarship", "school"],
            "confidence_score": 0.90,
            "eligibility": {"min_age": 13, "max_age": 19, "max_income": 200000, "gender": ["female"], "caste": ["SC", "ST", "OBC", "general"], "states": None, "education_level": "8th_pass"},
            "benefits": [
                ("scholarship_9_10", "Scholarship for Class IX-X", 5000, "annual"),
                ("scholarship_11_12", "Scholarship for Class XI-XII", 6000, "annual"),
            ],
            "documents": ["Minority Certificate", "Income Certificate", "Marksheet", "School Certificate"],
        },
        {
            "name": "Pradhan Mantri Kaushal Vikas Yojana (PMKVY)",
            "description": "Flagship skill development scheme enabling Indian youth to take up industry-relevant training. Free short-term training with certification and placement assistance.",
            "eligibility_text": "Indian youth aged 15-45 with Aadhaar. No minimum education requirement for most courses. Priority to school dropouts and unemployed.",
            "state_code": None,
            "provider": "Ministry of Education",
            "category": "Skill Program",
            "source": "pmkvyofficial.org",
            "link": "https://pmkvyofficial.org",
            "tags": ["skill", "training", "youth", "employment", "pmkvy"],
            "confidence_score": 0.93,
            "eligibility": {"min_age": 15, "max_age": 45, "max_income": None, "gender": ["male", "female", "transgender"], "caste": ["SC", "ST", "OBC", "general"], "states": None, "education_level": None},
            "benefits": [
                ("training", "Free industry-relevant skill training", None, "one_time"),
                ("certification", "Government-recognized certification", None, "one_time"),
                ("reward", "Monetary reward on certification", 8000, "one_time"),
            ],
            "documents": ["Aadhaar Card", "Bank Account"],
        },
        {
            "name": "Karnataka Vidyasiri Scholarship for SC/ST",
            "description": "State scholarship for SC/ST students pursuing higher education in Karnataka. Covers tuition fees and provides maintenance allowance for undergraduate and postgraduate courses.",
            "eligibility_text": "SC/ST students domiciled in Karnataka. Family income below Rs 2.5 lakh. Must be enrolled in recognized colleges within Karnataka.",
            "state_code": "KA",
            "provider": "Government of Karnataka",
            "category": "Scholarship",
            "source": "sw.karnataka.gov.in",
            "link": "https://sw.karnataka.gov.in",
            "tags": ["sc", "st", "karnataka", "scholarship", "higher-education"],
            "confidence_score": 0.90,
            "eligibility": {"min_age": 17, "max_age": 30, "max_income": 250000, "gender": ["male", "female"], "caste": ["SC", "ST"], "states": ["KA"], "education_level": "12th_pass"},
            "benefits": [
                ("tuition_fee", "Full tuition fee reimbursement", 30000, "annual"),
                ("maintenance", "Maintenance allowance", 1000, "monthly"),
            ],
            "documents": ["Caste Certificate", "Income Certificate", "Karnataka Domicile", "Marksheet"],
        },
        {
            "name": "Karnataka Bhagyalakshmi Scheme",
            "description": "Financial assistance for girl children born in BPL families. A bond of Rs 19,300 at birth matures to Rs 1,00,034 at age 18. Additional benefits for education milestones.",
            "eligibility_text": "Girl children born in BPL families in Karnataka. Must be registered within one year of birth. Family must hold BPL ration card.",
            "state_code": "KA",
            "provider": "Government of Karnataka",
            "category": "Welfare Scheme",
            "source": "dwcd.karnataka.gov.in",
            "link": "https://dwcd.karnataka.gov.in",
            "tags": ["girl", "child", "bpl", "karnataka", "welfare"],
            "confidence_score": 0.88,
            "eligibility": {"min_age": 0, "max_age": 1, "max_income": 120000, "gender": ["female"], "caste": ["SC", "ST", "OBC", "general"], "states": ["KA"], "education_level": None},
            "benefits": [
                ("bond", "Fixed deposit bond at birth", 19300, "one_time"),
                ("maturity", "Maturity value at age 18", 100034, "one_time"),
            ],
            "documents": ["Birth Certificate", "BPL Ration Card", "Hospital Discharge Summary"],
        },
        {
            "name": "Karnataka Arivu Educational Loan for Minorities",
            "description": "Interest-free educational loan for minority community students pursuing professional and technical courses in Karnataka.",
            "eligibility_text": "Minority students of Karnataka with family income below Rs 2.5 lakh. Pursuing engineering, medicine, law, or management courses.",
            "state_code": "KA",
            "provider": "Government of Karnataka",
            "category": "Loan",
            "source": "kmdc.karnataka.gov.in",
            "link": "https://kmdc.karnataka.gov.in",
            "tags": ["minority", "loan", "education", "karnataka"],
            "confidence_score": 0.88,
            "eligibility": {"min_age": 17, "max_age": 30, "max_income": 250000, "gender": ["male", "female"], "caste": ["SC", "ST", "OBC", "general"], "states": ["KA"], "education_level": "12th_pass"},
            "benefits": [("loan", "Interest-free educational loan", 200000, "one_time")],
            "documents": ["Minority Certificate", "Income Certificate", "Admission Letter", "Karnataka Domicile"],
        },
        {
            "name": "Karnataka Sanchi Honnamma Scholarship for Girls",
            "description": "Merit-based scholarship for girl students from economically weaker sections pursuing first-year degree courses in arts, science, and commerce in Karnataka.",
            "eligibility_text": "Girl students with first class in PUC II. Family income below Rs 2 lakh. Must be enrolled in first-year degree course in Karnataka.",
            "state_code": "KA",
            "provider": "Government of Karnataka",
            "category": "Scholarship",
            "source": "dce.karnataka.gov.in",
            "link": "https://dce.karnataka.gov.in",
            "tags": ["girls", "merit", "scholarship", "karnataka", "degree"],
            "confidence_score": 0.89,
            "eligibility": {"min_age": 17, "max_age": 22, "max_income": 200000, "gender": ["female"], "caste": ["SC", "ST", "OBC", "general"], "states": ["KA"], "education_level": "12th_pass"},
            "benefits": [("scholarship", "Annual scholarship for degree students", 10000, "annual")],
            "documents": ["PUC Marksheet", "Income Certificate", "Admission Letter", "Karnataka Domicile"],
        },
        {
            "name": "Karnataka Devaraj Urs Backward Classes Scholarship",
            "description": "Pre-matric and post-matric scholarship for students from backward classes pursuing education from Class 1 to Post Graduation in Karnataka.",
            "eligibility_text": "Backward class students of Karnataka. Family income below Rs 1 lakh for pre-matric, Rs 2 lakh for post-matric.",
            "state_code": "KA",
            "provider": "Government of Karnataka",
            "category": "Scholarship",
            "source": "bcwd.karnataka.gov.in",
            "link": "https://bcwd.karnataka.gov.in",
            "tags": ["backward", "classes", "scholarship", "karnataka"],
            "confidence_score": 0.87,
            "eligibility": {"min_age": 6, "max_age": 30, "max_income": 200000, "gender": ["male", "female"], "caste": ["OBC"], "states": ["KA"], "education_level": None},
            "benefits": [
                ("pre_matric", "Pre-matric scholarship amount", 3000, "annual"),
                ("post_matric", "Post-matric scholarship amount", 10000, "annual"),
            ],
            "documents": ["Backward Class Certificate", "Income Certificate", "School Certificate", "Karnataka Domicile"],
        },
        {
            "name": "Karnataka Arogya Sanjeevini Health Insurance",
            "description": "State health insurance providing cashless treatment up to Rs 5 lakh per family per year for BPL and APL families across empaneled hospitals.",
            "eligibility_text": "All families in Karnataka with annual income below Rs 5 lakh. BPL card holders automatically eligible.",
            "state_code": "KA",
            "provider": "Government of Karnataka",
            "category": "Welfare Scheme",
            "source": "arogya.karnataka.gov.in",
            "link": "https://arogya.karnataka.gov.in",
            "tags": ["health", "insurance", "bpl", "karnataka", "cashless"],
            "confidence_score": 0.89,
            "eligibility": {"min_age": 0, "max_age": 100, "max_income": 500000, "gender": ["male", "female", "transgender"], "caste": ["SC", "ST", "OBC", "general"], "states": ["KA"], "education_level": None},
            "benefits": [("insurance", "Annual health insurance coverage", 500000, "annual")],
            "documents": ["Ration Card", "Aadhaar Card", "Income Certificate"],
        },
        {
            "name": "Karnataka Udyogini Scheme for Women Entrepreneurs",
            "description": "Subsidized loans for women entrepreneurs from weaker sections to start or expand micro and small enterprises. Loans up to Rs 3 lakh with interest subsidy.",
            "eligibility_text": "Women aged 18-45 domiciled in Karnataka. Family income below Rs 1.5 lakh for general, Rs 2 lakh for SC/ST.",
            "state_code": "KA",
            "provider": "Government of Karnataka",
            "category": "Loan",
            "source": "kswdc.karnataka.gov.in",
            "link": "https://kswdc.karnataka.gov.in",
            "tags": ["women", "entrepreneur", "loan", "karnataka"],
            "confidence_score": 0.87,
            "eligibility": {"min_age": 18, "max_age": 45, "max_income": 200000, "gender": ["female"], "caste": ["SC", "ST", "OBC", "general"], "states": ["KA"], "education_level": None},
            "benefits": [("loan", "Subsidized business loan", 300000, "one_time")],
            "documents": ["Business Plan", "Income Certificate", "Karnataka Domicile", "Bank Account"],
        },
        {
            "name": "Karnataka Krishi Yantra Dhare - Farm Equipment Subsidy",
            "description": "Subsidy on agricultural equipment and machinery for Karnataka farmers. Up to 50% subsidy for small and marginal farmers for tractors, tillers, and harvesting equipment.",
            "eligibility_text": "Farmers with landholding in Karnataka. Priority to small and marginal farmers with less than 5 acres.",
            "state_code": "KA",
            "provider": "Government of Karnataka",
            "category": "Subsidy",
            "source": "raitamitra.karnataka.gov.in",
            "link": "https://raitamitra.karnataka.gov.in",
            "tags": ["farmer", "equipment", "subsidy", "karnataka", "agriculture"],
            "confidence_score": 0.86,
            "eligibility": {"min_age": 18, "max_age": 70, "max_income": None, "gender": ["male", "female"], "caste": ["SC", "ST", "OBC", "general"], "states": ["KA"], "education_level": None},
            "benefits": [("subsidy", "Equipment purchase subsidy up to 50%", 100000, "one_time")],
            "documents": ["Land Records", "Farmer ID", "Bank Account", "Quotation from Dealer"],
        },
        {
            "name": "Karnataka Ambedkar Overseas Scholarship",
            "description": "Scholarship for SC/ST students to pursue masters and PhD in top 500 QS-ranked universities abroad. Covers tuition, travel, and living expenses.",
            "eligibility_text": "SC/ST students domiciled in Karnataka for 10+ years. Admission in top 500 QS university. Family income below Rs 6 lakh.",
            "state_code": "KA",
            "provider": "Government of Karnataka",
            "category": "Scholarship",
            "source": "sw.karnataka.gov.in",
            "link": "https://sw.karnataka.gov.in",
            "tags": ["sc", "st", "overseas", "scholarship", "karnataka", "abroad"],
            "confidence_score": 0.88,
            "eligibility": {"min_age": 20, "max_age": 35, "max_income": 600000, "gender": ["male", "female"], "caste": ["SC", "ST"], "states": ["KA"], "education_level": "graduate"},
            "benefits": [
                ("tuition", "Tuition fee coverage", 2000000, "annual"),
                ("living", "Living expenses allowance", 100000, "annual"),
                ("travel", "Air travel reimbursement", 150000, "one_time"),
            ],
            "documents": ["Caste Certificate", "Income Certificate", "University Admission", "Passport", "Karnataka Domicile"],
        },
        {
            "name": "PRAGATI Scholarship for Girls in Technical Education",
            "description": "Scholarship for girl students admitted in first year of degree/diploma courses in AICTE-approved institutions. Part of the One Student-One Laptop scheme.",
            "eligibility_text": "Girl students in AICTE-approved technical institutions. Family income below Rs 8 lakh per annum.",
            "state_code": None,
            "provider": "Ministry of Education",
            "category": "Scholarship",
            "source": "aicte-india.org",
            "link": "https://www.aicte-india.org/schemes/students-development-schemes",
            "tags": ["girls", "technical", "engineering", "scholarship", "aicte"],
            "confidence_score": 0.91,
            "eligibility": {"min_age": 17, "max_age": 25, "max_income": 800000, "gender": ["female"], "caste": ["SC", "ST", "OBC", "general"], "states": None, "education_level": "12th_pass"},
            "benefits": [("scholarship", "Annual scholarship amount", 50000, "annual")],
            "documents": ["AICTE Admission Letter", "Income Certificate", "Marksheet", "Bank Account"],
        },
        {
            "name": "Swanath Scholarship for Orphan Students",
            "description": "Scholarship for orphan students and wards of armed forces/central paramilitary personnel martyred in action. Supports technical education at diploma and degree level.",
            "eligibility_text": "Orphan students or wards of martyred personnel. Admitted in AICTE institutions. Family income below Rs 8 lakh.",
            "state_code": None,
            "provider": "Ministry of Education",
            "category": "Scholarship",
            "source": "aicte-india.org",
            "link": "https://www.aicte-india.org/schemes/students-development-schemes",
            "tags": ["orphan", "technical", "scholarship", "armed-forces"],
            "confidence_score": 0.90,
            "eligibility": {"min_age": 17, "max_age": 30, "max_income": 800000, "gender": ["male", "female"], "caste": ["SC", "ST", "OBC", "general"], "states": None, "education_level": "12th_pass"},
            "benefits": [("scholarship", "Annual scholarship for technical education", 50000, "annual")],
            "documents": ["Orphan Certificate / Martyrdom Certificate", "AICTE Admission Letter", "Income Certificate"],
        },
        {
            "name": "Karnataka Anna Bhagya - Subsidized Rice Scheme",
            "description": "Subsidized rice at Rs 1/kg for BPL families through public distribution system. Each family receives up to 30 kg of rice per month.",
            "eligibility_text": "BPL families with Antyodaya or Priority household ration cards. Must be registered at local fair price shop.",
            "state_code": "KA",
            "provider": "Government of Karnataka",
            "category": "Subsidy",
            "source": "ahara.karnataka.gov.in",
            "link": "https://ahara.karnataka.gov.in",
            "tags": ["food", "rice", "bpl", "subsidy", "karnataka"],
            "confidence_score": 0.87,
            "eligibility": {"min_age": 0, "max_age": 100, "max_income": 120000, "gender": ["male", "female", "transgender"], "caste": ["SC", "ST", "OBC", "general"], "states": ["KA"], "education_level": None},
            "benefits": [("subsidy", "Subsidized rice at Rs 1/kg, up to 30 kg/month", 360, "monthly")],
            "documents": ["BPL Ration Card", "Aadhaar Card"],
        },
        {
            "name": "Karnataka PhD Fellowship for SC/ST Researchers",
            "description": "Fellowship for SC/ST scholars pursuing PhD in Karnataka universities. Monthly stipend and annual contingency grant for up to 5 years.",
            "eligibility_text": "SC/ST scholars enrolled in PhD in Karnataka state universities. Must have cleared NET/KSET. Family income below Rs 3 lakh.",
            "state_code": "KA",
            "provider": "Government of Karnataka",
            "category": "Fellowship",
            "source": "dhe.karnataka.gov.in",
            "link": "https://dhe.karnataka.gov.in",
            "tags": ["phd", "fellowship", "sc", "st", "research", "karnataka"],
            "confidence_score": 0.86,
            "eligibility": {"min_age": 22, "max_age": 40, "max_income": 300000, "gender": ["male", "female"], "caste": ["SC", "ST"], "states": ["KA"], "education_level": "post_graduate"},
            "benefits": [
                ("stipend", "Monthly research stipend", 25000, "monthly"),
                ("contingency", "Annual contingency grant", 15000, "annual"),
            ],
            "documents": ["Caste Certificate", "NET/KSET Score", "PhD Admission Letter", "Income Certificate"],
        },
        {
            "name": "Karnataka Skill Development - PMKVY State Component",
            "description": "Free skill training programs aligned with PMKVY covering IT, healthcare, construction, retail, and manufacturing sectors.",
            "eligibility_text": "Youth aged 18-35, residents of Karnataka. Minimum 10th pass for most courses.",
            "state_code": "KA",
            "provider": "Government of Karnataka",
            "category": "Skill Program",
            "source": "kaushalya.karnataka.gov.in",
            "link": "https://kaushalya.karnataka.gov.in",
            "tags": ["skill", "training", "youth", "karnataka", "pmkvy"],
            "confidence_score": 0.85,
            "eligibility": {"min_age": 18, "max_age": 35, "max_income": None, "gender": ["male", "female"], "caste": ["SC", "ST", "OBC", "general"], "states": ["KA"], "education_level": "10th_pass"},
            "benefits": [
                ("training", "Free skill training with certification", None, "one_time"),
                ("placement", "Placement assistance after training", None, "one_time"),
            ],
            "documents": ["Aadhaar Card", "Education Certificate", "Karnataka Residence Proof"],
        },
        {
            "name": "Post-Matric Scholarship for OBC Students",
            "description": "Central scholarship for Other Backward Classes students pursuing post-matriculation courses. Covers maintenance allowance and academic fees.",
            "eligibility_text": "OBC students with family income below Rs 1.5 lakh per annum. Must be enrolled in post-matric courses in recognized institutions.",
            "state_code": None,
            "provider": "Ministry of Social Justice and Empowerment",
            "category": "Scholarship",
            "source": "scholarships.gov.in",
            "link": "https://scholarships.gov.in",
            "tags": ["obc", "post-matric", "scholarship", "national"],
            "confidence_score": 0.94,
            "eligibility": {"min_age": 15, "max_age": 35, "max_income": 150000, "gender": ["male", "female", "transgender"], "caste": ["OBC"], "states": None, "education_level": "10th_pass"},
            "benefits": [
                ("maintenance", "Monthly maintenance allowance", 750, "monthly"),
                ("academic_fee", "Academic fee reimbursement", 15000, "annual"),
            ],
            "documents": ["OBC Certificate", "Income Certificate", "Marksheet", "Bank Account"],
        },
        {
            "name": "Karnataka CM Housing Scheme for EWS",
            "description": "Affordable housing for economically weaker sections with subsidy up to Rs 2.5 lakh for construction or purchase of dwelling units.",
            "eligibility_text": "EWS families in Karnataka with annual income below Rs 3 lakh. Must not own a pucca house. Priority for SC/ST and women-headed households.",
            "state_code": "KA",
            "provider": "Government of Karnataka",
            "category": "Welfare Scheme",
            "source": "housing.karnataka.gov.in",
            "link": "https://housing.karnataka.gov.in",
            "tags": ["housing", "ews", "karnataka", "subsidy"],
            "confidence_score": 0.85,
            "eligibility": {"min_age": 21, "max_age": 65, "max_income": 300000, "gender": ["male", "female"], "caste": ["SC", "ST", "OBC", "general"], "states": ["KA"], "education_level": None},
            "benefits": [("subsidy", "Housing construction subsidy", 250000, "one_time")],
            "documents": ["Income Certificate", "Land Document", "No-House Certificate", "Karnataka Domicile"],
        },
        {
            "name": "Karnataka Mathrushree Maternity Benefit",
            "description": "Cash incentive of Rs 6,000 for pregnant women from BPL families for institutional delivery. Paid in installments during pregnancy and after delivery.",
            "eligibility_text": "Pregnant women from BPL families in Karnataka. Must register at government health facility. First two live births only.",
            "state_code": "KA",
            "provider": "Government of Karnataka",
            "category": "Welfare Scheme",
            "source": "arogya.karnataka.gov.in",
            "link": "https://arogya.karnataka.gov.in",
            "tags": ["maternity", "women", "health", "bpl", "karnataka"],
            "confidence_score": 0.86,
            "eligibility": {"min_age": 18, "max_age": 45, "max_income": 120000, "gender": ["female"], "caste": ["SC", "ST", "OBC", "general"], "states": ["KA"], "education_level": None},
            "benefits": [("cash", "Maternity benefit in installments", 6000, "one_time")],
            "documents": ["BPL Card", "Hospital Registration", "Aadhaar Card"],
        },
    ]

    cur = conn.cursor()
    for s in schemes:
        sid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"scheme:{s['name']}"))
        pid = provider_ids.get(s["provider"])
        cid = category_ids.get(s["category"])

        cur.execute("""
            INSERT INTO schemes (id, provider_id, category_id, name, description,
                eligibility_text, state_code, status, source, source_type, link,
                tags, confidence_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (
            sid, pid, cid, s["name"], s["description"],
            s["eligibility_text"], s["state_code"], "ACTIVE", s["source"],
            "portal", s["link"], s["tags"], s["confidence_score"],
        ))

        elig = s["eligibility"]
        eid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"elig:{s['name']}"))
        cur.execute("""
            INSERT INTO eligibility_rules (id, scheme_id, min_age, max_age, max_income,
                gender, caste, states, education_level)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (
            eid, sid, elig["min_age"], elig["max_age"], elig["max_income"],
            elig["gender"], elig["caste"], elig["states"], elig["education_level"],
        ))

        for i, (btype, bdesc, amount, freq) in enumerate(s["benefits"]):
            bid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"benefit:{s['name']}:{i}"))
            cur.execute("""
                INSERT INTO benefits (id, scheme_id, benefit_type, description, amount, frequency)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (bid, sid, btype, bdesc, amount, freq))

        for i, doc_name in enumerate(s["documents"]):
            did = str(uuid.uuid5(uuid.NAMESPACE_URL, f"doc:{s['name']}:{i}"))
            cur.execute("""
                INSERT INTO documents_required (id, scheme_id, document_name, is_mandatory)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (did, sid, doc_name, True))

        print(f"  📜 Scheme: {s['name']}")

    conn.commit()
    cur.close()
    print(f"\n✅ Seeded {len(schemes)} schemes with eligibility rules, benefits, and documents")


def print_summary(conn):
    cur = conn.cursor()
    tables = ["providers", "categories", "schemes", "eligibility_rules", "benefits", "documents_required"]
    print("\n📊 Database Summary:")
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"  {table}: {count} rows")
    cur.close()


if __name__ == "__main__":
    print("🚀 Seeding database...\n")
    conn = get_conn()
    try:
        run_schema(conn)
        provider_ids = seed_providers(conn)
        category_ids = seed_categories(conn)
        seed_schemes(conn, provider_ids, category_ids)
        print_summary(conn)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
    print("\n🏁 Done!")
