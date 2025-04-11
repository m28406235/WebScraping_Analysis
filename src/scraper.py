from bs4 import BeautifulSoup
import requests
import json
import os
import time
from urllib.parse import urljoin, urlparse
import re

BASE_URL = "https://www.gsmarena.com"
SEARCH_URL = f"{BASE_URL}/results.php3?nYearMin=2024&nDisplayResMin=2073600&sAvailabilities=1&idOS=2&sFingerprints=1"
JSON_FILE = "phone_specs.json"
HEADERS = {"User-Agent": "Mozilla/5.0"}
DELAY = 1

def get_links():
    res = requests.get(SEARCH_URL, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")
    return [a["href"] for div in soup.find_all("div", class_="makers") for a in div.find_all("a", href=True)]

def get_phone_name_from_url(url):
    match = re.search(r'/([^/]+)-\d+\.php', urlparse(url).path)
    return match.group(1).replace("_", " ").title() if match else None

def scrape_phone(url):
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")
    title = soup.find("h1", class_="specs-phone-name-title")
    if not title:
        return None
    data = {"Phone Name": title.text.strip()}
    specs = soup.find("div", id="specs-list")
    if specs:
        for table in specs.find_all("table"):
            for row in table.find_all("tr"):
                cols = row.find_all("td")
                if len(cols) > 1:
                    data[cols[0].text.strip()] = cols[1].text.strip()
    return data

def load_json():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data, {item["Phone Name"] for item in data}
    return [], set()

def save_json(data):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    all_data, seen_names = load_json()
    links = get_links()

    for i, link in enumerate(links, 1):
        url = urljoin(BASE_URL, link)
        name = get_phone_name_from_url(url)
        print(f"[{i}/{len(links)}] {name}... ", end="")

        if not name or name in seen_names:
            print("skipped")
            continue

        data = scrape_phone(url)
        if data:
            all_data.append(data)
            seen_names.add(data["Phone Name"])
            print("done")
        else:
            print("failed")

        time.sleep(DELAY)

    save_json(all_data)
    print(f"\nSaved {len(all_data)} phones to {JSON_FILE}")