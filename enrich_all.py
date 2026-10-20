#!/usr/bin/env python3
"""
Enrich all MyScheme records with eligibility, benefits, documents.
Processes in small chunks with aggressive retry for API reliability.
"""

import os
import sys
import time

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, '/Users/avaneesh/Aiml-project')

from ingestion.sources.myscheme.client import MySchemeClient
from ingestion.sources.myscheme.parser import parse_schemes
from ingestion.normalizers.scheme_normalizer import SchemeNormalizer
from ingestion.validators.scheme_validator import SchemeValidator
from ingestion.dedup.dedup_engine import DedupEngine
from ingestion.enrichment.myscheme_detail import enrich_schemes
from ingestion.loaders.postgres_loader import PostgresLoader

import psycopg2
from dotenv import load_dotenv
load_dotenv()

# Get DB URL
url = os.getenv('DATABASE_URL')
if '@postgres:5432/' in url:
    import socket
    try:
        socket.gethostbyname('postgres')
    except socket.gaierror:
        url = url.replace('@postgres:5432/', '@localhost:5433/')

# Reset non-enriched records
conn = psycopg2.connect(url)
cur = conn.cursor()
cur.execute("DELETE FROM schemes WHERE source LIKE '%myscheme%' AND id NOT IN (SELECT scheme_id FROM eligibility_rules)")
conn.commit()
cur.close()
conn.close()
print('Cleared non-enriched records')

# Fetch and parse
client = MySchemeClient()
raw_records, _ = client.fetch_schemes()
parsed = parse_schemes(raw_records)

normalizer = SchemeNormalizer()
validator = SchemeValidator()
dedup = DedupEngine()

normalized = []
for r in parsed:
    rec = normalizer.normalize(r)
    normalized.append(validator.validate(rec))

records = dedup.deduplicate(normalized)
total = len(records)
print(f'Total to enrich: {total}')

# Process in chunks of 2 with aggressive retry
for i in range(0, len(records), 100):
    chunk = records[i:i+100]
    chunk_num = i//100 + 1
    total_chunks = (len(records) + 99)//100
    print(f'Chunk {chunk_num}/{total_chunks} ({i+1}-{min(i+2, len(records))}/{len(records)})...')
    
    for retry in range(5):
        try:
            enriched = enrich_schemes(chunk, rate_limit=0.02)
            loader = PostgresLoader()
            loader.load(enriched)
            loader.close()
            print(f'  Chunk {i//2 + 1} done')
            break
        except Exception as e:
            if retry == 4:
                print(f'  FAILED after 5 retries: {e}')
            else:
                print(f'  Retry {retry+1}/5: {str(e)[:80]}')
                time.sleep(5)

print('ALL DONE!')