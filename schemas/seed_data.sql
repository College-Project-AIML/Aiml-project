-- ============================================================
-- Seed Data — Karnataka Scholarships (Dept. of Collegiate Education)
-- Source: Official DCE Karnataka PDF, "Updated Scholarship Information"
-- Manually curated per project's documented data strategy.
-- ============================================================

-- 1. Provider
INSERT INTO providers (name, type, website)
VALUES (
    'Department of Collegiate Education, Government of Karnataka',
    'STATE_GOVERNMENT',
    'https://dce.karnataka.gov.in'
)
ON CONFLICT DO NOTHING;

-- 2. Category
INSERT INTO categories (name, slug, description)
VALUES (
    'Scholarships & Fee Reimbursement',
    'scholarships-fee-reimbursement',
    'Government scholarship and fee reimbursement schemes for students in Karnataka.'
)
ON CONFLICT (name) DO NOTHING;

-- 3. Schemes + related rows
-- Using CTEs to fetch provider_id and category_id once

WITH p AS (
    SELECT id AS provider_id FROM providers
    WHERE name = 'Department of Collegiate Education, Government of Karnataka'
),
c AS (
    SELECT id AS category_id FROM categories
    WHERE slug = 'scholarships-fee-reimbursement'
),

-- Scheme 1: Sanchi Honnamma Scholarship
s1 AS (
    INSERT INTO schemes (provider_id, category_id, name, description, eligibility_text, state_code, status, source, source_type, link, tags)
    SELECT provider_id, category_id,
        'Sanchi Honnamma Scholarship',
        'A scholarship to encourage girl students in higher education, introduced in 2002-03. Awarded to meritorious girl students in Government and Aided First Grade Colleges (Arts, Commerce & Science).',
        'Girl students studying in Government & Private Aided First Grade Colleges. Must pass semester exams in first attempt for renewal. Urban General category students need 50% marks; Rural, SC & ST category students need 45% marks in the previous exam. Limited to girls who studied in Government Schools from 1st to 7th Standard.',
        'KA', 'ACTIVE',
        'dce.karnataka.gov.in (Official PDF: Updated Scholarship Information)',
        'manual_curated',
        'https://dce.karnataka.gov.in/info-2/Student+Scholarships/en',
        ARRAY['scholarship', 'girl-students', 'undergraduate', 'karnataka']
    FROM p, c
    RETURNING id
),

-- Scheme 2: Sir C.V. Raman Scholarship
s2 AS (
    INSERT INTO schemes (provider_id, category_id, name, description, eligibility_text, state_code, status, source, source_type, link, tags)
    SELECT provider_id, category_id,
        'Sir C.V. Raman Scholarship (Scholarship to Encourage Bright Students to Study Science at Degree Level)',
        'Introduced in 2001-02 to encourage meritorious science students at the degree level (B.Sc).',
        'I year B.Sc. students studying at least two of Physics, Chemistry, Mathematics, Geology, Botany, or Zoology. General category students need 65% marks; SC & ST students need 60% marks in previous exam. Must maintain 60% marks each semester to continue receiving the scholarship.',
        'KA', 'ACTIVE',
        'dce.karnataka.gov.in (Official PDF: Updated Scholarship Information)',
        'manual_curated',
        'https://dce.karnataka.gov.in/info-2/Student+Scholarships/en',
        ARRAY['scholarship', 'science', 'bsc', 'undergraduate', 'karnataka']
    FROM p, c
    RETURNING id
),

-- Scheme 3: Kittur Rani Chennamma Puraskar Scholarship
s3 AS (
    INSERT INTO schemes (provider_id, category_id, name, description, eligibility_text, state_code, status, source, source_type, link, tags)
    SELECT provider_id, category_id,
        'Kittur Rani Chennamma Puraskar Scholarship',
        'Introduced in 2006-07 to provide financial assistance to girl students from Below Poverty Line (BPL) families to pursue professional courses.',
        'Limited to 10 girl students per district of Karnataka who hold a BPL card and scored 80%+ marks in PUC (II PU) at Government & Aided Pre-University Colleges. Selection verified by District and State level committees.',
        'KA', 'ACTIVE',
        'dce.karnataka.gov.in (Official PDF: Updated Scholarship Information)',
        'manual_curated',
        'https://dce.karnataka.gov.in/info-2/Student+Scholarships/en',
        ARRAY['scholarship', 'girl-students', 'bpl', 'professional-courses', 'karnataka']
    FROM p, c
    RETURNING id
),

-- Scheme 4: HIV/Leprosy Scholarship
s4 AS (
    INSERT INTO schemes (provider_id, category_id, name, description, eligibility_text, state_code, status, source, source_type, link, tags)
    SELECT provider_id, category_id,
        'Scholarship & Free Education for Students Affected by HIV/Leprosy',
        'Introduced in 2013 to support students in higher education who are affected by HIV/AIDS or Leprosy, or whose parents are affected (living or deceased).',
        'Student or parent affected by HIV/Leprosy; family must have resided in Karnataka for 25+ years; studying in Government/Government Aided colleges; enrolled in Certificate/Diploma/Degree/PG programmes (PhD students not eligible as they receive fellowships separately).',
        'KA', 'ACTIVE',
        'dce.karnataka.gov.in (Official PDF: Updated Scholarship Information)',
        'manual_curated',
        'https://dce.karnataka.gov.in/info-2/Student+Scholarships/en',
        ARRAY['scholarship', 'health', 'hiv-leprosy', 'karnataka']
    FROM p, c
    RETURNING id
),

-- Scheme 5: Rajiv Gandhi Loan Scholarship
s5 AS (
    INSERT INTO schemes (provider_id, category_id, name, description, eligibility_text, state_code, status, source, source_type, link, tags)
    SELECT provider_id, category_id,
        'Rajiv Gandhi Loan Scholarship',
        'Introduced in 2013 to enhance Gross Enrolment Ratio in higher education by providing interest-subsidized education loans to economically backward students, in partnership with scheduled banks (Nodal Bank: Vijaya Bank).',
        'Indian national; secured 50%+ in PUC/10+2; admitted to a higher education course in a Government or Aided college in Karnataka; family annual income not exceeding Rs. 2.5 lakh.',
        'KA', 'ACTIVE',
        'dce.karnataka.gov.in (Official PDF: Updated Scholarship Information)',
        'manual_curated',
        'https://dce.karnataka.gov.in/info-2/Student+Scholarships/en',
        ARRAY['scholarship', 'loan', 'economically-weaker', 'karnataka']
    FROM p, c
    RETURNING id
),

-- Scheme 6: Language Scholarship
s6 AS (
    INSERT INTO schemes (provider_id, category_id, name, description, eligibility_text, state_code, status, source, source_type, link, tags)
    SELECT provider_id, category_id,
        'Language Scholarship (Kannada/Sanskrit/English at Degree Level)',
        'Instituted since September 1967 to encourage study of Kannada, English, or Sanskrit as a major subject at the degree level.',
        'Must have scored 50%+ in the relevant language subject in PUC/XII Standard; awarded to top scorers (10 for Kannada, 10 for English, 9 for Sanskrit); must pass previous exam in first attempt.',
        'KA', 'ACTIVE',
        'dce.karnataka.gov.in (Official PDF: Updated Scholarship Information)',
        'manual_curated',
        'https://dce.karnataka.gov.in/info-2/Student+Scholarships/en',
        ARRAY['scholarship', 'language', 'kannada', 'sanskrit', 'english', 'karnataka']
    FROM p, c
    RETURNING id
),

-- Scheme 7: Jawaharlal Nehru Scholarship (JNU)
s7 AS (
    INSERT INTO schemes (provider_id, category_id, name, description, eligibility_text, state_code, status, source, source_type, link, tags)
    SELECT provider_id, category_id,
        'Jawaharlal Nehru Scholarship (JNU M.Phil/PhD)',
        'Instituted in 1965 for Karnataka students pursuing M.Phil or PhD at Jawaharlal Nehru University, New Delhi. Limited to 2 beneficiaries per year.',
        'Admission to 1st year PG/M.Phil/PhD programme at JNU; Karnataka domicile.',
        'KA', 'ACTIVE',
        'dce.karnataka.gov.in (Official PDF: Updated Scholarship Information)',
        'manual_curated',
        'https://dce.karnataka.gov.in/info-2/Student+Scholarships/en',
        ARRAY['scholarship', 'postgraduate', 'phd', 'mphil', 'jnu', 'karnataka']
    FROM p, c
    RETURNING id
),

-- Scheme 8: Anglo Indian Scholarship
s8 AS (
    INSERT INTO schemes (provider_id, category_id, name, description, eligibility_text, state_code, status, source, source_type, link, tags)
    SELECT provider_id, category_id,
        'Anglo Indian Scholarship (Fee Reimbursement)',
        'Introduced 25th August 1995. Fee reimbursement for Anglo-Indian students studying in colleges under the Department of Collegiate Education, Government of Karnataka.',
        'Anglo-Indian community students studying in recognized colleges under DCE Karnataka.',
        'KA', 'ACTIVE',
        'dce.karnataka.gov.in (Official PDF: Updated Scholarship Information)',
        'manual_curated',
        'https://dce.karnataka.gov.in/info-2/Student+Scholarships/en',
        ARRAY['scholarship', 'fee-reimbursement', 'anglo-indian', 'karnataka']
    FROM p, c
    RETURNING id
),

-- Scheme 9: Children of Defence Personnel & SC/ST Students Scholarship
s9 AS (
    INSERT INTO schemes (provider_id, category_id, name, description, eligibility_text, state_code, status, source, source_type, link, tags)
    SELECT provider_id, category_id,
        'Children of Defence Personnel & SC/ST Students Scholarship',
        'Fee reimbursement scheme for children of defence personnel and SC/ST students studying in colleges under the Department of Collegiate Education, Government of Karnataka.',
        'Children of Defence Personnel, or SC/ST students, studying in recognized colleges under DCE Karnataka.',
        'KA', 'ACTIVE',
        'dce.karnataka.gov.in (Official PDF: Updated Scholarship Information)',
        'manual_curated',
        'https://dce.karnataka.gov.in/info-2/Student+Scholarships/en',
        ARRAY['scholarship', 'fee-reimbursement', 'defence', 'sc-st', 'karnataka']
    FROM p, c
    RETURNING id
)

-- 4. Benefits (one representative row per scheme)
INSERT INTO benefits (scheme_id, benefit_type, description, amount, frequency)
SELECT id, 'CASH_AWARD', 'Annual scholarship amount', 2000.00, 'ANNUAL' FROM s1
UNION ALL
SELECT id, 'CASH_AWARD', 'Annual scholarship amount', 5000.00, 'ANNUAL' FROM s2
UNION ALL
SELECT id, 'FEE_REIMBURSEMENT', 'CET cell fee reimbursement', NULL, 'ONE_TIME' FROM s3
UNION ALL
SELECT id, 'LIVELIHOOD_ALLOWANCE', 'Monthly livelihood allowance', 1500.00, 'MONTHLY' FROM s4
UNION ALL
SELECT id, 'ADDITIONAL_GRANT', 'Fee/clothes/books/learning material grant', 3000.00, 'ANNUAL' FROM s4
UNION ALL
SELECT id, 'LOAN', 'Education loan (3-year degree course)', 180000.00, 'TOTAL_COURSE' FROM s5
UNION ALL
SELECT id, 'CASH_AWARD', 'Monthly award up to annual cap', 500.00, 'ANNUAL' FROM s6
UNION ALL
SELECT id, 'CASH_AWARD', 'Monthly scholarship for M.Phil (10 months)', 5000.00, 'MONTHLY' FROM s7
UNION ALL
SELECT id, 'FEE_REIMBURSEMENT', 'College fee reimbursement', NULL, 'ANNUAL' FROM s8
UNION ALL
SELECT id, 'FEE_REIMBURSEMENT', 'College fee reimbursement', NULL, 'ANNUAL' FROM s9;

-- 5. Eligibility rules (structured, where clearly quantifiable)
INSERT INTO eligibility_rules (scheme_id, gender, states, education_level)
SELECT id, ARRAY['FEMALE'], ARRAY['KA'], 'UNDERGRADUATE' FROM s1;

INSERT INTO eligibility_rules (scheme_id, states, education_level)
SELECT id, ARRAY['KA'], 'UNDERGRADUATE' FROM s2;

INSERT INTO eligibility_rules (scheme_id, gender, states, education_level)
SELECT id, ARRAY['FEMALE'], ARRAY['KA'], 'PRE_UNIVERSITY' FROM s3;

INSERT INTO eligibility_rules (scheme_id, states, education_level)
SELECT id, ARRAY['KA'], 'HIGHER_EDUCATION' FROM s4;

INSERT INTO eligibility_rules (scheme_id, max_income, states, education_level)
SELECT id, 250000.00, ARRAY['KA'], 'HIGHER_EDUCATION' FROM s5;
