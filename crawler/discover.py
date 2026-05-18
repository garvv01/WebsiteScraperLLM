import time
from urllib.parse import urlparse, urljoin
from config.settings import (
    EXCLUDED_PATTERNS,
    MAX_DEPTH,
    MODEL_NAME,
)
from utils.helpers import normalize_url
from crawler.prompts import build_discovery_prompt

# High-value URL keywords — sorted by importance.
# Links matching earlier keywords get priority in the LLM prompt.
PRIORITY_KEYWORDS = [
    "apply", "isafe", "safe", "invest", "thesis", "approach",
    "about", "faq", "how-we", "criteria", "focus", "stage",
    "sector", "portfolio", "companies", "team", "people",
    "contact", "founder", "resource", "partner", "process"
]

# These first path segments are always scraped regardless of what the LLM picks.
# Matched against ONLY the first segment of the URL path to avoid
# matching deep subpages like /investment-thesis/company-name.
# e.g. https://www.100x.vc/isafe → first segment = "isafe" → MATCH
#      https://www.100x.vc/investment-thesis/abc → first segment = "investment-thesis" → NO MATCH
MUST_SCRAPE_FIRST_SEGMENTS = {
    "apply", "isafe", "safe", "about", "about-us",
    "faq", "how-we-invest", "criteria", "invest", "approach"
}


def _priority_score(url):
    """Return a lower score for higher-priority URLs (for sorting)."""
    url_lower = url.lower()
    for i, keyword in enumerate(PRIORITY_KEYWORDS):
        if keyword in url_lower:
            return i
    return len(PRIORITY_KEYWORDS)


def _first_path_segment(url):
    """Return the first path segment of a URL in lowercase, or empty string."""
    parsed = urlparse(url)
    segments = [s for s in parsed.path.split("/") if s]
    return segments[0].lower() if segments else ""


def discover_urls(start_url, app, client):
    base_domain = urlparse(start_url).netloc
    queue = [(start_url, 0)]
    visited = set()
    discovered_urls = set()
    discovered_urls.add(start_url)

    while queue:
        current_url, depth = queue.pop(0)

        if current_url in visited:
            continue
        visited.add(current_url)

        if depth < MAX_DEPTH:
            links_data = app.map(current_url)
            time.sleep(10)

            if links_data.links:
                link_urls = [link.url for link in links_data.links]

                # Step 1: filter out excluded patterns
                filtered_links = []
                for link in link_urls:
                    normalized_link = link.lower()
                    if not any(pattern in normalized_link for pattern in EXCLUDED_PATTERNS):
                        filtered_links.append(link)

                filtered_links = list(set(filtered_links))

                # Step 2: sort by priority score so high-value pages come first
                filtered_links.sort(key=lambda u: (_priority_score(u), u.lower()))

                # Step 3: send top 60 to LLM
                links_text = "\n".join(filtered_links[:60])

                llm_response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {
                            "role": "user",
                            "content": build_discovery_prompt(links_text)
                        }
                    ]
                )

                important_links = [
                    link.strip()
                    for link in llm_response.choices[0].message.content.splitlines()
                    if link.strip()
                ]

                # Step 4: add LLM-selected links
                for link in important_links:
                    full_url = normalize_url(urljoin(current_url, link))
                    link_domain = urlparse(full_url).netloc

                    if (
                        link_domain == base_domain
                        and full_url not in visited
                    ):
                        discovered_urls.add(full_url)
                        print("QUEUEING:", full_url)
                        queue.append((full_url, depth + 1))

                # Step 5: force-add must-scrape pages the LLM may have missed.
                # Only matches on the FIRST path segment to avoid deep subpages
                # like /investment-thesis/company-name being incorrectly included.
                for link in filtered_links:
                    full_url = normalize_url(urljoin(current_url, link))
                    link_domain = urlparse(full_url).netloc

                    if link_domain != base_domain:
                        continue
                    if full_url in visited or full_url in discovered_urls:
                        continue

                    first_seg = _first_path_segment(full_url)
                    if first_seg in MUST_SCRAPE_FIRST_SEGMENTS:
                        discovered_urls.add(full_url)
                        print("FORCE-ADDING:", full_url)
                        queue.append((full_url, depth + 1))

    return discovered_urls