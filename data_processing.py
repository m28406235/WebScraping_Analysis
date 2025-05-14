import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.cluster import KMeans
from utils import to_usd, extract_numeric_value, extract_antutu_score, extract_display_type, extract_brightness, extract_chipset_info
import os
import warnings

os.environ["LOKY_MAX_CPU_COUNT"] = "4"
warnings.filterwarnings("ignore", category=UserWarning, module="joblib")
pd.options.mode.chained_assignment = None


def get_processed_phone_data():
    df = pd.read_json("phone_specs.json")
    specs = {
        col.lower().replace(" ", "_"):
        (pd.json_normalize(df[col]) if isinstance(df[col][0], (dict, list))
         else pd.DataFrame(df[col]))
        for col in df.columns
    }

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

    pd.set_option("display.float_format", "{:,.0f}".format)

    data["display_type"] = data["display_type"].apply(
        lambda x: "OLED-Based" if pd.notna(
            x) and "OLED" in str(x).upper() else "LCD-Based"
    )

    data = assign_phone_tiers(data)

    data['price'] = data.groupby('phone_tier')['price'].transform(
        lambda x: x.fillna(x.mean()))
    data['refresh_rate'] = data['refresh_rate'].fillna(
        data['refresh_rate'].mode()[0])
    data['brightness'] = data['brightness'].astype('float')
    data['brightness'] = data.groupby('display_type')[
        'brightness'].transform(lambda x: x.fillna(x.mean()))

    data["antutu_score"] = pd.to_numeric(data["antutu_score"], errors="coerce")
    data["antutu_score"] = data["antutu_score"].fillna(
        data.groupby("chipset")["antutu_score"].transform("mean")
    ).astype("Int64")

    data["antutu_score"] = data["antutu_score"].replace(0, pd.NA)
    encoder = LabelEncoder()
    data["phone_tier_encoded"] = encoder.fit_transform(data["phone_tier"])
    features = ["price", "phone_tier_encoded", "antutu_score"]
    knn_imputer = KNNImputer(n_neighbors=5)
    imputed_data = knn_imputer.fit_transform(data[features])
    data["antutu_score"] = imputed_data[:, 2]
    data["antutu_score"] = data["antutu_score"].astype(int)
    data = data.drop(columns=["phone_tier_encoded"])

    return data


def assign_phone_tiers(df):
    q1, q3 = df['price'].quantile([0.25, 0.75])
    iqr = q3 - q1
    mask = df['price'].between(q1 - 1.5*iqr, q3 + 1.5*iqr)
    df['tier_num'] = -1
    kmeans = KMeans(n_clusters=3, random_state=42)
    df.loc[mask, 'tier_num'] = kmeans.fit_predict(df.loc[mask, ['price']])
    cluster_order = np.argsort(kmeans.cluster_centers_.squeeze())
    tier_map = {
        **{cluster_order[i]: tier for i, tier in enumerate(['Budget', 'Mid-Range', 'Premium'])},
        -1: 'Flagship'
    }
    df['phone_tier'] = df['tier_num'].map(tier_map)
    df = df.drop(columns=["tier_num"])
    return df
