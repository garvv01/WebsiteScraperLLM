import json

from config.settings import MODEL_NAME
from extraction.prompts import build_extraction_prompt

def extract_page_data(page, client):

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": build_extraction_prompt(page)
            }
        ]
    )

    content = response.choices[0].message.content

    content = content.strip()

    if content.startswith("```json"):
        content = content.replace("```json", "", 1)

    if content.endswith("```"):
        content = content[:-3]

    content = content.strip()

    try:
        return json.loads(content)
    
    except Exception:
        return {
            "error": "invalid_json",
            "raw_response": content
        }