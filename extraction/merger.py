from extraction.schema_fields import TARGET_FIELDS

def merge_results(partial_results):
    final_json = {}

    for field in TARGET_FIELDS:

        final_json[field] = None

    for result in partial_results:

        for field, value in result.items():

            if value is None:
                continue

            if final_json[field] is None:

                final_json[field] = value

            elif isinstance(value, list):

                existing = final_json[field]

                if not isinstance(existing, list):
                    existing = [existing]

                merged = existing + value

                final_json[field] = list(set(merged))

    return final_json