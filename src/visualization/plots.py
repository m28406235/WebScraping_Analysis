import streamlit as st
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import sys
import os

# Add the parent directory to sys.path to make imports work
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from data.processor import process_data

def show_plots():
    st.set_page_config(page_title="Phone Analysis", layout="wide")
    st.title("Phone Visuals")
    data = process_data()
    if data.empty:
        st.write("No data available")
        return
    
    # Handle data display to avoid PyArrow serialization issues
    try:
        # Try to display the dataframe directly
        st.write(data.head())
    except Exception as e:
        # Fallback to safer display method if direct display fails
        st.write("Preview of first 5 rows:")
        # Convert to dict and then display to avoid PyArrow issues
        st.write(pd.DataFrame(data.head().to_dict()))
    
    st.write("Shape:", data.shape)
    st.write("Columns:", list(data.columns))
    st.write("Types:", dict(data.dtypes.astype(str)))
    st.write("Nulls:", dict(data.isnull().sum()))

    tiers = ["Budget", "Mid-Range", "Premium", "Flagship"]
    data["tier"] = pd.Categorical(data["tier"], categories=tiers, ordered=True)
    colors = {
        "Budget": "rgba(0, 200, 81, 0.7)",
        "Mid-Range": "rgba(0, 122, 255, 0.7)",
        "Premium": "rgba(138, 43, 226, 0.7)",
        "Flagship": "rgba(255, 0, 0, 0.7)"
    }
    data["label"] = data["Phone Name"]

    best_idx = data.groupby("tier").apply(lambda x: (x["score"] / x["price"]).idxmax() if not x.empty else None)
    best_data = data.loc[best_idx.dropna()]

    fig = px.scatter(
        data,
        x="price",
        y="score",
        color="tier",
        category_orders={"tier": tiers},
        color_discrete_map=colors,
        hover_data={"label": True, "price": True, "score": True, "tier": False},
        title="Price vs Score",
        labels={"price": "Price (USD)", "score": "Score (K)"}
    )
    for _, row in best_data.iterrows():
        fig.add_scatter(
            x=[row["price"]],
            y=[row["score"]],
            mode="markers",
            marker=dict(symbol="diamond", size=10, color=colors[row["tier"]], line=dict(width=1.2, color="gold")),
            name=f"Best ({row['tier']})",
            hovertemplate=f"<b>{row['Phone Name']}</b><br>Price: {row['price']}<br>Tier: {row['tier']}<br>Score: {row['score']}<extra></extra>"
        )
    fig.update_layout(
        xaxis_title="Price (USD)",
        yaxis_title="Score (K)",
        legend_title="Tier",
        hovermode="closest",
        template="plotly_white"
    )
    st.plotly_chart(fig)

    fig = px.scatter(
        data,
        x="charge",
        y="battery",
        size="price",
        color="tier",
        hover_name="Phone Name",
        title="Battery vs Charge Speed",
        labels={"charge": "Charge Speed (W)", "battery": "Battery (mAh)"},
        category_orders={"tier": tiers}
    )
    fig.update_layout(
        xaxis_title="Charge Speed (W)",
        yaxis_title="Battery (mAh)",
        template="plotly_white"
    )
    st.plotly_chart(fig)

    display_counts = data["display"].value_counts().reset_index()
    display_counts.columns = ["display", "count"]
    fig = px.pie(
        display_counts,
        values="count",
        names="display",
        title="Display Types",
        hole=0.3
    )
    fig.update_traces(textinfo="percent+label")
    st.plotly_chart(fig)

    tier_counts = data["tier"].value_counts().reset_index()
    tier_counts.columns = ["tier", "count"]
    tier_counts["tier"] = pd.Categorical(tier_counts["tier"], categories=tiers, ordered=True)
    tier_counts = tier_counts.sort_values("tier")
    fig = px.bar(
        tier_counts,
        x="tier",
        y="count",
        text="count",
        title="Phones per Tier",
        labels={"tier": "Tier", "count": "Count"},
        color="tier",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig.update_traces(texttemplate="%{text}", textposition="outside")
    fig.update_layout(
        xaxis_title="Tier",
        yaxis_title="Count",
        template="plotly_white"
    )
    st.plotly_chart(fig)

    cols = ["price", "score", "battery", "charge", "refresh", "bright"]
    corr = data[cols].corr()
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        cbar=True,
        square=True
    )
    plt.title("Correlation", fontsize=16)
    plt.xticks(rotation=45, ha="right", fontsize=12)
    plt.yticks(fontsize=12)
    st.pyplot(plt)

    top_chips = data[data["score"] > 0]
    top_chips = top_chips.sort_values(by="score", ascending=False)
    top_chips = top_chips.groupby("chip").first().reset_index()
    top_chips = top_chips.sort_values(by="score", ascending=False).head(10)
    fig = px.bar(
        top_chips,
        x="chip",
        y="score",
        text="Phone Name",
        title="Top 10 Chips by Score",
        labels={"chip": "Chip", "score": "Score"},
        color="score",
        color_continuous_scale="Viridis"
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        xaxis_title="Chip",
        yaxis_title="Score",
        xaxis_tickangle=45,
        template="plotly_white",
        showlegend=False
    )
    st.plotly_chart(fig)

    fig = px.box(
        data,
        x="display",
        y="bright",
        title="Brightness by Display",
        labels={"display": "Display", "bright": "Brightness (nits)"},
        color="display",
        hover_data=["Phone Name"],
        template="plotly_white"
    )
    fig.update_layout(
        xaxis_title="Display",
        yaxis_title="Brightness (nits)",
        xaxis_tickangle=45,
        showlegend=False
    )
    st.plotly_chart(fig)

# Run the app when this file is executed directly
if __name__ == "__main__":
    show_plots()