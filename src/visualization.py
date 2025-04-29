import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from regex import get_processed_phone_data

phone_data = get_processed_phone_data()
phone_data = phone_data[(phone_data[['price', 'antutu_score', 'battery_capacity', 'charging_speed']] != 0).all(axis=1)]

tier_order = ['Budget', 'Mid-Range', 'Premium', 'Flagship']
phone_data['phone_tier'] = pd.Categorical(phone_data['phone_tier'], categories=tier_order, ordered=True)

tier_colors = {'Budget': '#2ca02c', 'Mid-Range': '#1f77b4', 'Premium': '#9467bd', 'Flagship': '#d62728'}

best_phones = phone_data.loc[phone_data.groupby('phone_tier').apply(lambda group: (group['antutu_score'] / group['price']).idxmax())]

plt.figure(figsize=(8, 6))
sns.scatterplot(data=phone_data, x='price', y='antutu_score', hue='phone_tier', palette=tier_colors, hue_order=tier_order)
sns.scatterplot(data=best_phones, x='price', y='antutu_score', hue='phone_tier', palette=tier_colors, hue_order=tier_order, marker='P', s=250, edgecolor='gold', legend=False)
plt.title("Price vs Antutu Score")
plt.xlabel("Price")
plt.ylabel("Antutu Score")
plt.legend(title="Phone Tier")
plt.show()