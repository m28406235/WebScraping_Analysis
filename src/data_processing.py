
import pandas as pd
from sklearn.impute import KNNImputer
from sklearn.preprocessing import LabelEncoder
from Regex import get_processed_phone_data as raw_data_loader

def get_processed_phone_data():
    phone_data = raw_data_loader()

    # Data cleaning
    phone_data['price'] = phone_data.groupby('phone_tier')['price'].transform(lambda x: x.fillna(x.mean()))
    phone_data['refresh_rate'] = phone_data['refresh_rate'].fillna(phone_data['refresh_rate'].mode()[0])
    phone_data['brightness'] = phone_data['brightness'].astype('float')
    phone_data['brightness'] = phone_data.groupby('display_type')['brightness'].transform(lambda x: x.fillna(x.mean()))

    phone_data["antutu_score"] = phone_data["antutu_score"].replace(0, pd.NA)
    encoder = LabelEncoder()
    phone_data["phone_tier_encoded"] = encoder.fit_transform(phone_data["phone_tier"])
    features = ["price", "phone_tier_encoded", "antutu_score"]
    knn_imputer = KNNImputer(n_neighbors=5)
    imputed_data = knn_imputer.fit_transform(phone_data[features])
    phone_data["antutu_score"] = imputed_data[:, 2]
    phone_data["antutu_score"] = phone_data["antutu_score"].astype(int)
    phone_data = phone_data.drop(columns=["phone_tier_encoded"])

    return phone_data
