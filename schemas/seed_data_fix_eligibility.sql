-- ============================================================
-- Fix: eligibility_rules inserts, using scheme name lookup
-- (safe to run even if some rows already exist from the first attempt)
-- ============================================================

INSERT INTO eligibility_rules (scheme_id, gender, states, education_level)
SELECT id, ARRAY['FEMALE'], ARRAY['KA'], 'UNDERGRADUATE'
FROM schemes WHERE name = 'Sanchi Honnamma Scholarship'
AND NOT EXISTS (SELECT 1 FROM eligibility_rules WHERE scheme_id = schemes.id);

INSERT INTO eligibility_rules (scheme_id, states, education_level)
SELECT id, ARRAY['KA'], 'UNDERGRADUATE'
FROM schemes WHERE name = 'Sir C.V. Raman Scholarship (Scholarship to Encourage Bright Students to Study Science at Degree Level)'
AND NOT EXISTS (SELECT 1 FROM eligibility_rules WHERE scheme_id = schemes.id);

INSERT INTO eligibility_rules (scheme_id, gender, states, education_level)
SELECT id, ARRAY['FEMALE'], ARRAY['KA'], 'PRE_UNIVERSITY'
FROM schemes WHERE name = 'Kittur Rani Chennamma Puraskar Scholarship'
AND NOT EXISTS (SELECT 1 FROM eligibility_rules WHERE scheme_id = schemes.id);

INSERT INTO eligibility_rules (scheme_id, states, education_level)
SELECT id, ARRAY['KA'], 'HIGHER_EDUCATION'
FROM schemes WHERE name = 'Scholarship & Free Education for Students Affected by HIV/Leprosy'
AND NOT EXISTS (SELECT 1 FROM eligibility_rules WHERE scheme_id = schemes.id);

INSERT INTO eligibility_rules (scheme_id, max_income, states, education_level)
SELECT id, 250000.00, ARRAY['KA'], 'HIGHER_EDUCATION'
FROM schemes WHERE name = 'Rajiv Gandhi Loan Scholarship'
AND NOT EXISTS (SELECT 1 FROM eligibility_rules WHERE scheme_id = schemes.id);
