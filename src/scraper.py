from bs4 import BeautifulSoup
import requests, json, os, time, random, sys
from urllib.parse import urljoin
from tqdm import tqdm

BASE_URL = "https://www.gsmarena.com"
SEARCH_URL = f"{BASE_URL}//results.php3?nYearMin=2024&nYearMax=2024&nPriceMax=200&nDisplayResMin=2073600&sAvailabilities=1&idOS=2&sChipset=158,125,143,116,115,104,144,140,154,124,123,114,156,145,141,142,155,122,92,77,79,57,42,80,41,31,27,1,2,3,120,81,91,62,43,82,83,46,36,58,48,29,105,78,127,106,35,33,44,90,4,5,45,28,59,6,7,89,61,8,34,9,10,60,11,88,157,150,126,117,108,159,164,128,147,129,112,130,131,110,153,148,132,137,133,138,146,134,135,139,113,98,99,121,69,111,100,70,107,71,72,101"
JSON_FILE = "phone_specs.json"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_links():
    try:
        r = requests.get(SEARCH_URL, headers=HEADERS)
        s = BeautifulSoup(r.text, "html.parser")
        return [a["href"] for d in s.find_all("div", class_="makers") for a in d.find_all("a", href=True)]
    except: return []

def scrape_phone(url):
    try:
        r = requests.get(url, headers=HEADERS)
        s = BeautifulSoup(r.text, "html.parser")
        name = s.find("h1", class_="specs-phone-name-title")
        if not name: return None
        specs = s.find("div", id="specs-list")
        if not specs: return None
        data = {"Phone Name": name.text.strip(), "URL": url, "Specifications": {}}
        cat = None
        for t in specs.find_all("table"):
            for row in t.find_all("tr"):
                th = row.find("th")
                if th and th.get("rowspan"):
                    cat = th.text.strip()
                    data["Specifications"].setdefault(cat, {})
                if not cat: continue
                ttl = row.find("td", class_="ttl")
                nfo = row.find("td", class_="nfo")
                if nfo:
                    val = ' '.join(nfo.text.strip().split())
                    key = nfo.get("data-spec") if nfo.has_attr("data-spec") else ttl.text.strip() if ttl else None
                    if not key: continue
                    specs_cat = data["Specifications"][cat]
                    if key in specs_cat:
                        if isinstance(specs_cat[key], list): specs_cat[key].append(val)
                        else: specs_cat[key] = [specs_cat[key], val]
                    else: specs_cat[key] = val
        return data
    except: return None

def load_json():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                return d, set(i["Phone Name"] for i in d)
        except: pass
    return [], set()

def save_json(data):
    try:
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except: pass

def main():
    all_data, seen = load_json()
    links = get_links()
    if not links: sys.exit("No links found.")
    new = 0
    for link in tqdm(links, desc="Scraping phones", unit="phone"):
        url = urljoin(BASE_URL, link)
        phone = scrape_phone(url)
        if not phone: sys.exit(f"Failed to scrape: {url}")
        if phone["Phone Name"] not in seen:
            all_data.append(phone)
            seen.add(phone["Phone Name"])
            new += 1
            if new % 5 == 0: save_json(all_data)
        time.sleep(1 + random.uniform(0, 1))
    save_json(all_data)
    print(f"Scraped: {len(all_data)} | New: {new}")

if __name__ == "__main__":
    main()