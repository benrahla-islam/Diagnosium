import json
from rapidfuzz import process

def load_database(path=r"static\medicines.json"):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)

def find_drug_info(drug_name, data):
    candidates = []
    for letter, meds in data.items():
        for med in meds:
            candidates.append(med["name"])

    match, score = process.extractOne(drug_name, candidates)
    if score > 80:
        for letter, meds in data.items():
            for med in meds:
                if med["name"] == match:
                    return med  # Return full record
    return None
