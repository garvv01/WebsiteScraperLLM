from extraction.schema_fields import TARGET_FIELDS

def build_extraction_prompt(page):

    fields_text = "\n".join([f"- {field}" for field in TARGET_FIELDS])

    return f"""
You are extracting structured information about an investment firm from a website page.

Extract ONLY information that is clearly present on this page.

If a field is missing, return null.

Target fields:

{fields_text}

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