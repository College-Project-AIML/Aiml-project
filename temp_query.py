import os, json
from services.api.db import init_pool, close_pool, get_db
init_pool()
try:
    with get_db() as cur:
        cur.execute("SELECT id, name, description, eligibility_text, link, source FROM schemes WHERE name ILIKE '%Coir%'")
        row = cur.fetchone()
        if row:
            res = {
                'id': str(row['id']),
                'name': row['name'],
                'desc': row['description'],
                'elig': row['eligibility_text'],
                'link': row['link'],
                'source': row['source']
            }
            with open('temp_result.json', 'w') as f:
                json.dump(res, f, indent=2)
finally:
    close_pool()
