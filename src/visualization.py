import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import KNNImputer
from Regex import get_processed_phone_data
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import pandas as pd
import warnings

# Suppress warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Define constants
TIER_ORDER = ["Budget", "Mid-Range", "Premium", "Flagship"]
TIER_COLORS = {
    'Budget': '#2ca02c', 
    'Mid-Range': '#1f77b4', 
    'Premium': '#9467bd', 
    'Flagship': '#d62728'
}

def load_and_clean_data():
    """Load data and perform cleaning operations"""
    phone_data = get_processed_phone_data()
    
    # Fill missing price values with mean of their respective tier
    phone_data['price'] = phone_data.groupby(
        'phone_tier')['price'].transform(lambda x: x.fillna(x.mean()))
    
    # Fill missing refresh rate with mode
    phone_data['refresh_rate'] = phone_data['refresh_rate'].fillna(
        phone_data['refresh_rate'].mode()[0])
    
    # Convert brightness to float and fill missing values
    phone_data['brightness'] = phone_data['brightness'].astype('float')
    phone_data['brightness'] = phone_data.groupby(
        'display_type')['brightness'].transform(lambda x: x.fillna(x.mean()))
    
    # Replace 0 antutu scores with NA for proper imputation
    phone_data["antutu_score"] = phone_data["antutu_score"].replace(0, pd.NA)
    
    # Impute missing antutu scores using KNN
    encoder = LabelEncoder()
    phone_data["phone_tier_encoded"] = encoder.fit_transform(
        phone_data["phone_tier"])
    
    features = ["price", "phone_tier_encoded", "antutu_score"]
    knn_imputer = KNNImputer(n_neighbors=5)
    imputed_data = knn_imputer.fit_transform(phone_data[features])
    
    phone_data["antutu_score"] = imputed_data[:, 2].astype(int)
    phone_data = phone_data.drop(columns=["phone_tier_encoded"])
    
    # Set phone tier as categorical with proper order
    phone_data["phone_tier"] = pd.Categorical(
        phone_data["phone_tier"], categories=TIER_ORDER, ordered=True)
    
    # Add text field for hover information
    phone_data['text'] = phone_data['phone_name']
    
    return phone_data

def plot_antutu_vs_price(phone_data):
    """Create scatter plot of Antutu score vs price"""
    # Find phones with best value (antutu/price ratio) in each tier
    best_phones_idx = phone_data.groupby('phone_tier').apply(
        lambda group: (group['antutu_score'] / group['price']).idxmax())
    best_phones_data = phone_data.loc[best_phones_idx]
    
    # Create scatter plot
    fig = px.scatter(
        phone_data, 
        x='price', 
        y='antutu_score', 
        color='phone_tier', 
        category_orders={'phone_tier': TIER_ORDER}, 
        color_discrete_map=TIER_COLORS, 
        hover_data={'text': True, 'price': True, 'antutu_score': False, 'phone_tier': False}
    )
    
    # Add markers for best value phones
    fig.add_scatter(
        x=best_phones_data['price'], 
        y=best_phones_data['antutu_score'], 
        mode='markers', 
        marker=dict(
            symbol='diamond', 
            size=10, 
            color='gold', 
            line=dict(width=2, color='black')
        ), 
        name="Best Value Phones", 
        hovertemplate='%{customdata[0]}<br>Price: %{x}<extra></extra>', 
        customdata=best_phones_data[['text']]
    )
    
    # Update hover template and marker size
    fig.update_traces(
        hovertemplate='%{customdata[0]}<br>Price: %{x}<extra></extra>',
        customdata=phone_data[['text']], 
        marker=dict(size=10), 
        selector=dict(mode='markers')
    )
    
    # Improve layout
    fig.update_layout(
        title="Price vs Antutu Score (Performance)",
        xaxis_title="Price (USD)",
        yaxis_title="Antutu Score",
        legend_title="Phone Tier",
        hovermode='closest',
        template="plotly_white"
    )
    
    return fig

def plot_battery_vs_charging(phone_data):
    """Create scatter plot of battery capacity vs charging speed"""
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
        category_orders={"phone_tier": TIER_ORDER}
    )
    
    fig.update_layout(
        xaxis_title="Charging Speed (W)",
        yaxis_title="Battery Capacity (mAh)",
        template="plotly_white"
    )
    
    return fig

def plot_display_types(phone_data):
    """Create pie chart of display types"""
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
    return fig

def plot_phones_by_tier(phone_data):
    """Create bar chart of phone count by tier"""
    phone_count_by_tier = phone_data["phone_tier"].value_counts().reset_index()
    phone_count_by_tier.columns = ["phone_tier", "count"]
    
    # Ensure proper ordering of tiers
    phone_count_by_tier["phone_tier"] = pd.Categorical(
        phone_count_by_tier["phone_tier"], categories=TIER_ORDER, ordered=True)
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
    
    return fig

def plot_top_phones_by_tier(phone_data):
    """Create subplot with top 10 phones by price in each tier"""
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=[f"Top 10 Phones in {tier} Tier" for tier in TIER_ORDER]
    )
    
    for i, tier in enumerate(TIER_ORDER):
        row = (i // 2) + 1
        col = (i % 2) + 1
        
        top_10_phones = phone_data[phone_data["phone_tier"] == tier].sort_values(
            by="price", ascending=False).head(10)
        
        hover_text = (
            "Chipset: " + top_10_phones["chipset"] +
            "<br>Refresh Rate: " + top_10_phones["refresh_rate"].astype(str) +
            "<br>Display: " + top_10_phones["display_type"] +
            "<br>Price: " + top_10_phones["price"].astype(str)
        )
        
        fig.add_trace(
            go.Bar(
                x=top_10_phones["phone_name"],
                y=top_10_phones["price"],
                hovertext=hover_text,
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
    
    return fig

def plot_correlation_matrix(phone_data):
    """Create correlation matrix heatmap"""
    columns_of_interest = [
        "price", "antutu_score", "battery_capacity",
        "charging_speed", "refresh_rate", "brightness"
    ]
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
    
    return plt

def plot_top_chipsets(phone_data):
    """Create bar chart of top chipsets by Antutu score"""
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
    
    return fig

def plot_brightness_by_display(phone_data):
    """Create box plot of brightness by display type"""
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
    
    return fig

def main():
    """Main function to load data and create visualizations"""
    # Load and clean data
    phone_data = load_and_clean_data()
    
    # Create and display all plots
    plots = [
        plot_antutu_vs_price(phone_data),
        plot_battery_vs_charging(phone_data),
        plot_display_types(phone_data),
        plot_phones_by_tier(phone_data),
        plot_top_phones_by_tier(phone_data),
        plot_top_chipsets(phone_data),
        plot_brightness_by_display(phone_data)
    ]
    
    # Display all plotly figures
    for plot in plots:
        if isinstance(plot, plt.Figure):
            plot.show()
        else:
            plot.show()
    
    # Display matplotlib correlation matrix
    plot_correlation_matrix(phone_data).show()

if __name__ == "__main__":
    main()
