import json
import os
from config.settings import JSON_FILE

def load_data():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                seen = {item["Phone Name"] for item in data}
                return data, seen
        except Exception as e:
            print(f"Error loading {JSON_FILE}: {e}")
            return [], set()
    return [], set()

def save_data(data):
    try:
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Saved data to {JSON_FILE}")
    except Exception as e:
        print(f"Error saving {JSON_FILE}: {e}")