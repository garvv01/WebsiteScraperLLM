import re
import json
import time
from config.settings import MODEL_NAME
from extraction.team_prompt import build_team_prompt
from utils.cleaners import clean_content

# Regex patterns for extracting linkedin and email directly from page content
LINKEDIN_PATTERN = re.compile(
    r'https?://(?:www\.)?linkedin\.com/in/[^\s\)\]"\'<>]+'
)
EMAIL_PATTERN = re.compile(
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
)

# Emails to ignore — generic firm-level addresses
IGNORED_EMAIL_PREFIXES = ("hello", "info", "contact", "team", "support", "hi", "admin", "press")

# Keywords to identify team pages by URL
TEAM_PAGE_KEYWORDS = [
    "our-team", "/team", "people", "management",
    "staff", "crew", "who-we-are", "leadership"
]


def _fetch_links_via_firecrawl(url, app):
    """Use Firecrawl links format to get all URLs including LinkedIn."""
    try:
        response = app.scrape(url, formats=["markdown", "links"])
        links = response.links or []
        linkedin_links = [
            l for l in links
            if "linkedin.com/in/" in l.lower()
        ]
        return linkedin_links
    except Exception as e:
        print(f"FAILED TO FETCH LINKS FOR {url}: {e}")
        return []


def _scrape_profile(profile_url, app):
    """
    Scrape an individual team member's profile page and extract
    their LinkedIn URL and email using regex — no LLM needed.
    """
    print(f"  SCRAPING PROFILE: {profile_url}")

    try:
        response = app.scrape(profile_url, formats=["markdown", "links"])
        content = clean_content(response.markdown)
        time.sleep(3)

        # Try structured links first, fall back to regex
        linkedin_links = _fetch_links_via_firecrawl(profile_url, app)
        linkedin = linkedin_links[0].rstrip(".,;)") if linkedin_links else None

        if not linkedin:
            linkedin_match = LINKEDIN_PATTERN.search(content)
            linkedin = linkedin_match.group(0).rstrip(".,;)") if linkedin_match else None

        email = None
        for match in EMAIL_PATTERN.finditer(content):
            candidate = match.group(0)
            prefix = candidate.split("@")[0].lower()
            if not any(prefix.startswith(ig) for ig in IGNORED_EMAIL_PREFIXES):
                email = candidate
                break

        return {"linkedin": linkedin, "email": email}

    except Exception as e:
        print(f"  FAILED TO SCRAPE PROFILE {profile_url}: {e}")
        return {"linkedin": None, "email": None}


def _parse_search_result(result):
    """
    Safely extract url and content from a Firecrawl search result,
    which may be a tuple, dict, or object depending on SDK version.
    """
    if isinstance(result, tuple):
        url = result[0] if len(result) > 0 else ""
        content = result[1] if len(result) > 1 else ""
    elif isinstance(result, dict):
        url = result.get("url", "")
        content = result.get("markdown", "") or result.get("content", "") or ""
    else:
        url = getattr(result, "url", "") or ""
        content = (
            getattr(result, "markdown", "")
            or getattr(result, "content", "")
            or ""
        )
    return str(url), str(content)


def _enrich_via_search(member, firm_name, app):
    """
    Use Firecrawl's search to find a team member's LinkedIn URL
    when no profile_url is available on the website.
    Searches for "<name> <firm> linkedin" and regex-extracts the URL.
    """
    name = member.get("name", "")
    query = f"{name} {firm_name} linkedin"
    print(f"  SEARCHING FOR: {query}")

    try:
        results = app.search(query)
        time.sleep(2)

        for result in results:
            url, content = _parse_search_result(result)

            # Check if the result URL itself is a LinkedIn profile
            if "linkedin.com/in/" in url.lower():
                return url.rstrip(".,;)")

            # Otherwise regex the content for a LinkedIn URL
            if content:
                linkedin_match = LINKEDIN_PATTERN.search(content)
                if linkedin_match:
                    return linkedin_match.group(0).rstrip(".,;)")

    except Exception as e:
        print(f"  SEARCH FAILED FOR {name}: {e}")

    return None


def _find_team_pages_by_keyword(pages):
    """Try to find team pages using URL keywords — fast, no LLM."""
    return [
        page for page in pages
        if any(kw in page["url"].lower() for kw in TEAM_PAGE_KEYWORDS)
    ]


def _find_team_pages_by_llm(pages, client):
    """
    Fallback: ask the LLM to look at all page URLs and content previews
    and identify which ones are most likely to contain team member info.
    Homepage is always sent in full since team sections can appear anywhere on it.
    """
    print("USING LLM FALLBACK TO FIND TEAM PAGE...\n")

    # Send full content for homepage, 800 char preview for other pages
    pages_summary = "\n".join([
        f"URL: {page['url']}\nIs Homepage: {page.get('is_homepage', False)}\nContent: {page['content'] if page.get('is_homepage') else page['content'][:800]}\n---"
        for page in pages
    ])

    prompt = f"""
You are helping find team member information from an investment firm's website.

Below are all the pages scraped from the website, with their URLs and content.
The homepage is sent in full — team members may appear anywhere on it.
Your task: identify which pages contain the firm's actual team members with their names and positions.

Pages:
{pages_summary}

Rules:
- Only return pages that actually list people by name with their roles.
- Do NOT return pages that just describe what the team does without naming individuals.
- Team members may appear on the homepage — always check it carefully.
- Return ONLY the URLs, one per line.
- No explanation, no markdown, no numbering.
- If no page contains actual named team members, return the word: NONE
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}]
    )

    result = response.choices[0].message.content.strip()

    if result.upper() == "NONE":
        print("LLM could not find any team page with named members.")
        return []

    selected_urls = {line.strip() for line in result.splitlines() if line.strip()}
    matched_pages = [p for p in pages if p["url"] in selected_urls]

    if matched_pages:
        print(f"LLM IDENTIFIED TEAM PAGES: {[p['url'] for p in matched_pages]}\n")
    else:
        print("LLM returned URLs that don't match any scraped pages.")

    return matched_pages


def _extract_members_from_pages(team_pages, client):
    """Run LLM extraction on each team page and return deduplicated members."""
    all_members = []
    seen_names = set()

    for page in team_pages:
        print(f"EXTRACTING TEAM FROM: {page['url']}")

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": build_team_prompt(page)}]
        )

        content = response.choices[0].message.content.strip()

        if content.startswith("```json"):
            content = content.replace("```json", "", 1)
        if content.startswith("```"):
            content = content.replace("```", "", 1)
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            members = json.loads(content)

            if not isinstance(members, list):
                print(f"UNEXPECTED FORMAT from {page['url']} — expected a list")
                continue

            for member in members:
                name = member.get("name", "").strip()
                if name and name not in seen_names:
                    seen_names.add(name)
                    all_members.append(member)

        except Exception as e:
            print(f"INVALID JSON FROM {page['url']}: {e}")
            continue

    return all_members


def _get_firm_name(pages):
    """Extract the domain from the homepage URL to use in search queries."""
    for page in pages:
        if page.get("is_homepage"):
            url = page.get("url", "")
            match = re.search(r'https?://(?:www\.)?([^/]+)', url)
            if match:
                return match.group(1)
    return ""


def extract_team_data(pages, client, app=None):
    """
    Goes through all scraped pages, finds team-related pages,
    extracts team member details, and optionally enriches with
    individual profile pages for LinkedIn and email.

    Strategy:
    1. Try keywords to find team pages (fast, free)
    2. If keywords find pages but 0 members extracted → wrong page matched,
       fall through to LLM fallback
    3. If keywords find nothing → go straight to LLM fallback
    4. Extract members from found pages
    5. Enrich via profile_url scraping if available
    6. Enrich via Firecrawl search for members still missing LinkedIn
    7. Drop members with neither linkedin nor email

    Args:
        pages: list of scraped page dicts (url, title, content, is_homepage)
        client: OpenAI client instance
        app: FirecrawlApp instance (optional — needed for profile enrichment)

    Returns:
        list of team member dicts with name, position, linkedin, email
        Only includes members who have at least one of linkedin or email.
    """

    # Step 1: try keywords first
    team_pages = _find_team_pages_by_keyword(pages)

    if team_pages:
        # Step 2: keywords found pages — try extracting members
        all_members = _extract_members_from_pages(team_pages, client)

        if len(all_members) == 0:
            # Keywords matched a page but it had no actual people listed
            # Fall through to LLM to find the right page
            print("KEYWORDS FOUND A PAGE BUT 0 MEMBERS EXTRACTED — trying LLM fallback...\n")
            team_pages = _find_team_pages_by_llm(pages, client)
            all_members = _extract_members_from_pages(team_pages, client)
    else:
        # Step 3: keywords found nothing — go straight to LLM
        team_pages = _find_team_pages_by_llm(pages, client)
        all_members = _extract_members_from_pages(team_pages, client)

    # Step 4: give up if still nothing
    if not all_members:
        print("COULD NOT FIND ANY TEAM MEMBERS — skipping team extraction")
        return []

    print(f"\nTEAM MEMBERS FOUND: {len(all_members)}")

    # Step 5: enrich with profile pages using regex — no LLM needed
    members_to_enrich = [
        m for m in all_members
        if m.get("profile_url") and not m.get("linkedin")
    ]

    if app and members_to_enrich:
        print(f"\nENRICHING {len(members_to_enrich)} PROFILES WITH LINKEDIN/EMAIL...\n")

        for member in all_members:
            if member.get("profile_url") and not member.get("linkedin"):
                enriched = _scrape_profile(member["profile_url"], app)
                member["linkedin"] = enriched["linkedin"]
                member["email"] = enriched["email"]

    # Remove profile_url from final output — internal scaffolding only
    for member in all_members:
        member.pop("profile_url", None)

    # Step 6: search enrichment for members still missing LinkedIn
    members_without_linkedin = [
        m for m in all_members
        if not m.get("linkedin")
    ]

    if app and members_without_linkedin:
        firm_name = _get_firm_name(pages)
        print(f"\nSEARCH ENRICHMENT FOR {len(members_without_linkedin)} MEMBERS WITHOUT LINKEDIN...\n")

        for member in all_members:
            if not member.get("linkedin"):
                linkedin = _enrich_via_search(member, firm_name, app)
                if linkedin:
                    member["linkedin"] = linkedin
                    print(f"  FOUND VIA SEARCH: {member['name']} → {linkedin}")
                else:
                    print(f"  NOT FOUND: {member['name']}")

    # Step 7: drop members with neither linkedin nor email
    before = len(all_members)
    all_members = [
        m for m in all_members
        if m.get("linkedin") or m.get("email")
    ]
    dropped = before - len(all_members)
    if dropped > 0:
        print(f"DROPPED {dropped} MEMBERS WITH NO LINKEDIN OR EMAIL")

    print(f"\nTOTAL TEAM MEMBERS EXTRACTED: {len(all_members)}")
    return all_members