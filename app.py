from data_processing import get_processed_phone_data
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import pandas as pd
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)


st.set_page_config(page_title="Phone Data Analysis", layout="wide")
st.title("Phone Data Visualizations")

phone_data = get_processed_phone_data()

st.markdown("### Phone Data Preview")
st.write(phone_data.head(10).to_html(index=False), unsafe_allow_html=True)
st.write("Data shape:", phone_data.shape)
st.write("Data types:", phone_data.dtypes.astype(str).to_dict())
st.write("Missing values:", phone_data.isnull().sum().to_dict())

tier_order = ["Budget", "Mid-Range", "Premium", "Flagship"]
phone_data["phone_tier"] = pd.Categorical(
    phone_data["phone_tier"], categories=tier_order, ordered=True)

color_map = {
    'Budget': 'rgba(0, 200, 81, 0.7)',
    'Mid-Range': 'rgba(0, 122, 255, 0.7)',
    'Premium': 'rgba(138, 43, 226, 0.7)',
    'Flagship': 'rgba(255, 0, 0, 0.7)'
}

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
    hover_data={'text': True, 'price': True,
                'antutu_score': True, 'phone_tier': False},
    title="Price vs Antutu Score",
    labels={'price': 'Price (USD)', 'antutu_score': 'Antutu Score (K)'}
)

for _, row in best_phones_data.iterrows():
    fig.add_scatter(
        x=[row['price']],
        y=[row['antutu_score']],
        mode='markers',
        marker=dict(symbol='diamond', size=10, color=color_map[row['phone_tier']], line=dict(
            width=1.2, color='gold')),
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

fig = px.scatter(
    phone_data,
    x='charging_speed',
    y='battery_capacity',
    size='price',
    color='phone_tier',
    hover_name='phone_name',
    title="Battery Capacity vs Charging Speed",
    labels={
        'charging_speed': 'Charging Speed (W)', 'battery_capacity': 'Battery Capacity (mAh)'},
    category_orders={"phone_tier": tier_order}
)

fig.update_layout(
    xaxis_title="Charging Speed (W)",
    yaxis_title="Battery Capacity (mAh)",
    template="plotly_white"
)

st.plotly_chart(fig)

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

phone_count_by_tier = phone_data["phone_tier"].value_counts().reset_index()
phone_count_by_tier.columns = ["phone_tier", "count"]
phone_count_by_tier["phone_tier"] = pd.Categorical(
    phone_count_by_tier["phone_tier"], categories=tier_order, ordered=True)
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

columns_of_interest = ["price", "antutu_score", "battery_capacity",
                       "charging_speed", "refresh_rate", "brightness"]
correlation_data = phone_data[columns_of_interest]
correlation_matrix = correlation_data.corr()
plt.figure(figsize=(3, 3))
sns.heatmap(
    correlation_matrix,
    annot=True,
    fmt=".2f",
    cmap="coolwarm",
    cbar=True,
    square=True
)
plt.title("Correlation Matrix", fontsize=12)
plt.xticks(rotation=45, ha='right', fontsize=10)
plt.yticks(fontsize=10)
st.pyplot(plt)

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
    yaxis_title=" EHBrightness (nits)",
    xaxis_tickangle=45,
    showlegend=False
)
st.plotly_chart(fig)
