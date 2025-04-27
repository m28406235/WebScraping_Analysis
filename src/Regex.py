import re
import requests
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def get_processed_phone_data():
    df = pd.read_json("phone_specs.json")
    specs = {col.lower().replace(" ", "_"): pd.json_normalize(df[col]) if isinstance(df[col][0], (dict, list)) else pd.DataFrame(df[col]) for col in df.columns}

    rates = {k: 1/v for k, v in requests.get("https://open.er-api.com/v6/latest/USD").json()["rates"].items()}
    symbol_map = {'$': 'USD', '€': 'EUR', '£': 'GBP', '₹': 'INR'}

    def to_usd(x):
        m = re.search(r'([\$€£₹])?\s?([\d,]+(?:\.\d{2})?)\s?(USD|EUR|GBP|INR)?', str(x))
        if m: return round(float(m.group(2).replace(',', '')) * rates.get(symbol_map.get(m.group(1), m.group(3)), 1), 2)

    data = pd.DataFrame({
        "phone_name": specs["phone_name"].squeeze(),
        "chipset": specs["platform"]["chipset"].apply(lambda x: ", ".join(i.split(" (")[0].strip() for i in x) if isinstance(x, list) else x.split(" (")[0].strip() if isinstance(x, str) else x),
        "battery_capacity": specs["battery"]["batdescription1"].str.extract(r"(\d+)")[0].fillna(0).astype(int),
        "charging_speed": specs["battery"]["Charging"].str.extract(r"(\d+)")[0].fillna(0).astype(int),
        "price": specs["misc"]["price"].apply(to_usd),
        "antutu_score": specs["tests"]["tbench"].str.extract(r"AnTuTu:\s*(\d+)")[0].fillna(0).astype(int),
        "display_type": specs["display"]["displaytype"].str.strip().str.split(",").apply(lambda x: ", ".join(i.strip() for i in x) if isinstance(x, list) else x).str.split(",").str[0].str.strip(),
        "refresh_rate": specs["display"]["displaytype"].str.extract(r"(\d+)\s*Hz")[0].astype("Int64"),
        "brightness": specs["tests"]["Display"].str.extract(r"(\d+)\s*nits")[0].combine_first(specs["display"]["displaytype"].str.extract(r"(\d+)\s*nits")[0]).astype("Int64")
    })

    pd.set_option("display.float_format", "{:,.0f}".format)

    data["display_type"] = data["display_type"].apply(lambda x: "OLED-Based" if pd.notna(x) and "OLED" in str(x).upper() else "LCD-Based")
    data["antutu_score"] = pd.to_numeric(data["antutu_score"], errors="coerce").fillna(data.groupby("chipset")["antutu_score"].transform("mean")).astype("Int64")

    q1, q3 = data['price'].quantile([0.25, 0.75])
    filtered_data = data[data['price'].between(q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1))]

    prices = filtered_data['price'].values.reshape(-1, 1)
    clusters = KMeans(n_clusters=3, random_state=42).fit_predict(StandardScaler().fit_transform(prices))

    filtered_data['phone_tier'] = clusters
    data = data.merge(filtered_data[['phone_tier']], left_index=True, right_index=True, how='left')
    data['phone_tier'] = data['phone_tier'].fillna(-1).astype(int)

    cluster_means = data[data['phone_tier'] != -1].groupby('phone_tier')['price'].mean().sort_values()
    cluster_map = {c: ['Budget', 'Mid-Range', 'Premium'][i] for i, c in enumerate(cluster_means.index)}
    cluster_map[-1] = 'Flagship'
    data['phone_tier'] = data['phone_tier'].map(cluster_map)

    return data