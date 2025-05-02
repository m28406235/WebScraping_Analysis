import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
from Regex import get_processed_phone_data
from sklearn.impute import KNNImputer
from sklearn.preprocessing import LabelEncoder
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# Streamlit Setup
st.set_page_config(page_title="Phone Data Analysis", layout="wide")
st.title("Phone Data Visualizations")

# Load data
phone_data = get_processed_phone_data()
st.write(phone_data.head())
st.write("Data shape:", phone_data.shape)
st.write("Columns:", phone_data.columns)
st.write("Data types:", phone_data.dtypes)
st.write("Missing values:", phone_data.isnull().sum())

# Data cleaning steps (as in original code)
phone_data['price'] = phone_data.groupby('phone_tier')['price'].transform(lambda x: x.fillna(x.mean()))
phone_data['refresh_rate'] = phone_data['refresh_rate'].fillna(phone_data['refresh_rate'].mode()[0])
phone_data['brightness'] = phone_data['brightness'].astype('float')
phone_data['brightness'] = phone_data.groupby('display_type')['brightness'].transform(lambda x: x.fillna(x.mean()))

#KNN Imputation for Antutu Score
phone_data["antutu_score"] = phone_data["antutu_score"].replace(0, pd.NA)
encoder = LabelEncoder()
phone_data["phone_tier_encoded"] = encoder.fit_transform(phone_data["phone_tier"])
features = ["price", "phone_tier_encoded", "antutu_score"]
knn_imputer = KNNImputer(n_neighbors=5)
imputed_data = knn_imputer.fit_transform(phone_data[features])
phone_data["antutu_score"] = imputed_data[:, 2]
phone_data["antutu_score"] = phone_data["antutu_score"].astype(int)
phone_data = phone_data.drop(columns=["phone_tier_encoded"])
st.write("After Cleaning")
st.write("Missing values:", phone_data.isnull().sum())



tier_order = ["Budget", "Mid-Range", "Premium", "Flagship"]
phone_data["phone_tier"] = pd.Categorical(phone_data["phone_tier"], categories=tier_order, ordered=True)

# Scatter Plot for Performance vs Price
color_map = {
    'Budget': 'rgba(0, 200, 81, 0.7)',
    'Mid-Range': 'rgba(0, 122, 255, 0.7)',
    'Premium': 'rgba(138, 43, 226, 0.7)',
    'Flagship': 'rgba(255, 0, 0, 0.7)'
}

phone_data['phone_tier'] = pd.Categorical(phone_data['phone_tier'], categories=tier_order, ordered=True)
phone_data['text'] = phone_data['phone_name']

best_phones_idx = phone_data.groupby('phone_tier').apply(
    lambda group: (group['antutu_score'] / group['price']).idxmax()
)
best_phones_data = phone_data.loc[best_phones_idx]

fig = px.scatter(
    phone_data,
    x='price',
    y='antutu_score',
    color='phone_tier',
    category_orders={'phone_tier': tier_order},
    color_discrete_map=color_map,
    hover_data={'text': True, 'price': True, 'antutu_score': True, 'phone_tier': False},
    title="Price vs Antutu Score",
    labels={'price': 'Price (USD)', 'antutu_score': 'Antutu Score (K)'}
)

for _, row in best_phones_data.iterrows():
    fig.add_scatter(
        x=[row['price']],
        y=[row['antutu_score']],
        mode='markers',
        marker=dict(symbol='diamond', size=10, color=color_map[row['phone_tier']], line=dict(width=1.2, color='gold')),
        name=f"Best Phone ({row['phone_tier']})",
        hovertemplate=(
            f"<b>{row['phone_name']}</b><br>"
            f"Price: {row['price']}<br>"
            f"Phone Tier: {row['phone_tier']}<br>"
            f"Antutu Score: {row['antutu_score']}<extra></extra>"
        )
    )

fig.update_layout(
    xaxis_title="Price (USD)",
    yaxis_title="Antutu Score (K)",
    legend_title="Phone Tier",
    hovermode='closest',
    template="plotly_white"
)

st.plotly_chart(fig)

# Bubble Chart for Battery vs Charging Speed
fig = px.scatter(
    phone_data,
    x='charging_speed',
    y='battery_capacity',
    size='price',
    color='phone_tier',
    hover_name='phone_name',
    title="Battery Capacity vs Charging Speed",
    labels={'charging_speed': 'Charging Speed (W)', 'battery_capacity': 'Battery Capacity (mAh)'},
    category_orders={"phone_tier": ["Budget", "Mid-Range", "Premium", "Flagship"]}
)

fig.update_layout(
    xaxis_title="Charging Speed (W)",
    yaxis_title="Battery Capacity (mAh)",
    template="plotly_white"
)

st.plotly_chart(fig)

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
st.plotly_chart(fig)

# Bar Chart for Number of Phones by Tier
phone_count_by_tier = phone_data["phone_tier"].value_counts().reset_index()
phone_count_by_tier.columns = ["phone_tier", "count"]
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

st.plotly_chart(fig)

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
st.pyplot(plt)

# Top 10 Chipsets by Antutu Score
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
    text="phone_name",
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
st.plotly_chart(fig)

# Box Plot for Brightness by Display Type
fig = px.box(
    phone_data,
    x="display_type",
    y="brightness",
    title="Comparison of Brightness by Display Type",
    labels={"display_type": "Display Type", "brightness": "Brightness (nits)"},
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
st.plotly_chart(fig)
