def clean_content(content):
    
    lines = content.splitlines()

    cleaned_lines = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        if len(line) < 3:
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)