import json

def save_json(data, filepath):

    with open(filepath, "w") as file:

        json.dump(data, file, indent=4, ensure_ascii=False)