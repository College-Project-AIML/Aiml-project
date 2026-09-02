"""
Validation script for the live-sync feature (docs/next.md validation plan).

Run:
    python scripts/test_live_sync.py

Covers:
    1. Fingerprint stability (timestamps excluded, deterministic)
    2. classify(): NEW / UNCHANGED / UPDATED
    3. diff_fields(): precise old → new diffs
    4. Two-run synthetic scenario (edited record → UPDATED with right diff)
    5. Connector parser smoke tests (myscheme + karnataka_ssp)
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.sync import change_detector as cd
from ingestion.sync.fingerprint import fingerprint_record
from ingestion.normalizers.scheme_normalizer import SchemeNormalizer

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name} {detail}")


def base_record():
    return {
        "scheme_name": "Vidyasiri Scholarship",
        "source": "dce.karnataka.gov.in",
        "category": "scholarship",
        "ministry": "Department of Collegiate Education, Karnataka",
        "description": "Financial assistance to SC/ST students.",
        "eligibility": "SC/ST students, income below 2.5 lakh.",
        "state": "karnataka",
        "link": "https://dce.karnataka.gov.in",
        "tags": ["sc", "st"],
    }


def test_fingerprint():
    print("\n[1] Fingerprint")
    n1 = SchemeNormalizer().normalize(base_record())
    n2 = SchemeNormalizer().normalize(base_record())
    fp1, fp2 = fingerprint_record(n1), fingerprint_record(n2)
    check("same record → same fingerprint", fp1 == fp2)
    check("fingerprint is sha256 hex", len(fp1) == 64)

    # Changing only a timestamp must NOT change the fingerprint.
    n3 = dict(n1, ingested_at="2099-01-01T00:00:00")
    check("timestamps excluded", fingerprint_record(n3) == fp1)

    # Changing semantic content must change the fingerprint.
    n4 = dict(n1, eligibility_text="SC/ST students, income below 5 lakh.")
    check("semantic change detected", fingerprint_record(n4) != fp1)


def test_classify():
    print("\n[2] classify()")
    fp = "abc123"
    check("no snapshot → NEW", cd.classify(fp, None) == cd.NEW)
    check("same fingerprint → UNCHANGED", cd.classify(fp, fp) == cd.UNCHANGED)
    check("different fingerprint → UPDATED", cd.classify(fp, "old") == cd.UPDATED)


def test_diff():
    print("\n[3] diff_fields()")
    old = {"name": "A", "tags": ["x"], "status": "ACTIVE"}
    new = {"name": "A", "tags": ["x", "y"], "status": "INACTIVE"}
    diff = cd.diff_fields(old, new)
    check("only changed fields reported", set(diff.keys()) == {"status"})
    check("old/new values captured", diff["status"] == ["ACTIVE", "INACTIVE"])
    # Auto-derived tags are excluded from diffs (see DIFF_FIELDS docstring).
    check("auto-derived tags excluded from diff", "tags" not in diff)


def test_two_run_scenario():
    print("\n[4] Two-run synthetic scenario")
    normalizer = SchemeNormalizer()

    run1 = normalizer.normalize(base_record())
    fp1 = fingerprint_record(run1)

    # Run 1 → NEW.
    change1 = cd.classify(fp1, None)
    check("run 1 classified as NEW", change1 == cd.NEW)

    # Run 2 with an edited eligibility → UPDATED with the right diff.
    edited = dict(base_record(), eligibility="SC/ST students, income below 5 lakh.")
    run2 = normalizer.normalize(edited)
    fp2 = fingerprint_record(run2)
    change2 = cd.classify(fp2, fp1)
    diff = cd.diff_fields(run1, run2)
    check("run 2 classified as UPDATED", change2 == cd.UPDATED)
    check(
        "diff names eligibility_text as changed",
        "eligibility_text" in diff,
    )

    # Run 3 unchanged → UNCHANGED.
    run3 = normalizer.normalize(edited)
    check("run 3 classified as UNCHANGED", cd.classify(fingerprint_record(run3), fp2) == cd.UNCHANGED)


def test_myscheme_parser():
    print("\n[5] MyScheme parser smoke test")
    from ingestion.sources.myscheme.parser import parse_schemes
    from services.api.scheme_links import is_direct_scheme_link

    # Real API shape: search hits carry the payload under `fields`.
    payload = [
        {
            "id": "abc123",
            "fields": {
                "schemeName": "Test Central Scheme",
                "nodalMinistryName": "Ministry of Education",
                "schemeCategory": ["Education & Learning"],
                "briefDescription": "Helps students.",
                "beneficiaryState": ["All"],
                "slug": "test-central-scheme",
                "tags": ["merit", "scholarship"],
                "level": "Central",
                "schemeCloseDate": "2026-12-31",
                "applicationUrl": "https://apply.gov.in/test-central-scheme",
            },
        },
        {
            "id": "def456",
            "fields": {
                "schemeName": "Karnataka State Loan Scheme",
                "schemeCategory": ["Business & Entrepreneurship"],
                "beneficiaryState": ["Karnataka"],
                "slug": "ka-state-loan",
                "level": "State",
            },
        },
    ]
    records = parse_schemes(payload)
    check("parsed two records", len(records) == 2)
    rec = records[0]
    check("scheme_name mapped", rec["scheme_name"] == "Test Central Scheme")
    check("slug → link", rec["link"] == "https://www.myscheme.gov.in/schemes/test-central-scheme")
    check("application URL mapped", rec["application_link"] == "https://apply.gov.in/test-central-scheme")
    check("beneficiaryState All → state india", rec["state"] == "india")
    check("category mapped Education → scholarship", rec["category"] == "scholarship")
    check("tags list kept", rec["tags"] == ["merit", "scholarship"])
    check("extras carried (deadline/level)", rec["raw_extras"]["deadline"] == "2026-12-31" and rec["raw_extras"]["level"] == "Central")
    check("ministry mapped", rec["ministry"] == "Ministry of Education")
    rec2 = records[1]
    check("state name kept lowercase", rec2["state"] == "karnataka")
    check("category mapped Business → loan", rec2["category"] == "loan")
    check("portal homepage is not direct", not is_direct_scheme_link("https://scholarships.gov.in/"))
    check("scheme path is direct", is_direct_scheme_link(rec["link"]))

    # Legacy flat shape must keep working (backward compat).
    legacy = {
        "data": [
            {
                "schemeName": "Legacy Flat Scheme",
                "ministryName": "Ministry of Finance",
                "categoryName": "scholarship",
                "objective": "Helps students.",
                "eligibilityCriteria": "Income below limit.",
                "slug": "legacy-flat-scheme",
                "keywords": "merit, scholarship",
            }
        ],
        "hasMore": False,
    }
    legacy_records = parse_schemes(legacy)
    check("legacy flat shape parsed", len(legacy_records) == 1)
    check("legacy tags parsed from string", legacy_records[0]["tags"] == ["merit", "scholarship"])


def test_dedup_scales():
    print("\n[7] DedupEngine LSH (catalog-scale)")
    import time

    from ingestion.dedup.dedup_engine import DedupEngine

    # 2,000 synthetic distinct names with diverse words (low pairwise trigram
    # overlap), so only the appended genuine duplicates should collapse.
    nouns = ["Scholarship", "Pension", "Yojana", "Grant", "Fellowship", "Loan", "Subsidy", "Aid", "Benefit", "Support"]
    adjectives = ["National", "State", "Rural", "Urban", "Central", "Special", "Merit", "Financial", "Social", "Technical"]
    recipients = ["Students", "Farmers", "Women", "Artisans", "Teachers", "Tribal", "Minorities", "Disabled", "Veterans", "Youth"]

    def _name(i):
        return f"{adjectives[i % 10]} {recipients[(i // 10) % 10]} {nouns[(i // 100) % 10]} Scheme {i:04d}"

    records = [{"name": _name(i), "scheme_id": f"s{i}", "link": f"https://example.gov.in/s{i}"} for i in range(2000)]
    # Two genuine near-duplicates that must be caught (same name + same link,
    # new ids) — an exact re-fetch of the same scheme.
    records.append({"name": records[0]["name"], "scheme_id": "dup0", "link": records[0]["link"]})
    records.append({"name": records[1]["name"], "scheme_id": "dup1", "link": records[1]["link"]})
    # A same-name DIFFERENT-link record must NOT be collapsed (distinct scheme).
    records.append({"name": records[0]["name"], "scheme_id": "other", "link": "https://example.gov.in/other"})

    start = time.monotonic()
    out = DedupEngine().deduplicate(records)
    elapsed = time.monotonic() - start

    check("same-name same-link collapsed (2003 → 2001)", len(out) == 2001, detail=f"(got {len(out)})")
    check(
        "same-name different-link kept",
        any(r["scheme_id"] == "other" for r in out),
    )
    check(
        "LSH dedup fast (< 15s for 2k records)",
        elapsed < 15,
        detail=f"(took {elapsed:.1f}s)",
    )


def test_ssp_parser():
    print("\n[6] Karnataka SSP parser smoke test")
    from ingestion.sources.karnataka_ssp.parser import parse_notices, parse_schemes

    html = """
    <html><body>
      <a href="/ssppre/PostMatricScholarship">Post Matric Scholarship</a>
      <a href="/home">Home</a>
      <div class="notice-board">
        <strong>Deadline extended to 31-10-2026</strong>
        <a href="/notices/123">Read more</a>
      </div>
    </body></html>
    """
    schemes = parse_schemes(html, base_url="https://ssp.karnataka.gov.in")
    check("scheme link extracted", any("Post Matric Scholarship" in s["scheme_name"] for s in schemes))
    check("scheme link is absolute", all(s["link"].startswith("http") for s in schemes))

    notices = parse_notices(html)
    check("notice extracted", len(notices) == 1)
    check("notice date parsed", notices[0]["published_at"] == "2026-10-31")


if __name__ == "__main__":
    test_fingerprint()
    test_classify()
    test_diff()
    test_two_run_scenario()
    test_myscheme_parser()
    test_ssp_parser()
    test_dedup_scales()

    print(f"\n{'=' * 40}\nResult: {PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)
