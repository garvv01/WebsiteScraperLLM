import time

from urllib.parse import urlparse, urljoin

from config.settings import (
    IMPORTANT_LINK_KEYWORDS,
    EXCLUDED_PATTERNS,
    MAX_DEPTH,
    RATE_LIMIT,
    MODEL_NAME
)

from utils.helpers import normalize_url

def discover_urls(start_url, app, client):

    base_domain = urlparse(start_url).netloc

    queue = [(start_url, 0)]

    visited = set()

    discovered_urls = set()
    discovered_urls.add(start_url)

    queued_urls = {start_url}

    while queue:
        start_url, depth = queue.pop(0)

        if start_url in visited:
            continue

        visited.add(start_url)

        if depth < MAX_DEPTH:

            links_data = app.map(start_url)

            time.sleep(RATE_LIMIT)

            if links_data.links:

                link_urls = [link.url for link in links_data.links]

                filtered_links = []

                for link in link_urls:  

                    normalized_link = link.lower()

                    if any(word in normalized_link for word in IMPORTANT_LINK_KEYWORDS) and not any(pattern in normalized_link for pattern in EXCLUDED_PATTERNS):
                        filtered_links.append(link)

                links_text = "\n".join(filtered_links[:20])

                llm_response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {
                            "role": "system",
                            "content": """
                        You are a website crawling assistant.

                        Return ONLY important internal URLs.

                        Rules:
                        - Return one URL per line
                        - No explanations
                        - No markdown
                        - No numbering
                        - No extra text
                        - If no useful links exist, return NOTHING
                        """
                        },
                        {
                            "role": "user",
                            "content": links_text
                        }
                    ]
                )

                important_links = [
                    link.strip()
                    for link in llm_response.choices[0].message.content.splitlines()
                    if link.strip()
                ]

                for link in important_links:

                    full_url = normalize_url(urljoin(start_url, link))

                    link_domain = urlparse(full_url).netloc

                    if (
                        link_domain == base_domain
                        and full_url not in visited
                        and full_url not in queued_urls
                    ):

                        discovered_urls.add(full_url)

                        queued_urls.add(full_url)

                        print("QUEUEING:", full_url)

                        queue.append((full_url, depth +1))
    
    return discovered_urls