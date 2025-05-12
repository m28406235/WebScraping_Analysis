import pandas as pd
import re
import requests
from config.settings import JSON_FILE
from data.tier_assigner import set_tiers

def to_usd(price, rates, symbols):
    match = re.search(r"([\$€£₹])?\s?([\d,]+(?:\.\d{2})?)\s?(USD|EUR|GBP|INR)?", str(price))
    if not match:
        return None
    amount = float(match.group(2).replace(",", ""))
    currency = symbols.get(match.group(1), match.group(3))
    return round(amount * rates.get(currency, 1), 2)

def load_raw():
    try:
        df = pd.read_json(JSON_FILE)
    except Exception as e:
        print(f"Error reading {JSON_FILE}: {e}")
        return pd.DataFrame()

    if df.empty:
        return pd.DataFrame(columns=["Phone Name", "chip", "battery", "charge", "price", "score", "display", "refresh", "bright"])

    specs = {}
    for col in df.columns:
        key = col.lower().replace(" ", "_")
        specs[key] = pd.json_normalize(df[col]) if isinstance(df[col][0], (dict, list)) else pd.DataFrame(df[col])

    try:
        rates = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5).json()["rates"]
        rates = {k: 1 / v for k, v in rates.items()}
    except Exception as e:
        print(f"Error fetching currency rates: {e}")
        rates = {"USD": 1, "EUR": 1, "GBP": 1, "INR": 0.012}

    symbols = {"$": "USD", "€": "EUR", "£": "GBP", "₹": "INR"}

    chip = pd.Series("", index=df.index, dtype="object") if "platform" not in specs else specs["platform"].get("chipset", pd.Series("", index=df.index, dtype="object"))
    chip = chip.apply(lambda x: ", ".join(i.split(" (")[0].strip() for i in x) if isinstance(x, list) else x.split(" (")[0].strip() if isinstance(x, str) else x)
    
    battery = pd.Series(0, index=df.index, dtype=int) if "battery" not in specs else specs["battery"].get("batdescription1", pd.Series(0, index=df.index, dtype=int)).str.extract(r"(\d+)")[0].fillna(0).astype(int)
    
    charge = pd.Series(0, index=df.index, dtype=int) if "battery" not in specs else specs["battery"].get("Charging", pd.Series(0, index=df.index, dtype=int)).str.extract(r"(\d+)")[0].fillna(0).astype(int)
    
    score = pd.Series(0, index=df.index, dtype=int) if "tests" not in specs else specs["tests"].get("tbench", pd.Series(0, index=df.index, dtype=int)).str.extract(r"AnTuTu:\s*(\d+)")[0].fillna(0).astype(int)
    
    display = pd.Series("", index=df.index, dtype="object") if "display" not in specs else specs["display"].get("displaytype", pd.Series("", index=df.index, dtype="object")).str.strip().str.split(",").str[0].str.strip()
    
    refresh = pd.Series(pd.NA, index=df.index, dtype="Int64") if "display" not in specs else specs["display"].get("displaytype", pd.Series("", index=df.index, dtype="object")).str.extract(r"(\d+)\s*Hz")[0].astype("Int64")
    
    bright_tests = pd.Series(pd.NA, index=df.index, dtype="Int64") if "tests" not in specs else specs["tests"].get("Display", pd.Series("", index=df.index, dtype="object")).str.extract(r"(\d+)\s*nits")[0]
    bright_display = pd.Series(pd.NA, index=df.index, dtype="Int64") if "display" not in specs else specs["display"].get("displaytype", pd.Series("", index=df.index, dtype="object")).str.extract(r"(\d+)\s*nits")[0]
    bright = bright_tests.combine_first(bright_display).astype("Int64")

    data = pd.DataFrame({
        "Phone Name": specs.get("Phone Name", pd.Series("", index=df.index, dtype="object")).squeeze(),
        "chip": chip,
        "battery": battery,
        "charge": charge,
        "price": specs.get("misc", pd.DataFrame({"price": pd.Series("", index=df.index, dtype="object")})).get("price", pd.Series("", index=df.index, dtype="object")).apply(lambda x: to_usd(x, rates, symbols)),
        "score": score,
        "display": display,
        "refresh": refresh,
        "bright": bright
    })

    pd.set_option("display.float_format", "{:,.0f}".format)
    data["display"] = data["display"].apply(lambda x: "OLED" if pd.notna(x) and "OLED" in str(x).upper() else "LCD")
    data["score"] = pd.to_numeric(data["score"], errors="coerce")
    data["score"] = data["score"].fillna(data.groupby("chip")["score"].transform("mean")).astype("Int64")
    return set_tiers(data)

def process_data():
    """Process raw data and return a cleaned DataFrame."""
    df = load_raw()
    if df.empty:
        print("No data to process.")
        return pd.DataFrame()

    # Ensure all data types are compatible with PyArrow
    df = set_tiers(df)
    
    # Convert problematic object columns to appropriate types
    df["Phone Name"] = df["Phone Name"].astype(str)
    df["chip"] = df["chip"].astype(str)
    df["display"] = df["display"].astype(str)
    
    # Convert numeric columns
    df["battery"] = pd.to_numeric(df["battery"], errors="coerce").fillna(0).astype(int)
    df["charge"] = pd.to_numeric(df["charge"], errors="coerce").fillna(0).astype(int)
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0).astype(float)
    df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0).astype(int)
    
    # Handle nullable integer columns
    df["refresh"] = pd.to_numeric(df["refresh"], errors="coerce").fillna(0).astype(int)
    df["bright"] = pd.to_numeric(df["bright"], errors="coerce").fillna(0).astype(int)
    
    return df