from bs4 import BeautifulSoup
import requests
import json
import os
import time
import random
from urllib.parse import urljoin
from tqdm import tqdm

# Constants
BASE_URL = "https://www.gsmarena.com"
SEARCH_URL = f"{BASE_URL}/results.php3?nYearMin=2020&nDisplayResMin=2073600&chkReview=selected&sAvailabilities=1&idOS=2&sChipset=158,125,143,116,115,104,144,140,154,124,123,114,156,145,141,142,155,122,92,77,79,57,42,80,41,31,27,1,2,3,120,81,91,62,43,82,83,46,36,58,48,29,105,78,127,106,35,33,44,90,4,5,45,28,59,6,7,89,61,8,34,9,10,60,11,88,163,162,118,84,161,160,109,102,73,74,75,85,37,38,32,47,39,12,13,49,40,14,15,16,157,150,126,117,108,159,164,128,147,129,112,130,131,110,153,148,132,137,133,138,146,134,135,139,113,98,99,121,69,111,100,70,107,71,72,101,152,119,97,96,149,54,95,68,151,94,67,93,76,51,52,53,66,20,21,65,22,23,64,17,18,19,103,86,50,87,30,24,25,55,56,63,26"
JSON_FILE = "phone_specs.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
# Rate limiting constants
MIN_DELAY = 0.5
MAX_DELAY = 1.5


def get_links():
    """
    Fetch all phone links from the search results page.
    
    Returns:
        list: List of URLs for phone detail pages or empty list if request fails
    """
    try:
        response = requests.get(SEARCH_URL, headers=HEADERS, timeout=10)
        
        # Check specifically for 429 status code
        if response.status_code == 429:
            print(f"Error fetching search results: 429 Client Error: Too Many Requests")
            print("Rate limit detected. Exiting program.")
            exit(1)  # Exit the program with error code
            
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        # Extract all phone links from the makers div
        return [
            a["href"] 
            for div in soup.find_all("div", class_="makers") 
            for a in div.find_all("a", href=True)
        ]
    except requests.RequestException as e:
        # Check if the exception is due to rate limiting
        if "429" in str(e):
            print(f"Error fetching search results: {e}")
            print("Rate limit detected. Exiting program.")
            exit(1)  # Exit the program with error code
        print(f"Error fetching search results: {e}")
        return []


def extract_specs_data(specs_element):
    """
    Extract specifications from the specs element.
    
    Args:
        specs_element: BeautifulSoup element containing the specifications
    
    Returns:
        dict: Categorized phone specifications
    """
    categories = {}
    current_category = None
    
    for table in specs_element.find_all("table"):
        for row in table.find_all("tr"):
            # Check if this row defines a new category
            category_header = row.find("th")
            if category_header and category_header.get("rowspan"):
                current_category = category_header.text.strip()
                categories[current_category] = categories.get(current_category, {})
                
            # Extract specification details
            title_cell = row.find("td", class_="ttl")
            value_cell = row.find("td", class_="nfo")
            
            if value_cell:
                # Clean up the text value
                value = ' '.join(value_cell.text.strip().split())
                # Use data-spec attribute as key if available, otherwise use the title text
                key = value_cell.get("data-spec") or (title_cell.text.strip() if title_cell else None)
                
                if key and current_category:
                    target = categories[current_category]
                    # Handle multiple values for the same key
                    if key in target:
                        if isinstance(target[key], list):
                            target[key].append(value)
                        else:
                            target[key] = [target[key], value]
                    else:
                        target[key] = value
    
    return categories


def scrape_phone(url):
    """
    Scrape detailed specifications for a single phone.
    
    Args:
        url (str): URL of the phone's page
        
    Returns:
        dict: Phone specifications or None if scraping fails
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        # Check specifically for 429 status code
        if response.status_code == 429:
            print(f"Error scraping phone at {url}: 429 Client Error: Too Many Requests")
            print("Rate limit detected. Exiting program.")
            exit(1)  # Exit the program with error code
            
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Get phone name
        name_element = soup.find("h1", class_="specs-phone-name-title")
        if not name_element:
            return None
            
        # Get specifications list
        specs_element = soup.find("div", id="specs-list")
        if not specs_element:
            return None
            
        # Create the base data with the phone name
        data = {"Phone Name": name_element.text.strip()}
        
        # Extract all specifications
        categories = extract_specs_data(specs_element)
        
        # Merge specifications with base data
        data.update(categories)
        return data
        
    except requests.RequestException as e:
        # Check if the exception is due to rate limiting
        if "429" in str(e):
            print(f"Error scraping phone at {url}: {e}")
            print("Rate limit detected. Exiting program.")
            exit(1)  # Exit the program with error code
        print(f"Error scraping phone at {url}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error while scraping {url}: {e}")
        return None


def load_json():
    """
    Load existing phone data from JSON file.
    
    Returns:
        tuple: (list of phone data, set of existing phone names)
    """
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Create a set of existing phone names for fast lookup
                existing_phones = set(item["Phone Name"] for item in data)
                return data, existing_phones
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading existing data: {e}")
            return [], set()
    return [], set()


def save_json(data):
    """
    Save phone data to JSON file.
    
    Args:
        data (list): List of phone specification dictionaries
    """
    try:
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Data successfully saved to {JSON_FILE}")
    except IOError as e:
        print(f"Error saving data: {e}")


def main():
    """Main function to orchestrate the scraping process."""
    # Load existing data
    all_data, seen_phones = load_json()
    print(f"Loaded {len(all_data)} existing phone records")
    
    # Get all phone links
    links = get_links()
    if not links:
        print("No phone links found. Exiting.")
        return
    
    print(f"Found {len(links)} phones to process")
    new_count = 0
    
    # Process each phone link
    for link in tqdm(links, desc="Scraping phones", unit="phone"):
        full_url = urljoin(BASE_URL, link)
        phone_data = scrape_phone(full_url)
        
        # Add new phone if it doesn't exist
        if phone_data and phone_data["Phone Name"] not in seen_phones:
            all_data.append(phone_data)
            seen_phones.add(phone_data["Phone Name"])
            new_count += 1
            
        # Respect the website by adding a delay between requests
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
    
    # Save results
    save_json(all_data)
    print(f"Scraping complete. Total phones: {len(all_data)} | Newly added: {new_count}")


if __name__ == "__main__":
    main()
