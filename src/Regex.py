import os
import re
import requests
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings

# Environment and warning settings
os.environ["LOKY_MAX_CPU_COUNT"] = "4"
warnings.filterwarnings("ignore", category=UserWarning, module="joblib")
pd.options.mode.chained_assignment = None

def get_processed_phone_data():
    """
    Processes phone specification data from a JSON file, transforming and categorizing it.
    
    Returns:
        pandas.DataFrame: Processed phone data with calculated metrics and categories
    """
    # Load and normalize raw data
    df = pd.read_json("phone_specs.json")
    specs = {
        col.lower().replace(" ", "_"): 
        (pd.json_normalize(df[col]) if isinstance(df[col][0], (dict, list)) 
         else pd.DataFrame(df[col])) 
        for col in df.columns
    }
    
    # Setup currency conversion
    rates = {k: 1 / v for k, v in requests.get("https://open.er-api.com/v6/latest/USD").json()["rates"].items()}
    symbol_map = {'$': 'USD', '€': 'EUR', '£': 'GBP', '₹': 'INR'}

    def to_usd(price_string):
        """Convert price strings in various currencies to USD"""
        pattern = r'([\$€£₹])?\s?([\d,]+(?:\.\d{2})?)\s?(USD|EUR|GBP|INR)?'
        match = re.search(pattern, str(price_string))
        
        if not match:
            return None
            
        # Extract amount and convert based on currency symbol or code
        amount = float(match.group(2).replace(',', ''))
        symbol = match.group(1)
        code = match.group(3)
        currency = symbol_map.get(symbol, code)
        
        return round(amount * rates.get(currency, 1), 2)

    # Create structured dataframe with relevant fields
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

    # Format display and post-processing
    pd.set_option("display.float_format", "{:,.0f}".format)
    
    # Classify display types
    data["display_type"] = data["display_type"].apply(
        lambda x: "OLED-Based" if pd.notna(x) and "OLED" in str(x).upper() else "LCD-Based"
    )
    
    # Fill missing AnTuTu scores with chipset averages
    data["antutu_score"] = pd.to_numeric(data["antutu_score"], errors="coerce")
    data["antutu_score"] = data["antutu_score"].fillna(
        data.groupby("chipset")["antutu_score"].transform("mean")
    ).astype("Int64")
    
    # Assign phone tiers based on price clustering
    data = assign_phone_tiers(data)
    
    return data

def extract_chipset_info(chipset_series):
    """Extract and clean chipset information from raw data"""
    return chipset_series.apply(
        lambda x: ", ".join(i.split(" (")[0].strip() for i in x) if isinstance(x, list) 
        else x.split(" (")[0].strip() if isinstance(x, str) else x
    )

def extract_numeric_value(series):
    """Extract numeric values from text strings"""
    return series.str.extract(r"(\d+)")[0].fillna(0).astype(int)

def extract_antutu_score(bench_series):
    """Extract AnTuTu benchmark scores from text strings"""
    return bench_series.str.extract(r"AnTuTu:\s*(\d+)")[0].fillna(0).astype(int)

def extract_display_type(display_series):
    """Extract and standardize display type information"""
    return (display_series.str.strip()
            .str.split(",")
            .apply(lambda x: ", ".join(i.strip() for i in x) if isinstance(x, list) else x)
            .str.split(",")
            .str[0]
            .str.strip())

def extract_brightness(specs):
    """Extract brightness information from multiple possible locations"""
    from_tests = specs["tests"]["Display"].str.extract(r"(\d+)\s*nits")[0]
    from_display = specs["display"]["displaytype"].str.extract(r"(\d+)\s*nits")[0]
    return from_tests.combine_first(from_display).astype("Int64")

def assign_phone_tiers(data):
    """
    Assign phones to price tiers using KMeans clustering.
    
    Args:
        data (pd.DataFrame): Phone data with price information
        
    Returns:
        pd.DataFrame: Same dataframe with added phone_tier column
    """
    # Remove outliers for better clustering
    q1, q3 = data['price'].quantile([0.25, 0.75])
    iqr = q3 - q1
    filtered_data = data[data['price'].between(q1 - 1.5 * iqr, q3 + 1.5 * iqr)]
    
    # Perform clustering on prices
    prices = filtered_data['price'].values.reshape(-1, 1)
    scaled_prices = StandardScaler().fit_transform(prices)
    clusters = KMeans(n_clusters=3, random_state=42).fit_predict(scaled_prices)
    filtered_data['phone_tier'] = clusters
    
    # Merge cluster info back to original data
    data = data.merge(filtered_data[['phone_tier']], left_index=True, right_index=True, how='left')
    data['phone_tier'] = data['phone_tier'].fillna(-1).astype(int)
    
    # Map numeric clusters to meaningful labels
    cluster_means = data[data['phone_tier'] != -1].groupby('phone_tier')['price'].mean().sort_values()
    cluster_map = {c: ['Budget', 'Mid-Range', 'Premium'][i] for i, c in enumerate(cluster_means.index)}
    cluster_map[-1] = 'Flagship'
    data['phone_tier'] = data['phone_tier'].map(cluster_map)
    
    return data