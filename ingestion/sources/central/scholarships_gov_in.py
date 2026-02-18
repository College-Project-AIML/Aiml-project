# ingestion/sources/central/scholarships_gov_in.py

from playwright.sync_api import sync_playwright
import json
import time

API_RESPONSES = []

def capture_response(response):
    url = response.url
    if "scholarship" in url.lower() or "scheme" in url.lower():
        try:
            if response.request.resource_type == "xhr":
                data = response.json()
                API_RESPONSES.append({
                    "url": url,
                    "data": data
                })
        except:
            pass

def scrape_scholarships():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.on("response", capture_response)

        page.goto("https://scholarships.gov.in", timeout=60000)
        page.wait_for_timeout(15000)  # allow JS + API calls

        browser.close()

    return API_RESPONSES


if __name__ == "__main__":
    data = scrape_scholarships()

    print(f"Captured {len(data)} API responses")

    with open("scholarships_api_dump.json", "w") as f:
        json.dump(data, f, indent=2)

    print("Saved scholarships_api_dump.json")
