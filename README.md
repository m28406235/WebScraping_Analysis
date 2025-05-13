**README for Phone Data Project**

This README provides a deep, line-by-line explanation of each of the five Python files in this project:

1. **data\_processing.py**
2. **mongo\_insert.py**
3. **utils.py**
4. **app.py** (Streamlit visualization)
5. **scraper.py**

---

## 1. data\_processing.py

```python
import pandas as pd
```

1. Imports the pandas library under the alias `pd` to handle DataFrame structures and data manipulation.

```python
from sklearn.impute import KNNImputer
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.cluster import KMeans
```

2–4. Pulls in Scikit-Learn modules for:

* `KNNImputer`: fills missing values via k-nearest neighbors.
* `LabelEncoder`: encodes categorical labels as integers.
* `StandardScaler`: standardizes features by removing the mean and scaling to unit variance.
* `KMeans`: clustering algorithm to segment phone prices into tiers.

```python
from Regex import to_usd, extract_numeric_value, extract_antutu_score, extract_display_type, extract_brightness, extract_chipset_info
```

5. Imports custom parsing functions from `Regex.py`:

   * `to_usd`: converts various currency formats to USD float.
   * `extract_numeric_value`: captures the first numeric occurrence.
   * `extract_antutu_score`: extracts benchmark score.
   * `extract_display_type`: normalizes display type strings.
   * `extract_brightness`: obtains brightness in nits.
   * `extract_chipset_info`: cleans chipset lists/strings.

```python
import os
import warnings
```

6–7. Standard modules to manage environment variables and suppress non-critical warnings.

```python
os.environ["LOKY_MAX_CPU_COUNT"] = "4"
warnings.filterwarnings("ignore", category=UserWarning, module="joblib")
pd.options.mode.chained_assignment = None
```

8–10. Configuration:

* Restricts Loky (joblib's multiprocessing backend) to 4 CPUs.
* Ignores `UserWarning` messages in `joblib` operations.
* Disables pandas’ chained-assignment warnings for cleaner output.

```python
def get_processed_phone_data():
```

11. Defines the main function to read raw JSON, parse fields, clean, impute, cluster, and return a processed DataFrame.

```python
    df = pd.read_json("phone_specs.json")
```

12. Loads scraped phone specs from JSON into a pandas DataFrame.

```python
    specs = {
        col.lower().replace(" ", "_"):
        (pd.json_normalize(df[col]) if isinstance(df[col][0], (dict, list))
         else pd.DataFrame(df[col]))
        for col in df.columns
    }
```

13–17. **Normalization:** Iterates over each column in the raw DataFrame:

* Renames to lowercase and underscores.
* If the column entries are nested (`dict` or `list`), flattens them via `json_normalize`.
* Otherwise, turns each column into its own DataFrame.

```python
    data = pd.DataFrame({
        "phone_name": specs["phone_name"].squeeze(),
        "chipset": extract_chipset_info(specs["platform"]["chipset"]),
        "battery_capacity": extract_numeric_value(specs["battery"]["batdescription1"]),
        "charging_speed": extract_numeric_value(specs["battery"]["Charging"]),
        "price": specs["misc"]["price"].apply(to_usd),
        "antutu_score": extract_antutu_score(specs["tests"]["tbench"]),
        "display_type": extract_display_type(specs["display"]["displaytype"]),
        "refresh_rate": specs["display"]["displaytype"].str.extract(r"(\d+)\s*Hz")[0].astype("Int64"),
        "brightness": extract_brightness(specs)
    })
```

18–26. Builds a new DataFrame `data` with selected, cleaned columns:

* Applies extraction functions for chipset, battery, charging, price, Antutu, display, refresh rate, brightness.

```python
    pd.set_option("display.float_format", "{:,.0f}".format)
```

27. Configures pandas to display floats without decimal places by default.

```python
    data["display_type"] = data["display_type"].apply(
        lambda x: "OLED-Based" if pd.notna(x) and "OLED" in str(x).upper() else "LCD-Based"
    )
```

28–31. Standardizes display types into two categories based on presence of "OLED".

```python
    data = assign_phone_tiers(data)
```

32. Calls helper function to assign "Budget", "Mid-Range", "Premium", or "Flagship" tiers via clustering.

```python
    data['price'] = data.groupby('phone_tier')['price'].transform(lambda x: x.fillna(x.mean()))
```

33. Fills missing `price` values with the mean price of their tier.

```python
    data['refresh_rate'] = data['refresh_rate'].fillna(data['refresh_rate'].mode()[0])
```

34. Imputes missing refresh rates with the most common value across all phones.

```python
    data['brightness'] = data['brightness'].astype('float')
    data['brightness'] = data.groupby('display_type')['brightness'].transform(lambda x: x.fillna(x.mean()))
```

35–36. Ensures brightness is numeric, then fills missing per display type average.

```python
    data["antutu_score"] = pd.to_numeric(data["antutu_score"], errors="coerce")
    data["antutu_score"] = data["antutu_score"].fillna(
        data.groupby("chipset")["antutu_score"].transform("mean")
    ).astype("Int64")
    data["antutu_score"] = data["antutu_score"].replace(0, pd.NA)
```

37–40. Parses Antutu to numeric, fills missing by chipset mean, casts to nullable integer, and drops zero placeholders.

```python
    encoder = LabelEncoder()
    data["phone_tier_encoded"] = encoder.fit_transform(data["phone_tier"])
```

41–42. Encodes textual tiers into numeric for KNN imputation.

```python
    features = ["price", "phone_tier_encoded", "antutu_score"]
    knn_imputer = KNNImputer(n_neighbors=5)
    imputed_data = knn_imputer.fit_transform(data[features])
```

43–45. Applies KNN-based imputation on selected features to refine Antutu scores.

```python
    data["antutu_score"] = imputed_data[:, 2]
    data["antutu_score"] = data["antutu_score"].astype(int)
    data = data.drop(columns=["phone_tier_encoded"])
```

46–48. Replaces Antutu column with imputed results, casts back to int, and removes temporary encoding.

```python
    return data
```

49. Returns the fully processed DataFrame.

---

### Helper Function: assign\_phone\_tiers(data)

```python
def assign_phone_tiers(data):
```

50. Defines function to segment phones into tiers via clustering.

```python
    q1, q3 = data['price'].quantile([0.25, 0.75])
    iqr = q3 - q1
    filtered_data = data[data['price'].between(q1 - 1.5 * iqr, q3 + 1.5 * iqr)]
```

51–53. Computes IQR-based bounds to exclude outliers for clustering.

```python
    prices = filtered_data['price'].values.reshape(-1, 1)
    scaled_prices = StandardScaler().fit_transform(prices)
    clusters = KMeans(n_clusters=3, random_state=42).fit_predict(scaled_prices)
    filtered_data['phone_tier'] = clusters
```

54–57. Scales prices, clusters into three groups, and labels them 0–2.

```python
    data = data.merge(filtered_data[['phone_tier']], left_index=True, right_index=True, how='left')
    data['phone_tier'] = data['phone_tier'].fillna(-1).astype(int)
```

58–59. Merges tier labels back to the full dataset; marks outliers as `-1`.

```python
    cluster_means = data[data['phone_tier'] != -1].groupby('phone_tier')['price'].mean().sort_values()
    cluster_map = {c: ['Budget', 'Mid-Range', 'Premium'][i] for i, c in enumerate(cluster_means.index)}
    cluster_map[-1] = 'Flagship'
    data['phone_tier'] = data['phone_tier'].map(cluster_map)
```

60–63. Maps numeric clusters to descriptive names; outliers become `Flagship`.

```python
    return data
```

64. Returns DataFrame with a `phone_tier` column of descriptive tiers.

---

## 2. mongo\_insert.py

```python
from pymongo import MongoClient
from data_processing import get_processed_phone_data
```

1–2. Imports MongoDB client and the data processing function.

```python
cluster = MongoClient("<CONNECTION_STRING>")
db = cluster["Web_Scraping"]
collection = db["Phones"]
```

3–5. Establishes connection to MongoDB Atlas, selects the `Web_Scraping` database and `Phones` collection.

```python
phone_data = get_processed_phone_data()
print(phone_data.isnull().sum())
```

6–7. Retrieves processed DataFrame and logs counts of nulls per column for confirmation.

```python
phone_data_dict = phone_data.to_dict(orient="records")
```

8. Converts DataFrame into a list of dictionaries, ready for MongoDB insertion.

```python
try:
    collection.insert_many(phone_data_dict)
    print("Data inserted successfully into MongoDB!")
except Exception as e:
    print(f"An error occurred: {e}")
```

9–13. Attempts bulk insert; prints success message or error details.

---

## 3. utils.py

```python
import re
import requests
```

1–2. Imports the regular expressions module and `requests` for HTTP calls.

```python
def to_usd(price_string):
    rates = {k: 1 / v for k, v in requests.get("https://open.er-api.com/v6/latest/USD").json()["rates"].items()}
    symbol_map = {'$': 'USD', '€': 'EUR', '£': 'GBP', '₹': 'INR'}
    pattern = r'([\$€£₹])?\s?([\d,]+(?:\.\d{2})?)\s?(USD|EUR|GBP|INR)?'
    match = re.search(pattern, str(price_string))
    if not match:
        return None
    amount = float(match.group(2).replace(',', ''))
    symbol = match.group(1)
    code = match.group(3)
    currency = symbol_map.get(symbol, code)
    return round(amount * rates.get(currency, 1), 2)
```

3–16. Fetches live USD exchange rates and converts various currency formats (symbol or code) into a USD float.

```python
def extract_numeric_value(series):
    return series.str.extract(r"(\d+)")[0].fillna(0).astype(int)
```

17–19. Extracts first integer from a pandas Series of strings, fills missing with zero.

```python
def extract_antutu_score(bench_series):
    return bench_series.str.extract(r"AnTuTu:\s*(\d+)")[0].fillna(0).astype(int)
```

20–22. Parses out Antutu benchmark values from text (e.g., "AnTuTu: 450000").

```python
def extract_display_type(display_series):
    return (display_series.str.strip()
            .str.split(",")
            .apply(lambda x: ", ".join(i.strip() for i in x) if isinstance(x, list) else x)
            .str.split(",")
            .str[0]
            .str.strip())
```

23–29. Normalizes display type strings by:

* Stripping whitespace.
* Splitting on commas, rejoining lists.
* Taking the first type option.

```python
def extract_brightness(specs):
    from_tests = specs["tests"]["Display"].str.extract(r"(\d+)\s*nits")[0]
    from_display = specs["display"]["displaytype"].str.extract(r"(\d+)\s*nits")[0]
    return from_tests.combine_first(from_display).astype("Int64")
```

30–34. Retrieves brightness from test results or display specs, preferring tests when available.

```python
def extract_chipset_info(chipset_series):
    return chipset_series.apply(
        lambda x: ", ".join(i.split(" (")[0].strip() for i in x) if isinstance(x, list)
        else x.split(" (")[0].strip() if isinstance(x, str) else x
    )
```

35–39. Cleans up chipset entries by removing bracketed details, joining lists.

---

## 4. app.py (Streamlit Visualization)

```python
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
```

1–3. Suppresses future and deprecation warnings for a smooth Streamlit UI.

```python
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
from data_processing import get_processed_phone_data
```

4–9. Imports core libraries for data handling (`pandas`), visualizations (`plotly`, `seaborn`, `matplotlib`), the Streamlit framework, and the processing function.

```python
st.set_page_config(page_title="Phone Data Analysis", layout="wide")
st.title("Phone Data Visualizations")
```

10–11. Configures the Streamlit page and sets the main title.

```python
phone_data = get_processed_phone_data()
```

12. Retrieves processed data for use in charts.

```python
st.markdown("### Phone Data Preview")
st.write(phone_data.head().to_html(index=False), unsafe_allow_html=True)
```

13–14. Displays a preview table of the first five rows.

```python
st.write("Data shape:", phone_data.shape)
st.write("Data types:", phone_data.dtypes.astype(str).to_dict())
st.write("Missing values:", phone_data.isnull().sum().to_dict())
```

15–17. Shows DataFrame dimensions, column types, and null-value counts.

```python
tier_order = ["Budget", "Mid-Range", "Premium", "Flagship"]
phone_data["phone_tier"] = pd.Categorical(phone_data["phone_tier"], categories=tier_order, ordered=True)
```

18–19. Defines consistent ordering for tiers in all plots.

```python
color_map = { ... }
phone_data['text'] = phone_data['phone_name']
```

20–21. Sets custom colors per tier and prepares hover text.

```python
best_phones_idx = phone_data.groupby('phone_tier').apply(
    lambda group: (group['antutu_score'] / group['price']).idxmax()
)
best_phones_data = phone_data.loc[best_phones_idx]
```

22–25. Identifies the "best value" phone in each tier by Antutu-to-price ratio.

*Then follows multiple `plotly.express` charts:*

* **Price vs Antutu Score** (scatter with highlighted best phones)
* **Battery Capacity vs Charging Speed** (bubble chart)
* **Display Type Distribution** (pie)
* **Count per Tier** (bar)
* **Correlation Matrix** (heatmap via seaborn + matplotlib)
* **Top 10 Chipsets by Antutu** (bar)
* **Brightness Comparison by Display Type** (box)

Each block:

1. Defines `fig = px...`
2. Customizes layout/annotations
3. Renders with `st.plotly_chart()` or `st.pyplot()`

---

## 5. scraper.py

```python
import json
import os
import random
import time
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
```

1–7. Imports standard modules for JSON, file operations, randomness, sleeps, URL handling, HTTP, HTML parsing, and progress bars.

```python
BASE_URL = "https://www.gsmarena.com"
JSON_FILE = "phone_specs.json"
USER_AGENTS = [...]
DELAY_RANGE = (0.5, 2.0)
SEARCH_URLS = [ ... ]
```

8–14. Defines constants:

* Base site URL
* Output JSON filename
* A list of user-agent strings for polite scraping
* Delay range between requests
* Query URLs filtering by price, resolution, year

```python
def get_random_headers():
    return {"User-Agent": random.choice(USER_AGENTS)}
```

15–17. Returns a random `User-Agent` header for each request.

```python
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
```

18–27. Parses each category table on a phone-spec page into a nested dict of sections and key–value specs.

```python
def get_phone_links(url):
    try:
        time.sleep(random.uniform(*DELAY_RANGE))
        response = requests.get(url, headers=get_random_headers(), timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return [urljoin(BASE_URL, a["href"]) for a in soup.select("div.makers a[href]")]
    except requests.RequestException:
        return []
```

28–38. Fetches listing pages, extracts individual phone URLs, and handles failures gracefully.

```python
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
```

39–53. Retrieves an individual phone page, parses its name and specs, and returns a combined dict.

```python
def load_json():
    try:
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data, {item["Phone Name"] for item in data}
    except:
        pass
    return [], set()
```

54–62. Loads existing JSON to resume incremental scraping without duplicates.

```python
def save_json(data):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

63–66. Overwrites JSON file with up-to-date list of scraped phone specs.

```python
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
```

67–83. Coordinates full scraping workflow:

1. Loads previous results to avoid repeats.
2. Gathers all phone page URLs from search filters.
3. Iterates with progress bar, scrapes each page, appends new data, and saves incrementally.

---

This README should help any developer or analyst understand exactly what each line in every file is doing, the data flow from scraping to database insertion, and the visualizations presented in the Streamlit app.
