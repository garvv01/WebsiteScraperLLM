def build_team_prompt(page):
    return f"""
You are extracting team member information from an investment firm's website page.

Page URL: {page["url"]}
Page Content:
{page["content"]}

---

Your task:
Extract every team member mentioned on this page and return them as a JSON array.

Each team member object must have exactly these fields:
- name: full name of the person (string)
- position: their job title or role (string)
- profile_url: their individual profile page URL if present in the page content (string or null)
- linkedin: their personal LinkedIn profile URL if present on THIS page (string or null)
- email: their email address if present on THIS page (string or null)

Rules:
- Return ALL team members mentioned, not just partners or senior staff.
- position should be their exact title as written on the page (e.g. "General Partner", "Associate").
- profile_url should be the link to their individual profile page on the same website
  (e.g. "https://www.peakxv.com/people/shailendra-singh"). Only include if clearly present.
- linkedin must be a personal profile URL (linkedin.com/in/...).
  Do NOT use company LinkedIn pages (linkedin.com/company/...).
- email should only be a personal or role-specific email.
  Do NOT use general firm emails like hello@, info@, contact@.
- If a field is not available on this page, return null for that field.
- Do not invent or guess any information.
- Do not include advisors, mentors, or portfolio founders — only the firm's own team.

Return ONLY a valid JSON array. No explanation, no markdown, no extra text.

Example output format:
[
    {{
        "name": "John Smith",
        "position": "General Partner",
        "profile_url": "https://www.example.com/people/john-smith",
        "linkedin": null,
        "email": null
    }}
]
"""