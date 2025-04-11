from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import json
import os

BASE_URL = "https://www.gsmarena.com"
JSON_FILE = "phone_specs.json"

def get_phone_links():
    url = BASE_URL + "/results.php3?nYearMin=2024&nDisplayResMin=2073600&sAvailabilities=1&idOS=2&sFingerprints=1"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    return [a["href"] for div in soup.find_all("div", class_="makers") for a in div.find_all("a", href=True)]

def load_existing_specs():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data, {item["Phone Name"] for item in data}
    return [], set()

def scrape_phone(url):
    response = requests.get(url)
    if response.status_code != 200 or len(response.text) < 2000:
        return "blocked"
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.find("h1", class_="specs-phone-name-title")
    if not title:
        return None
    data = {"Phone Name": title.get_text(strip=True)}
    specs = soup.find("div", id="specs-list")
    if specs:
        for table in specs.find_all("table"):
            for row in table.find_all("tr"):
                cols = row.find_all("td")
                if len(cols) > 1:
                    data[cols[0].get_text(strip=True)] = cols[1].get_text(strip=True)
    return data

def save_json(data):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    all_specs, existing_names = load_existing_specs()
    links = get_phone_links()

    for link in links:
        full_url = urljoin(BASE_URL, link)
        print(f"Scraping {full_url}")
        phone_data = scrape_phone(full_url)
        if phone_data == "blocked":
            print("Blocked by site. Saving and exiting.")
            break
        if phone_data and phone_data["Phone Name"] not in existing_names:
            print(f"Saved specs for: {phone_data['Phone Name']}")
            all_specs.append(phone_data)
            existing_names.add(phone_data["Phone Name"])
        else:
            print("Already saved or invalid. Skipping.")

    save_json(all_specs)