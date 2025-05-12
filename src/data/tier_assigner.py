import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def set_tiers(data):
    if data.empty or data["price"].isna().all():
        return data.assign(tier="Flagship")
    
    # Get price quartiles for outlier detection
    q1, q3 = data["price"].quantile([0.25, 0.75])
    iqr = q3 - q1
    filtered = data[data["price"].between(q1 - 1.5 * iqr, q3 + 1.5 * iqr)]
    
    if filtered.empty:
        return data.assign(tier="Flagship")
    
    # Perform k-means clustering on prices
    prices = filtered["price"].values.reshape(-1, 1)
    scaled = StandardScaler().fit_transform(prices)
    clusters = KMeans(n_clusters=3, random_state=42).fit_predict(scaled)
    
    # Create a temporary column with cluster assignments
    filtered = filtered.copy()  # Create a copy to avoid SettingWithCopyWarning
    filtered["temp_tier"] = clusters
    
    # Merge the cluster info back to the original dataframe
    merged_data = data.merge(filtered[["temp_tier"]], left_index=True, right_index=True, how="left")
    
    # Now safely fill NA values and convert to integer
    merged_data["temp_tier"] = merged_data["temp_tier"].fillna(-1).astype(int)
    
    # Calculate means for each tier and map to human-readable tiers
    means = merged_data[merged_data["temp_tier"] != -1].groupby("temp_tier")["price"].mean()
    
    if means.empty:
        return data.assign(tier="Flagship")
    
    # Sort tiers by price
    means = means.sort_values()
    
    # Map numeric tiers to descriptive tiers
    tier_map = {c: ["Budget", "Mid-Range", "Premium"][i] for i, c in enumerate(means.index)}
    tier_map[-1] = "Flagship"
    
    # Create the final tier column
    merged_data["tier"] = merged_data["temp_tier"].map(tier_map)
    
    # Return dataframe with only the needed columns
    result = data.copy()
    result["tier"] = merged_data["tier"]
    return result