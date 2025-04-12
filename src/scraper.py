from bs4 import BeautifulSoup
import requests
import json
import os
import time
from urllib.parse import urljoin
from tqdm import tqdm

BASE_URL = "https://www.gsmarena.com"
SEARCH_URL = f"{BASE_URL}/results.php3?nYearMin=2024&nDisplayResMin=2073600&sAvailabilities=1&idOS=2&sFingerprints=1"
JSON_FILE = "phone_specs.json"
HEADERS = {"User-Agent": "Mozilla/5.0"}
DELAY = 1

def get_links():
    soup = BeautifulSoup(requests.get(SEARCH_URL, headers=HEADERS).text, "html.parser")
    return [a["href"] for div in soup.find_all("div", class_="makers") for a in div.find_all("a", href=True)]

def scrape_phone(url):
    soup = BeautifulSoup(requests.get(url, headers=HEADERS).text, "html.parser")
    title = soup.find("h1", class_="specs-phone-name-title")
    if not title:
        return None
    data = {"Phone Name": title.text.strip()}
    for row in soup.find("div", id="specs-list").find_all("tr"):
        cols = row.find_all("td")
        if len(cols) > 1:
            data[cols[0].text.strip()] = cols[1].text.strip()
    return data

def load_json():
    return json.load(open(JSON_FILE, "r", encoding="utf-8")) if os.path.exists(JSON_FILE) else ([], set())

def save_json(data):
    json.dump(data, open(JSON_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

if __name__ == "__main__":
    all_data, seen_names = load_json()
    links = get_links()
    for link in tqdm(links, desc="Scraping phones", unit="phone"):
        url = urljoin(BASE_URL, link)
        name = link.split("/")[-1].split("-")[0].replace("_", " ").title()
        
        if name in seen_names:
            continue

        if data := scrape_phone(url):
            all_data.append(data)
            seen_names.add(name)

        time.sleep(DELAY)

    save_json(all_data)
    print(f"Saved {len(all_data)} phones to {JSON_FILE}")