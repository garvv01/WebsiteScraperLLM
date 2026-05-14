from extraction.schema_fields import TARGET_FIELDS

def build_extraction_prompt(page):

    fields_text = "\n".join([f"- {field}" for field in TARGET_FIELDS])

    return f"""
You are extracting structured information about an investment firm from a website page.

Extract ONLY information that is clearly present on this page.

If a field is missing, return null.

Target fields:

{fields_text}

Important extraction rules:

- linkedin must ONLY contain the company's official LinkedIn page.
- Do NOT include employee, founder, or partner LinkedIn profiles.
- If company LinkedIn does not exist, return null.

- pitch_url should contain founder application forms or pitch submission pages.
- pitch_email should contain dedicated founder/pitch email addresses.
- If one exists and the other does not, return the missing field as null.

- Extract investment amounts as numeric values only.
- Convert shorthand values:
    - 100k → 100000
    - 2M → 2000000
- If only one ticket size exists, use the same value for both min_investment_amount and max_investment_amount.
- Do NOT return formatted currency strings.

Return ONLY valid JSON.

Page URL:
{page["url"]}

Page Title:
{page["title"]}

Page Type:
{page["page_type"]}

Page Content:
{page["content"]}
"""