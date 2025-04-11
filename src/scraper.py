from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import json
import os
import time
from requests.exceptions import RequestException
import logging

# Constants
BASE_URL = "https://www.gsmarena.com"
JSON_FILE = "phone_specs.json"
SEARCH_URL = f"{BASE_URL}/results.php3?nYearMin=2024&nDisplayResMin=2073600&sAvailabilities=1&idOS=2&sFingerprints=1"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
REQUEST_TIMEOUT = 10
RETRY_ATTEMPTS = 3
RATE_LIMIT_DELAY = 1

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def get_links():
    """Fetch phone page links from the search results."""
    try:
        response = requests.get(SEARCH_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        links = [a["href"] for div in soup.find_all("div", class_="makers") for a in div.find_all("a", href=True)]
        logger.info(f"Found {len(links)} phone links.")
        return links
    except RequestException as e:
        logger.error(f"Failed to fetch links: {e}")
        return []

def load_existing_specs():
    """Load existing phone specs from JSON file."""
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data, {item["Phone Name"] for item in data}
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error loading JSON: {e}")
    return [], set()

def get_phone_name(url):
    """Fetch only the phone name from a phone's page."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.find("h1", class_="specs-phone-name-title")
        if title:
            phone_name = title.get_text(strip=True).replace("\n", " ").strip()
            logger.debug(f"Extracted phone name: {phone_name} from {url}")
            return phone_name
        logger.warning(f"No phone name found at {url}")
        return None
    except RequestException as e:
        logger.warning(f"Failed to get phone name from {url}: {e}")
        return None

def scrape_phone(url):
    """Scrape specs for a single phone with retries."""
    for attempt in range(RETRY_ATTEMPTS):
        try:
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            if len(response.text) < 2000:
                logger.warning(f"Response too short at {url}. Possible block.")
                return None

            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.find("h1", class_="specs-phone-name-title")
            if not title:
                logger.warning(f"No title found at {url}. Skipping.")
                return None

            data = {"Phone Name": title.get_text(strip=True).replace("\n", " ").strip()}
            specs = soup.find("div", id="specs-list")
            if specs:
                for table in specs.find_all("table"):
                    for row in table.find_all("tr"):
                        cols = row.find_all("td")
                        if len(cols) > 1:
                            key = cols[0].get_text(strip=True).replace("\n", " ").strip()
                            value = cols[1].get_text(strip=True).replace("\n", " ").strip()
                            if key:
                                data[key] = value
            logger.info(f"Successfully scraped {data['Phone Name']}")
            return data

        except RequestException as e:
            logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
            if attempt == RETRY_ATTEMPTS - 1:
                logger.error(f"Max retries reached for {url}. Skipping.")
                return None
        time.sleep(RATE_LIMIT_DELAY)
    return None

def save_json(data):
    """Save phone specs to JSON file."""
    try:
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info(f"Saved {len(data)} phones to {JSON_FILE}")
    except IOError as e:
        logger.error(f"Failed to save JSON: {e}")

if __name__ == "__main__":
    all_specs, existing_names = load_existing_specs()
    links = get_links()
    if not links:
        logger.error("No links found. Exiting.")
        exit(1)

    for i, link in enumerate(links, 1):
        full_url = urljoin(BASE_URL, link)
        logger.info(f"[{i}/{len(links)}] Processing {full_url}")
        
        # First, get the phone name
        phone_name = get_phone_name(full_url)
        if not phone_name:
            logger.info(f"Skipping {full_url} due to missing or invalid phone name")
            continue
        
        # Check if phone was already scraped
        if phone_name in existing_names:
            logger.info(f"Phone {phone_name} already scraped. Skipping full scrape.")
            continue
        
        # Scrape full specs if phone is new
        logger.info(f"Scraping full specs for {phone_name}")
        phone_data = scrape_phone(full_url)
        if phone_data:
            all_specs.append(phone_data)
            existing_names.add(phone_data["Phone Name"])
            logger.info(f"Added {phone_data['Phone Name']} to dataset")
        else:
            logger.info(f"Failed to scrape full specs for {phone_name}. Skipping.")
        
        time.sleep(RATE_LIMIT_DELAY)  # Prevent overwhelming the server

    save_json(all_specs)