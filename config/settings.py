EXCLUDED_PATTERNS = [
    "#",
    "page=",
    "privacy",
    "terms",
    "cookie",
    "login",
    "signup",
    "/people/",         # skip individual team profile pages e.g. /people/shailendra-singh
    "/investment-thesis/",  # skip individual portfolio thesis pages
]

MAX_DEPTH = 3

MODEL_NAME = "gpt-5.4"

HOMEPAGE_PRIORITY_FIELDS = {
    "name",
    "title",
    "about_us",
    "investment_thesis",
    "website",
    "ticket_size",
    "min_investment_amount",
    "max_investment_amount",
}