import re

def clean_content(content):
    
    content = re.sub(r'!\[.*?\]\(.*?\)', '', content)

    lines = content.splitlines()

    lines = [
        line for line in lines
        if not (
            "google.com/maps" in line
            or "_next/image" in line
            or "recaptcha" in line.lower()
            or "gstatic" in line
            or "token=" in line
        )
    ]

    cleaned_lines = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)