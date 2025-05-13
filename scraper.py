import json
import os
import random
import time
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

BASE_URL = "https://www.gsmarena.com"
JSON_FILE = "phone_specs.json"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Firefox/117.0",
]
DELAY_RANGE = (0.5, 2.0)

SEARCH_URLS = [
    "https://www.gsmarena.com/results.php3?nPriceMin=900&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=700&nPriceMax=900&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=600&nPriceMax=700&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=450&nPriceMax=600&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=350&nPriceMax=450&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=300&nPriceMax=350&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=250&nPriceMax=300&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=200&nPriceMax=250&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nYearMin=2022&nPriceMin=150&nPriceMax=200&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nYearMax=2022&nPriceMin=150&nPriceMax=200&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMax=150&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1"
]


def get_random_headers():
    return {"User-Agent": random.choice(USER_AGENTS)}


def extract_specs(specs_element):
    specs = {}
    for table in specs_element.find_all("table"):
        category = table.find("th").text.strip()
        specs[category] = {}
        for row in table.find_all("tr")[1:]:
            title = row.find("td", class_="ttl")
            value = row.find("td", class_="nfo")
            if title and value:
                key = title.text.strip()
                specs[category][key] = value.text.strip()
    return specs


def get_phone_links(url):
    try:
        time.sleep(random.uniform(*DELAY_RANGE))
        response = requests.get(url, headers=get_random_headers(), timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return [urljoin(BASE_URL, a["href"]) for a in soup.select("div.makers a[href]")]
    except requests.RequestException:
        return []


def scrape_phone(url):
    try:
        time.sleep(random.uniform(*DELAY_RANGE))
        response = requests.get(url, headers=get_random_headers(), timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        name = soup.find("h1", class_="specs-phone-name-title")
        specs = soup.find("div", id="specs-list")
        if not (name and specs):
            return None

        return {"Phone Name": name.text.strip(), **extract_specs(specs)}
    except requests.RequestException:
        return None


def load_json():
    try:
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data, {item["Phone Name"] for item in data}
    except:
        pass
    return [], set()


def save_json(data):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    data, seen_phones = load_json()
    phone_links = []
    for url in SEARCH_URLS:
        phone_links.extend(get_phone_links(url))

    with tqdm(phone_links, desc="Scraping phones") as pbar:
        for url in pbar:
            phone_data = scrape_phone(url)
            if phone_data and phone_data["Phone Name"] not in seen_phones:
                data.append(phone_data)
                seen_phones.add(phone_data["Phone Name"])
                save_json(data)


if __name__ == "__main__":
    main()
