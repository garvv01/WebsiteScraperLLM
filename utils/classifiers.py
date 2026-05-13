def get_page_type(url):

    normalized_url = url.lower()

    if "portfolio" in normalized_url:
            page_type = "portfolio"

    elif "team" in normalized_url or "people" in normalized_url:
            page_type = "team"

    elif "about" in normalized_url:
            page_type = "about"

    elif "contact" in normalized_url:
            page_type = "contact"

    elif "invest" in normalized_url or "pitch" in normalized_url:
            page_type = "invest"

    elif "news" in normalized_url or "blog" in normalized_url:
            page_type = "news"

    return "general"