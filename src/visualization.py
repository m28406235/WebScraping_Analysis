import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

import pandas as pd
import plotly.express as px
from regex import get_processed_phone_data

phone_data = get_processed_phone_data()
phone_data = phone_data[(phone_data[['price', 'antutu_score', 'battery_capacity', 'charging_speed']] != 0).all(axis=1)]

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