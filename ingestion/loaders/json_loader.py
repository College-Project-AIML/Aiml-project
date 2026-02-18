"""
JSON Loader
-------------
Purpose:
- Save normalized scheme records to JSON files
- Load scheme records back from JSON files
- Create output directories automatically
- Pretty-print JSON for human readability and version control diffs
- Act as a file-based persistence layer for pipeline outputs

This enables offline inspection, debugging, and backup of pipeline results.
"""

import json
import os
from datetime import datetime
from typing import List, Dict


class JsonLoader:

    def __init__(self):
        self.stats = {"saved": 0, "loaded": 0}

    def save(self, records: List[Dict], output_path: str):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        envelope = {
            "metadata": {
                "total_records": len(records),
                "exported_at": datetime.utcnow().isoformat(),
                "format_version": "1.0",
            },
            "records": records,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2, ensure_ascii=False, default=str)

        self.stats["saved"] = len(records)
        print(f"[JsonLoader] Saved {len(records)} records to {output_path}")

    def load(self, input_path: str) -> List[Dict]:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict) and "records" in data:
            records = data["records"]
        elif isinstance(data, list):
            records = data
        else:
            records = []

        self.stats["loaded"] = len(records)
        print(f"[JsonLoader] Loaded {len(records)} records from {input_path}")
        return records
