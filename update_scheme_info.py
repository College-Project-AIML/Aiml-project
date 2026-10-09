import os
import uuid
from services.api.db import init_pool, close_pool, get_db

SCHEME_ID = "5d74e854-6d35-06af-ffb2-e7f420d42fcf"

def update_scheme():
    init_pool()
    try:
        with get_db() as cur:
            # 1. Update eligibility_text in schemes table
            elig_text = "Candidates must be between 18 and 35 years of age. Must be a native of the Union Territory or continuous resident for at least 3 years."
            cur.execute("""
                UPDATE schemes 
                SET eligibility_text = %s 
                WHERE id = %s
            """, (elig_text, SCHEME_ID))
            
            # 2. Insert or update eligibility rules
            # We first check if a rule exists for this scheme
            cur.execute("SELECT id FROM eligibility_rules WHERE scheme_id = %s", (SCHEME_ID,))
            rule_row = cur.fetchone()
            
            if rule_row:
                cur.execute("""
                    UPDATE eligibility_rules
                    SET min_age = 18, max_age = 35, states = ARRAY['PY']::varchar[],
                        education_level = '10th_pass'
                    WHERE scheme_id = %s
                """, (SCHEME_ID,))
            else:
                rule_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO eligibility_rules (id, scheme_id, min_age, max_age, states, education_level)
                    VALUES (%s, %s, 18, 35, ARRAY['PY']::varchar[], '10th_pass')
                """, (rule_id, SCHEME_ID))

            # 3. Add Benefits
            cur.execute("DELETE FROM benefits WHERE scheme_id = %s", (SCHEME_ID,))
            
            b1_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO benefits (id, scheme_id, benefit_type, description, amount, frequency)
                VALUES (%s, %s, 'stipend', 'Monthly stipend during the 6-month training period', 3000, 'monthly')
            """, (b1_id, SCHEME_ID))
            
            b2_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO benefits (id, scheme_id, benefit_type, description, amount, frequency)
                VALUES (%s, %s, 'training', 'Free high-skill technical training in Coir', NULL, 'one_time')
            """, (b2_id, SCHEME_ID))

            # 4. Add Documents
            cur.execute("DELETE FROM documents_required WHERE scheme_id = %s", (SCHEME_ID,))
            
            docs = [
                "Aadhaar Card",
                "Residence Certificate",
                "Educational Certificate (10th/ITI)"
            ]
            for doc in docs:
                d_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO documents_required (id, scheme_id, document_name, is_mandatory)
                    VALUES (%s, %s, %s, TRUE)
                """, (d_id, SCHEME_ID, doc))
            
            cur.connection.commit()
            print("Successfully updated scheme with actual fetched information.")
    finally:
        close_pool()

if __name__ == "__main__":
    update_scheme()
