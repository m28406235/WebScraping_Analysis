from bs4 import BeautifulSoup
import requests
import json
import os
import time
import random
from urllib.parse import urljoin
from tqdm import tqdm

BASE_URL = "https://www.gsmarena.com"
SEARCH_URL = f"{BASE_URL}/results.php3?nYearMin=2020&nYearMax=2024&nPriceMin=400&nPriceMax=450&nDisplayResMin=2073600&sAvailabilities=1&idOS=2&sChipset=158,125,143,116,115,104,144,140,154,124,123,114,156,145,141,142,155,122,92,77,79,57,42,80,41,31,27,1,2,3,120,81,91,62,43,82,83,46,36,58,48,29,105,78,127,106,35,33,44,90,4,5,45,28,59,6,7,89,61,8,34,9,10,60,11,88&sFingerprints=1"
JSON_FILE = "phone_specs.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def get_links():
    try:
        r = requests.get(SEARCH_URL, headers=HEADERS, timeout=10)
        r.raise_for_status()
        s = BeautifulSoup(r.text, "html.parser")
        return [a["href"] for d in s.find_all("div", class_="makers") for a in d.find_all("a", href=True)]
    except:
        return []


def scrape_phone(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        s = BeautifulSoup(r.text, "html.parser")
        name = s.find("h1", class_="specs-phone-name-title")
        if not name:
            return None
        specs = s.find("div", id="specs-list")
        if not specs:
            return None
        data = {"Phone Name": name.text.strip()}
        categories = {}
        current_cat = None
        for t in specs.find_all("table"):
            for row in t.find_all("tr"):
                th = row.find("th")
                if th and th.get("rowspan"):
                    current_cat = th.text.strip()
                    categories[current_cat] = categories.get(current_cat, {})
                ttl = row.find("td", class_="ttl")
                nfo = row.find("td", class_="nfo")
                if nfo:
                    val = ' '.join(nfo.text.strip().split())
                    key = nfo.get(
                        "data-spec") or (ttl.text.strip() if ttl else None)
                    if key:
                        target = categories[current_cat]
                        if key in target:
                            if isinstance(target[key], list):
                                target[key].append(val)
                            else:
                                target[key] = [target[key], val]
                        else:
                            target[key] = val
        data.update(categories)
        return data
    except:
        return None


def load_json():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data, set(i["Phone Name"] for i in data)
        except:
            return [], set()
    return [], set()


def save_json(data):
    try:
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass


def main():
    all_data, seen = load_json()
    links = get_links()
    if not links:
        return
    new = 0
    for link in tqdm(links, desc="Scraping phones", unit="phone"):
        url = urljoin(BASE_URL, link)
        phone = scrape_phone(url)
        if phone and phone["Phone Name"] not in seen:
            all_data.append(phone)
            seen.add(phone["Phone Name"])
            new += 1
        time.sleep(random.uniform(0.5, 1.5))
    save_json(all_data)
    print(f"Scraped: {len(all_data)} | New: {new}")


if __name__ == "__main__":
    main()
