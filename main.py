import os
import time
from dotenv import load_dotenv
from firecrawl import FirecrawlApp
from openai import OpenAI
from utils.cleaners import clean_content
from utils.helpers import normalize_url
from crawler.discover import discover_urls
from extraction.extractor import extract_page_data
from extraction.merger import merge_results
from extraction.team_extractor import extract_team_data
from utils.savers import save_json

load_dotenv()

firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

app = FirecrawlApp(api_key=firecrawl_api_key)
client = OpenAI(api_key=openai_api_key)

url = normalize_url("https://www.2amvc.com")
all_pages = []
partial_results = []

discovered_urls = discover_urls(url, app, client)

print("\nDISCOVERED URLS:\n")
for discovered_url in discovered_urls:
    print(discovered_url)

print("\nSTARTING CONTENT SCRAPING...\n")

for discovered_url in discovered_urls:
    print("SCRAPING:", discovered_url)
    try:
        response = app.scrape(discovered_url)
        cleaned_content = clean_content(response.markdown)
        all_pages.append(
            {
                "url": discovered_url,
                "title": response.metadata.title,
                "content": cleaned_content,
                "is_homepage": normalize_url(discovered_url) == url,
            }
        )
        time.sleep(10)
    except Exception as e:
        print("FAILED:", discovered_url)
        print(e)

print("\nSCRAPED PAGES:\n")
for page in all_pages:
    print(page["url"])

save_json(all_pages, "output/scraped_pages.json")
print("\nSCRAPED PAGE DATA SAVED TO output/scraped_pages.json")

# ── MAIN EXTRACTION ───────────────────────────────────────────────────────────

print("\nSTARTING EXTRACTION...\n")

for page in all_pages:
    print("EXTRACTING:", page["url"])
    extracted_data = extract_page_data(page, client)
    extracted_data["is_homepage"] = page.get("is_homepage", False)
    partial_results.append(extracted_data)

final_json = merge_results(partial_results)

print("\nFINAL JSON:\n")
print(final_json)

save_json(final_json, "output/final.json")
print("\nFINAL JSON SAVED TO output/final.json")

# ── TEAM EXTRACTION ───────────────────────────────────────────────────────────

print("\nSTARTING TEAM EXTRACTION...\n")

# Pass app so team_extractor can scrape individual profile pages on demand
team_data = extract_team_data(all_pages, client, app=app)

print("\nTEAM DATA:\n")
for member in team_data:
    print(member)

save_json(team_data, "output/team.json")
print("\nTEAM DATA SAVED TO output/team.json")