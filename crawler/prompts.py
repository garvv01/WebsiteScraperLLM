from extraction.schema_fields import TARGET_FIELDS


def build_discovery_prompt(links_text):
    fields_text = "\n".join([f"- {field}" for field in TARGET_FIELDS])

    return f"""
You are helping build a structured database of investment firms.
We want to extract the following information from the website:
{fields_text}

Below is a list of internal links from the website, already sorted by likely relevance.
Your task: select the links most likely to contain the target information.

HIGH PRIORITY — always include if present:
- apply / application / pitch / submit
- isafe / safe / safe-note / how-we-invest
- about / about-us / who-we-are
- investment-thesis / thesis / approach / criteria / focus
- faq / frequently-asked-questions
- portfolio / companies / investments
- team / people / partners

MEDIUM PRIORITY — include if the high priority pages are sparse:
- contact / contact-us
- sectors / industries
- founder-resources / founders-hub
- news / blog / insights (only the index page, not individual articles)
- careers (sometimes contains culture or thesis)

SKIP entirely:
- individual blog posts or news articles
- legal / privacy / terms / cookie pages
- login / signup / auth pages
- pagination links (?page=, /page/)
- social media share links
- anchor-only links (#section)

Rules:
- Return ONLY URLs, one per line
- No explanations, no markdown, no numbering
- Prefer pages that are likely to mention: ticket size, cheque size, investment amount,
  stage focus, sector focus, geographic focus, or founder application process

Links:
{links_text}
"""