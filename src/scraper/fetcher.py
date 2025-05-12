import aiohttp
import asyncio
import sys
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm.asyncio import tqdm_asyncio
from config.settings import BASE_URL, SEARCH_URLS, MAX_CONCURRENT_REQUESTS
from scraper.parser import parse_specs

BASE_URL = "https://www.gsmarena.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

async def get_phone_links(session, url):
    try:
        async with session.get(url, headers=HEADERS, timeout=10) as response:
            # Exit the code immediately if 'Rate limited' is encountered
            if response.status == 429:
                print(f"Rate limited at {url}.")
                from data.loader import load_data
                phones, seen = load_data()
                print(f"Total phones in JSON file: {len(phones)}")
                new_scraped_count = len([phone for phone in phones if phone["Phone Name"] not in seen])
                print(f"Total scraped phones: {new_scraped_count}")
                print(f"Total skipped phones: 0")
                print("Exiting...")
                sys.exit(1)
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
        async with session.get(url, headers=HEADERS, timeout=10) as response:
            # Exit the code immediately if 'Rate limited' is encountered
            if response.status == 429:
                print(f"Rate limited at {url}.")
                # Print summary before exiting
                from data.loader import load_data
                phones, seen = load_data()
                print(f"Total phones in JSON file: {len(phones)}")
                # Adjusted 'Total scraped phones' to reflect phones scraped in the current run
                new_scraped_count = len([phone for phone in phones if phone["Phone Name"] not in seen])
                print(f"Total scraped phones: {new_scraped_count}")
                # Since we're being rate limited during scraping, show how many phones we've attempted to scrape
                print(f"Total skipped phones: 0")
                print("Exiting...")
                sys.exit(1)
            text = await response.text()
            soup = BeautifulSoup(text, "html.parser")
            name_element = soup.find("h1", class_="specs-phone-name-title")
            specs_element = soup.find("div", id="specs-list")
            if not name_element or not specs_element:
                print(f"No name or specs found for {url}")
                return None
            data = {"Phone Name": name_element.text.strip()}
            data.update(parse_specs(specs_element))
            return data
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

async def scrape():
    from data.loader import load_data, save_data
    phones, seen = load_data()
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        try:
            all_links = []
            for url in SEARCH_URLS:
                links = await get_phone_links(session, url)
                all_links.extend(links)
            if not all_links:
                print("No phone links found across all URLs")
                # Ensure 'Total skipped phones' reflects only skipped phones during actual scraping attempts
                print("Total skipped phones: 0")
                return
            unique_links = list(dict.fromkeys(all_links))
            tasks = [scrape_phone(session, url) for url in unique_links]
            results = await tqdm_asyncio.gather(*tasks, desc="Scraping phones")
            for phone in results:
                if phone and phone["Phone Name"] not in seen:
                    phones.append(phone)
                    seen.add(phone["Phone Name"])
                    save_data(phones)
            # Ensure 'Total skipped phones' reflects only skipped phones during actual scraping attempts
            if not results:  # If no scraping results due to rate limiting
                print("Total skipped phones: 0")
            else:
                skipped_count = len([phone for phone in seen if phone in [result["Phone Name"] for result in results if result]])
                print(f"Total skipped phones: {skipped_count}")
        except RuntimeError as e:
            raise