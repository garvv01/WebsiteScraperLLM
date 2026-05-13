from extraction.schema_fields import TARGET_FIELDS

def build_discovery_prompt(links_text):

    fields_text = "\n".join([f"- {field}" for field in TARGET_FIELDS])

    return f"""
You are helping build a structured database of investment firms.

We want to extract the following information from the website:

{fields_text}

Below is a list of already discovered internal links from the website.

Your task:
Select ALL internal links that could help extract ANY investor-related information.

Even moderately useful pages should be included.

Examples of useful pages include:
- about
- team
- people
- portfolio
- companies
- investment approach
- thesis
- sectors
- founder resources
- apply
- FAQ
- contact
- news
- blog
- partners
- careers (sometimes contains culture/thesis)

Prioritize links related to:
- portfolio companies
- investment thesis
- sectors
- stages
- founder applications
- team members
- contact information
- pitch submission
- firm overview

Also include supporting pages such as:
- about pages
- team pages
- founder pages
- investment approach pages
- FAQ pages
- application pages

Ignore:
- legal pages
- privacy pages
- terms pages
- login/signup pages
- pagination links
- social share links

Rules:
- Return ONLY URLs
- One URL per line
- No explanations
- No markdown
- No numbering

Links:
{links_text}
"""