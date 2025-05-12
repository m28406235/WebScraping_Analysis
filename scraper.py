import aiohttp
import asyncio
import json
import os
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm_asyncio
from urllib.parse import urljoin

BASE_URL = "https://www.gsmarena.com"
JSON_FILE = "phone_specs.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

search_urls = [
    "https://www.gsmarena.com/results.php3?nPriceMin=900&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=700&nPriceMax=900&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=600&nPriceMax=700&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=500&nPriceMax=600&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=400&nPriceMax=500&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=350&nPriceMax=400&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=300&nPriceMax=350&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=250&nPriceMax=300&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=200&nPriceMax=250&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nYearMin=2023&nPriceMin=150&nPriceMax=200&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nYearMax=2023&nPriceMin=150&nPriceMax=200&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMax=150&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1"
]


def extract_specs_data(specs_element):
    categories = {}
    current_category = None
    for table in specs_element.find_all("table"):
        for row in table.find_all("tr"):
            category_header = row.find("th")
            if category_header and category_header.get("rowspan"):
                current_category = category_header.text.strip()
                categories[current_category] = {}

            title_cell = row.find("td", class_="ttl")
            value_cell = row.find("td", class_="nfo")

            if value_cell:
                value = ' '.join(value_cell.text.strip().split())
                key = value_cell.get(
                    "data-spec") or (title_cell.text.strip() if title_cell else None)
                if key and current_category:
                    target = categories[current_category]
                    if key in target:
                        if isinstance(target[key], list):
                            target[key].append(value)
                        else:
                            target[key] = [target[key], value]
                    else:
                        target[key] = value
    return categories


async def get_phone_links(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 429:
                print(f"Rate limited at {url}")
                return []
            text = await response.text()
            soup = BeautifulSoup(text, "html.parser")
            return [urljoin(BASE_URL, a["href"])
                    for div in soup.find_all("div", class_="makers")
                    for a in div.find_all("a", href=True)]
    except Exception as e:
        print(f"Error fetching links from {url}: {e}")
        return []


async def scrape_phone(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 429:
                print(f"Rate limited at {url}")
                return None
            text = await response.text()
            soup = BeautifulSoup(text, "html.parser")
            name_element = soup.find("h1", class_="specs-phone-name-title")
            specs_element = soup.find("div", id="specs-list")
            if not name_element or not specs_element:
                return None
            data = {"Phone Name": name_element.text.strip()}
            data.update(extract_specs_data(specs_element))
            return data
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None


def load_json():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                existing = set(item["Phone Name"] for item in data)
                return data, existing
        except:
            return [], set()
    return [], set()


def save_json(data):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved to {JSON_FILE}")


async def scrape_search_url(session, search_url, all_data, seen_phones):
    phone_links = await get_phone_links(session, search_url)
    print(f"Found {len(phone_links)} phone links in {search_url}.")

    scrape_tasks = [scrape_phone(session, url) for url in phone_links]
    results = await tqdm_asyncio.gather(*scrape_tasks, desc="Scraping phones", unit="phone")

    new_count = 0
    for phone_data in results:
        if phone_data and phone_data["Phone Name"] not in seen_phones:
            all_data.append(phone_data)
            seen_phones.add(phone_data["Phone Name"])
            new_count += 1

    return new_count


async def main():
    all_data, seen_phones = load_json()
    print(f"Loaded {len(all_data)} existing phones.")

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        new_total = 0
        for search_url in search_urls:
            print(f"Processing {search_url}...")
            new_count = await scrape_search_url(session, search_url, all_data, seen_phones)
            new_total += new_count
            print(f"New phones added from this search URL: {new_count}")

    save_json(all_data)
    print(f"Done. Total phones: {len(all_data)} | Newly added: {new_total}")

if __name__ == "__main__":
    asyncio.run(main())

search_urls = [
    "https://www.gsmarena.com/results.php3?nPriceMin=900&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=700&nPriceMax=900&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=600&nPriceMax=700&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=500&nPriceMax=600&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=400&nPriceMax=500&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=350&nPriceMax=400&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=300&nPriceMax=350&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=250&nPriceMax=300&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMin=200&nPriceMax=250&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nYearMin=2023&nPriceMin=150&nPriceMax=200&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nYearMax=2023&nPriceMin=150&nPriceMax=200&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1",
    "https://www.gsmarena.com/results.php3?nPriceMax=150&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1"
]


def extract_specs_data(specs_element):
    categories = {}
    current_category = None
    for table in specs_element.find_all("table"):
        for row in table.find_all("tr"):
            category_header = row.find("th")
            if category_header and category_header.get("rowspan"):
                current_category = category_header.text.strip()
                categories[current_category] = {}

            title_cell = row.find("td", class_="ttl")
            value_cell = row.find("td", class_="nfo")

            if value_cell:
                value = ' '.join(value_cell.text.strip().split())
                key = value_cell.get(
                    "data-spec") or (title_cell.text.strip() if title_cell else None)
                if key and current_category:
                    target = categories[current_category]
                    if key in target:
                        if isinstance(target[key], list):
                            target[key].append(value)
                        else:
                            target[key] = [target[key], value]
                    else:
                        target[key] = value
    return categories


async def get_phone_links(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 429:
                print(f"Rate limited at {url}")
                return []
            text = await response.text()
            soup = BeautifulSoup(text, "html.parser")
            return [urljoin(BASE_URL, a["href"])
                    for div in soup.find_all("div", class_="makers")
                    for a in div.find_all("a", href=True)]
    except Exception as e:
        print(f"Error fetching links from {url}: {e}")
        return []


async def scrape_phone(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 429:
                print(f"Rate limited at {url}")
                return None
            text = await response.text()
            soup = BeautifulSoup(text, "html.parser")
            name_element = soup.find("h1", class_="specs-phone-name-title")
            specs_element = soup.find("div", id="specs-list")
            if not name_element or not specs_element:
                return None
            data = {"Phone Name": name_element.text.strip()}
            data.update(extract_specs_data(specs_element))
            return data
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None


def load_json():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                existing = set(item["Phone Name"] for item in data)
                return data, existing
        except:
            return [], set()
    return [], set()


def save_json(data):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved to {JSON_FILE}")


async def scrape_search_url(session, search_url, all_data, seen_phones):
    phone_links = await get_phone_links(session, search_url)
    print(f"Found {len(phone_links)} phone links in {search_url}.")

    scrape_tasks = [scrape_phone(session, url) for url in phone_links]
    results = await tqdm_asyncio.gather(*scrape_tasks, desc="Scraping phones", unit="phone")

    new_count = 0
    for phone_data in results:
        if phone_data and phone_data["Phone Name"] not in seen_phones:
            all_data.append(phone_data)
            seen_phones.add(phone_data["Phone Name"])
            new_count += 1

    return new_count


async def main():
    all_data, seen_phones = load_json()
    print(f"Loaded {len(all_data)} existing phones.")

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        new_total = 0
        for search_url in search_urls:
            print(f"Processing {search_url}...")
            new_count = await scrape_search_url(session, search_url, all_data, seen_phones)
            new_total += new_count
            print(f"New phones added from this search URL: {new_count}")

    save_json(all_data)
    print(f"Done. Total phones: {len(all_data)} | Newly added: {new_total}")

if __name__ == "__main__":
    asyncio.run(main())
