from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import json


def get_phone_maker_links():
    url = "https://www.gsmarena.com/results.php3?nYearMin=2024&nDisplayResMin=2073600&sAvailabilities=1&idOS=2&sChipset=158,125,143,116,115,104,144,140,154,124,123,114,156,145,141,142,155,122,92,77,79,57,42,80,41,31,27,1,2,3,120,81,91,62,43,82,83,46,36,58,48,29,105,78,127,106,35,33,44,90,4,5,45,28,59,6,7,89,61,8,34,9,10,60,11,88,163,162,118,84,161,160,109,102,73,74,75,85,37,38,32,47,39,12,13,49,40,14,15,16,157,150,126,117,108,159,164,128,147,129,112,130,131,110,153,148,132,137,133,138,146,134,135,139,113,98,99,121,69,111,100,70,107,71,72,101,152,119,97,96,149,54,95,68,151,94,67,93,76,51,52,53,66,20,21,65,22,23,64,17,18,19,103,86,50,87,30,24,25,55,56,63,26&sFingerprints=1"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    makers_div = soup.find_all("div", class_="makers")
    links = []
    for div in makers_div:
        for link in div.find_all("a", href=True):
            links.append(link["href"])
    return links


def scrape_phone_specs(url):
    phone_data = {}
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.find("h1", class_="specs-phone-name-title")
    phone_name = title.get_text(strip=True) if title else "Unknown"
    phone_data["Phone Name"] = phone_name
    specs_list_div = soup.find("div", id="specs-list")
    if specs_list_div:
        tables = specs_list_div.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                columns = row.find_all("td")
                if len(columns) > 1:
                    key = columns[0].get_text(strip=True)
                    value = columns[1].get_text(strip=True)
                    phone_data[key] = value
    return phone_data


def save_to_json(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    phone_maker_links = get_phone_maker_links()
    all_phone_specs = []

    for link in phone_maker_links:
        full_url = urljoin("https://www.gsmarena.com", link)
        print(f"Scraping {full_url}")

        phone_specs = scrape_phone_specs(full_url)
        if phone_specs:
            all_phone_specs.append(phone_specs)

        print("\n" + "=" * 50 + "\n")

        user_input = (
            input("Do you want to scrape the next phone specs? (y/n): ").strip().lower()
        )
        if user_input != "y":
            print("\nExiting scraper. Goodbye!")
            break
        else:
            print("\nContinuing to the next phone...\n")

    save_to_json(all_phone_specs, "phone_specs.json")
