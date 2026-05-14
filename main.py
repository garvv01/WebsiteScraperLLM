import os
import time
from dotenv import load_dotenv
from firecrawl import FirecrawlApp
from openai import OpenAI
from utils.cleaners import clean_content
from utils.classifiers import get_page_type
from utils.helpers import normalize_url
from crawler.discover import discover_urls
from extraction.extractor import extract_page_data
from extraction.merger import merge_results
from utils.savers import save_json

load_dotenv()

firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

app = FirecrawlApp(api_key=firecrawl_api_key)

client = OpenAI(api_key=openai_api_key)

url = normalize_url("https://pointone.capital")

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

        page_type = get_page_type(discovered_url)

        all_pages.append(
            {
                "url": discovered_url,
                "title": response.metadata.title,
                "page_type": page_type,
                "content": cleaned_content
            }
        )

        time.sleep(10)

    except Exception as e:

        print("FAILED:", discovered_url)

        print(e)

print("\nSCRAPED PAGES:\n")

for page in all_pages:
    print(page["url"])

print("\nSTARTING EXTRACTION...\n")

for page in all_pages:

    print("EXTRACTING:", page["url"])

    extracted_data = extract_page_data(page, client)

    partial_results.append(extracted_data)

print("\nPARTIAL RESULTS:\n")

for result in partial_results:
    print(result)

final_json = merge_results(partial_results)

print("\nFINAL JSON:\n")

print(final_json)

save_json(final_json, "output/final.json")