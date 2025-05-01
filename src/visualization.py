import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
from Regex import get_processed_phone_data

phone_data = get_processed_phone_data()
print(phone_data.head())
print(phone_data.shape)
print(phone_data.columns)
print(phone_data.dtypes)
print(phone_data.isnull().sum())
# replace NaN values in 'price' with the mean price of the corresponding phone tier
phone_data['price'] = phone_data.groupby('phone_tier')['price'].transform(lambda x: x.fillna(x.mean()))
#replace NaN values in 'refresh_rate' with the mode of the corresponding phone tier
phone_data['refresh_rate'] = phone_data['refresh_rate'].fillna(phone_data['refresh_rate'].mode()[0])

#make brightness a float
phone_data['brightness'] = phone_data['brightness'].astype('float')
#replace NaN values in 'brightness' with the mean brightness of the corresponding display type
phone_data['brightness'] = phone_data.groupby('display_type')['brightness'].transform(lambda x: x.fillna(x.mean()))
print(phone_data.isnull().sum())
print(phone_data.head())

# replace 0 antutu_score with knn imputation
from sklearn.impute import KNNImputer
from sklearn.preprocessing import LabelEncoder

#replace 0 values in 'antutu_score' with NaN
phone_data["antutu_score"] = phone_data["antutu_score"].replace(0, pd.NA)

#label encoding for 'phone_tier'
encoder = LabelEncoder()
phone_data["phone_tier_encoded"] = encoder.fit_transform(phone_data["phone_tier"])

#select features for KNNImputer
features = ["price", "phone_tier_encoded", "antutu_score"]

#knn imputation
knn_imputer = KNNImputer(n_neighbors=5)  # use 5 nearest neighbors
imputed_data = knn_imputer.fit_transform(phone_data[features])

#update the original DataFrame with imputed values
phone_data["antutu_score"] = imputed_data[:, 2]

#integer conversion for 'antutu_score'
phone_data["antutu_score"] = phone_data["antutu_score"].astype(int)

#delete the temporary column
phone_data = phone_data.drop(columns=["phone_tier_encoded"])


# Define the custom order for phone_tier
tier_order = ["Budget", "Mid-Range", "Premium", "Flagship"]

# Apply the custom order to the phone_tier column
phone_data["phone_tier"] = pd.Categorical(phone_data["phone_tier"], categories=tier_order, ordered=True)

#1
# Scatter Plot for Performance vs Price
tier_order = ['Budget', 'Mid-Range', 'Premium', 'Flagship']
phone_data['phone_tier'] = pd.Categorical(phone_data['phone_tier'], categories=tier_order, ordered=True)

phone_data['text'] = phone_data['phone_name']

best_phones_idx = phone_data.groupby('phone_tier').apply(lambda group: (group['antutu_score'] / group['price']).idxmax())
best_phones_data = phone_data.loc[best_phones_idx]

fig = px.scatter(phone_data, x='price', y='antutu_score', color='phone_tier', category_orders={'phone_tier': tier_order}, color_discrete_map={'Budget': '#2ca02c', 'Mid-Range': '#1f77b4', 'Premium': '#9467bd', 'Flagship': '#d62728'}, hover_data={'text': True, 'price': True, 'antutu_score': False, 'phone_tier': False})

fig.add_scatter(x=best_phones_data['price'], y=best_phones_data['antutu_score'], mode='markers', marker=dict(symbol='diamond', size=10, color='gold', line=dict(width=2, color='black')), name="Best Phones", hovertemplate='%{customdata[0]}<br>Price: %{x}<extra></extra>', customdata=best_phones_data[['text']])

fig.update_traces(hovertemplate='%{customdata[0]}<br>Price: %{x}<extra></extra>', customdata=phone_data[['text']], marker=dict(size=10), selector=dict(mode='markers'))

fig.update_layout(title="Price vs Antutu Score", xaxis_title="Price", yaxis_title="Antutu Score", legend_title="Phone Tier", hovermode='closest')

fig.show()
#2
# Bubble Chart for Battery vs Charging Speed
fig = px.scatter(
    phone_data,
    x='charging_speed',
    y='battery_capacity',
    size='price',
    color='phone_tier',
    hover_name='phone_name',
    title="Battery Capacity vs Charging Speed",
    labels={
        'charging_speed': 'Charging Speed (W)',
        'battery_capacity': 'Battery Capacity (mAh)'
    },
    category_orders={"phone_tier": ["Budget", "Mid-Range", "Premium", "Flagship"]}  # Confirm order
)

fig.update_layout(
    xaxis_title="Charging Speed (W)",
    yaxis_title="Battery Capacity (mAh)",
    template="plotly_white"
)

fig.show()
#3
# Pie Chart for Display Types
display_counts = phone_data['display_type'].value_counts().reset_index()
display_counts.columns = ['display_type', 'count']

fig = px.pie(
    display_counts,
    values='count',
    names='display_type',
    title="Distribution of Display Types",
    hole=0.3
)

fig.update_traces(textinfo='percent+label')
fig.show()
#4
phone_count_by_tier = phone_data["phone_tier"].value_counts().reset_index()
phone_count_by_tier.columns = ["phone_tier", "count"]

tier_order = ["Budget", "Mid-Range", "Premium", "Flagship"]
phone_count_by_tier["phone_tier"] = pd.Categorical(phone_count_by_tier["phone_tier"], categories=tier_order, ordered=True)
phone_count_by_tier = phone_count_by_tier.sort_values("phone_tier")

fig = px.bar(
    phone_count_by_tier,
    x="phone_tier",
    y="count",
    text="count",
    title="Number of Phones in Each Tier",
    labels={"phone_tier": "Phone Tier", "count": "Number of Phones"},
    color="phone_tier",
    color_discrete_sequence=px.colors.qualitative.Set2
)
fig.update_traces(texttemplate='%{text}', textposition='outside')
fig.update_layout(
    xaxis_title="Phone Tier",
    yaxis_title="Number of Phones",
    template="plotly_white"
)

fig.show()
#5
#Compare the top 10 most expensive phones in each tier

from plotly.subplots import make_subplots
import plotly.graph_objects as go

tier_order = ["Budget", "Mid-Range", "Premium", "Flagship"]
phone_data["phone_tier"] = pd.Categorical(phone_data["phone_tier"], categories=tier_order, ordered=True)

fig = make_subplots(
    rows=2,
    cols=2,
    subplot_titles=[f"Top 10 Phones in {tier} Tier" for tier in tier_order]  # عناوين لكل فئة
)

for i, tier in enumerate(tier_order):
    row = (i // 2) + 1
    col = (i % 2) + 1

    top_10_phones = phone_data[phone_data["phone_tier"] == tier].sort_values(by="price", ascending=False).head(10)

    fig.add_trace(
        go.Bar(
            x=top_10_phones["phone_name"],
            y=top_10_phones["price"],
          #  text=top_10_phones["chipset"],  # عرض نوع المعالج كـ Text
            hovertext=(
                    "Chipset: " + top_10_phones["chipset"]  +
                    "<br>Refresh Rate: " + top_10_phones["refresh_rate"].astype(str) +
                    "<br>Display: " + top_10_phones["display_type"] +
                    "<br>Price: " + top_10_phones["price"].astype(str)
            ),

            hoverinfo="text",
            name=tier
        ),
        row=row,
        col=col
    )

fig.update_layout(
    height=1200,
    width=1400,
    title_text="Top 10 Most Expensive Phones by Tier",
    showlegend=False,
    template="plotly_white"
)

fig.update_xaxes(tickangle=45, title_text="Phone Name")
fig.update_yaxes(title_text="Price (USD)")

fig.show()
#6
# Correlation Matrix
columns_of_interest = ["price", "antutu_score", "battery_capacity", "charging_speed", "refresh_rate", "brightness"]
correlation_data = phone_data[columns_of_interest]

correlation_matrix = correlation_data.corr()

plt.figure(figsize=(10, 8))
sns.heatmap(
    correlation_matrix,
    annot=True,
    fmt=".2f",
    cmap="coolwarm",
    cbar=True,
    square=True
)
plt.title("Correlation Matrix", fontsize=16)
plt.xticks(rotation=45, ha='right', fontsize=12)
plt.yticks(fontsize=12)
plt.show()

#7
#top 10 chipsets based on Antutu Score
filtered_data = phone_data[phone_data["antutu_score"] > 0]

top_10_data = (
    filtered_data.sort_values(by="antutu_score", ascending=False)
    .groupby("chipset")
    .first()
    .reset_index()
    .sort_values(by="antutu_score", ascending=False)
    .head(10)
)
fig = px.bar(
    top_10_data,
    x="chipset",
    y="antutu_score",
    text="phone_name",  # عرض أسماء الهواتف داخل الرسم
    title="Top 10 Chipsets by Antutu Score with Phones",
    labels={"chipset": "Chipset", "antutu_score": "Antutu Score"},
    color="antutu_score",
    color_continuous_scale="Viridis"
)

fig.update_traces(textposition="outside")
fig.update_layout(
    xaxis_title="Chipset",
    yaxis_title="Antutu Score",
    xaxis_tickangle=45,
    template="plotly_white",
    showlegend=False
)
fig.show()
#8
# Box Plot for Brightness by Display Type
fig = px.box(
    phone_data,
    x="display_type",
    y="brightness",
    title="Comparison of Brightness by Display Type",
    labels={
        "display_type": "Display Type",
        "brightness": "Brightness (nits)"
    },
    color="display_type",
    hover_data=["phone_name"],
    template="plotly_white"
)
fig.update_layout(
    xaxis_title="Display Type",
    yaxis_title="Brightness (nits)",
    xaxis_tickangle=45,
    showlegend=False
)

fig.show()