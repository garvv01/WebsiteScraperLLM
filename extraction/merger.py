from config.settings import HOMEPAGE_PRIORITY_FIELDS
from extraction.schema_fields import TARGET_FIELDS


def merge_results(partial_results):
    final_json = {field: None for field in TARGET_FIELDS}

    homepage_result = None
    other_results = []

    for result in partial_results:
        if "error" in result:
            continue
        if result.get("is_homepage"):
            homepage_result = result
        else:
            other_results.append(result)

    ordered_results = ([homepage_result] if homepage_result else []) + other_results

    for result in ordered_results:
        if "error" in result:
            continue

        for field, value in result.items():
            if field == "is_homepage":
                continue
            if value is None:
                continue

            if field in HOMEPAGE_PRIORITY_FIELDS and final_json[field] is not None:
                continue

            if final_json[field] is None:
                final_json[field] = value
            elif isinstance(value, list):
                existing = final_json[field]
                if not isinstance(existing, list):
                    existing = [existing]
                existing_lower = {v.lower() for v in existing if isinstance(v, str)}
                new_vals = [v for v in value if not (isinstance(v, str) and v.lower() in existing_lower)]
                final_json[field] = existing + new_vals

    for field, value in final_json.items():
        if isinstance(value, list) and len(value) == 0:
            final_json[field] = None

    if final_json.get("portfolio_companies"):
        final_json["total_company_invested"] = len(final_json["portfolio_companies"])
    else:
        final_json["total_company_invested"] = None

    min_val = final_json.get("min_investment_amount")
    max_val = final_json.get("max_investment_amount")
    ticket = final_json.get("ticket_size")

    if ticket is None and (min_val is not None or max_val is not None):
        if min_val is not None and max_val is not None:
            final_json["ticket_size"] = f"${_format_amount(min_val)} - ${_format_amount(max_val)}"
        elif min_val is not None:
            final_json["ticket_size"] = f"${_format_amount(min_val)}"
        elif max_val is not None:
            final_json["ticket_size"] = f"Up to ${_format_amount(max_val)}"

    for url_field in ("pitch_url", "contact_link", "website"):
        val = final_json.get(url_field)
        if val and val.startswith("https://sparrowvc.com"):
            final_json[url_field] = val.replace("https://sparrowvc.com", "https://www.sparrowvc.com", 1)

    return final_json


def _format_amount(amount):
    """Format a numeric amount into a readable shorthand string."""
    try:
        amount = int(amount)
        if amount >= 1_000_000:
            return f"{amount // 1_000_000}M" if amount % 1_000_000 == 0 else f"{amount / 1_000_000:.1f}M"
        elif amount >= 1_000:
            return f"{amount // 1_000}k" if amount % 1_000 == 0 else f"{amount / 1_000:.1f}k"
        return str(amount)
    except (TypeError, ValueError):
        return str(amount)