from extraction.schema_fields import TARGET_FIELDS


def build_extraction_prompt(page):
    fields_text = "\n".join([f"- {field}" for field in TARGET_FIELDS])

    is_homepage = page.get("is_homepage", False)

    return f"""
You are extracting structured information about an investment firm from a website page.
Extract ONLY information that is clearly and explicitly present on this page.
If a field is missing or cannot be confidently determined, return null.

Page URL: {page["url"]}
Page Title: {page["title"]}
Is Homepage: {is_homepage}
Page Content:
{page["content"]}

---

Target fields:
{fields_text}

---

Important extraction rules:

GENERAL:
- Extract ONLY from the page content above. Do not infer, guess, or hallucinate.
- If a field is not clearly and explicitly stated, return null.

name:
- Extract the firm's official name.
- Only extract from homepage or about pages, not from form pages.

title:
- The firm's tagline or headline, NOT a page heading like "Contact Us" or "Get In Touch".
- Only extract if is_homepage is true.
- If is_homepage is false, return null for title.

website:
- Must be the main homepage URL of the investment firm.
- Do not use the current page URL unless it is the homepage.

linkedin:
- Must be the LinkedIn page representing the investment firm itself (e.g. /company/...).
- Do not use individual team member LinkedIn profiles.
- If no company LinkedIn exists, return null.

pitch_url:
- Use founder application forms, pitch submission pages, or contact forms intended for founders.
- Always return the full URL including https:// and www. if present on the site.
- If a dedicated pitch page does not exist but a contact page is clearly for founder outreach, use that URL.

contact_link:
- Always return the full URL including https:// and www. if present on the site.

ticket_size:
- ONLY extract if the page explicitly states a specific investment amount or range as a string (e.g. "$500k", "$100k - $2M").
- Do NOT infer or calculate from other fields.
- If not explicitly stated, return null.

min_investment_amount:
- ONLY extract if the page explicitly states a minimum investment amount.
- Must be a plain number only (no symbols, no text).
- Convert shorthand: 100k → 100000, 2M → 2000000.
- "starting at X", "minimum cheque X", "from X" → set this field to that value.
- "up to X", "as much as X" (maximum-only language) → return null for this field.
- If no explicit minimum is stated, return null.

max_investment_amount:
- ONLY extract if the page explicitly states a maximum investment amount.
- Must be a plain number only (no symbols, no text).
- Convert shorthand: 100k → 100000, 2M → 2000000.
- "up to X", "as much as X", "maximum X" → set this field to that value.
- "starting at X", "minimum cheque X" (minimum-only language) → return null for this field.
- If no explicit maximum is stated, return null.

ticket_size / min / max consistency rules:
- Range stated (e.g. "$100k - $2M"): ticket_size = "$100k - $2M", min = 100000, max = 2000000.
- Single amount stated (e.g. "we write $500k checks"): ticket_size = "$500k", min = 500000, max = null.
- Nothing stated about investment amounts: all three fields must be null.
- NEVER set these fields based on portfolio company valuations or round sizes.

total_company_invested:
- Do NOT count links, logos, or list items on a page.
- Only extract if the page explicitly states a number (e.g. "we have invested in 40+ companies").
- If not explicitly stated, return null.

sectors:
- Must be an array of strings.
- ONLY extract if the firm explicitly lists their focus sectors in an about/homepage section.
- Blog post tags, article categories, and Medium post labels are NOT sector indicators.
- Contact form dropdown options are NOT sector indicators.
- If no explicit sector focus is stated, return null.

investment_stages:
- Must be an array of normalized stage strings.
- Normalize to standard labels ONLY: "Pre-Seed", "Seed", "Series A", "Series B", "Growth", "Late Stage".
- ONLY extract if the firm explicitly states the stages they invest in.
- Phrases like "selectively in growth stages" or "follow-on rounds" in general descriptions are NOT explicit stage declarations.
- If no explicit stage is stated, return null.

geographic_focus:
- Always an array of strings.
- Only extract if explicitly mentioned.

portfolio_companies:
- Extract company names from a portfolio or partnerships page.
- Return as an array of clean company name strings.
- Do not include the investment firm itself.

special_reachout_remarks:
- Maximum 1 sentence summarizing founder outreach instructions.
- Do NOT list individual form fields.

Return ONLY valid JSON. No explanation, no markdown fences, no extra text.
"""