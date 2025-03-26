import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_visualizations(data):
    """
    Create interactive visualizations of the charging data
    
    Args:
        data: DataFrame containing charging data
        
    Returns:
        Dictionary of plotly figures
    """
    figures = {}
    
    # Ensure data is sorted by date
    data = data.sort_values('date')
    
    # Ensure numeric fields are properly converted to float
    numeric_columns = ['total_kwh', 'peak_kw', 'cost_per_kwh', 'total_cost']
    for col in numeric_columns:
        if col in data.columns:
            # Handle NaN and None values by filling with 0
            data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
    
    # Time series of charging sessions
    # Convert size parameter to a list of values explicitly
    peak_kw_values = data['peak_kw'].fillna(5).tolist()  # Use default size for missing values
    
    figures['time_series'] = px.scatter(
        data,
        x='date',
        y='total_kwh',
        size=peak_kw_values,  # Pass as explicit list
        color='cost_per_kwh',
        hover_name='location',
        hover_data=['total_cost', 'peak_kw', 'duration'],
        title='Charging Sessions Over Time',
        labels={
            'date': 'Date',
            'total_kwh': 'Energy Delivered (kWh)',
            'peak_kw': 'Peak Power (kW)',
            'cost_per_kwh': 'Cost per kWh ($)'
        },
        color_continuous_scale='Viridis'
    )
    
    figures['time_series'].update_layout(
        xaxis_title='Date',
        yaxis_title='Energy Delivered (kWh)',
        hovermode='closest'
    )
    
    # Histogram of peak power
    figures['peak_kw_histogram'] = px.histogram(
        data,
        x='peak_kw',
        nbins=20,
        title='Distribution of Peak Charging Power',
        labels={'peak_kw': 'Peak Power (kW)'},
        color_discrete_sequence=['#3366CC']
    )
    
    figures['peak_kw_histogram'].update_layout(
        xaxis_title='Peak Power (kW)',
        yaxis_title='Number of Sessions'
    )
    
    # Energy delivered by location
    location_kwh = data.groupby('location')['total_kwh'].sum().reset_index()
    location_kwh = location_kwh.sort_values('total_kwh', ascending=False)
    
    figures['kwh_by_location'] = px.bar(
        location_kwh,
        x='location',
        y='total_kwh',
        title='Total Energy by Location',
        labels={
            'location': 'Location',
            'total_kwh': 'Total Energy (kWh)'
        },
        color='total_kwh',
        color_continuous_scale='Viridis'
    )
    
    figures['kwh_by_location'].update_layout(
        xaxis_title='Location',
        yaxis_title='Total Energy (kWh)',
        xaxis={'categoryorder':'total descending'}
    )
    
    # Time series of costs
    figures['cost_time_series'] = px.line(
        data,
        x='date',
        y='total_cost',
        title='Charging Costs Over Time',
        labels={
            'date': 'Date',
            'total_cost': 'Total Cost ($)'
        }
    )
    
    figures['cost_time_series'].update_layout(
        xaxis_title='Date',
        yaxis_title='Total Cost ($)'
    )
    
    # Add monthly aggregate
    monthly_data = data.copy()
    monthly_data['month'] = monthly_data['date'].dt.to_period('M')
    monthly_agg = monthly_data.groupby('month').agg({
        'total_cost': 'sum',
        'total_kwh': 'sum'
    }).reset_index()
    monthly_agg['month'] = monthly_agg['month'].dt.to_timestamp()
    
    figures['cost_time_series'].add_trace(
        go.Scatter(
            x=monthly_agg['month'],
            y=monthly_agg['total_cost'],
            mode='lines+markers',
            name='Monthly Total',
            line=dict(width=3, dash='dash'),
            marker=dict(size=10)
        )
    )
    
    # Cost per kWh over time
    # Convert size parameter explicitly
    total_kwh_values = data['total_kwh'].fillna(5).tolist()  # Use default size for missing values
    
    figures['cost_per_kwh'] = px.scatter(
        data,
        x='date',
        y='cost_per_kwh',
        color='location',
        size=total_kwh_values,  # Pass as explicit list
        title='Cost per kWh Over Time',
        labels={
            'date': 'Date',
            'cost_per_kwh': 'Cost per kWh ($)',
            'location': 'Location',
            'total_kwh': 'Energy Delivered (kWh)'
        }
    )
    
    figures['cost_per_kwh'].update_layout(
        xaxis_title='Date',
        yaxis_title='Cost per kWh ($)'
    )
    
    # Charging duration analysis
    # Convert size parameter to list
    total_cost_values = data['total_cost'].fillna(5).tolist()  # Use default size for missing values
    
    figures['charging_duration'] = px.scatter(
        data,
        x='total_kwh',
        y='peak_kw',
        size=total_cost_values,  # Pass as explicit list
        color='cost_per_kwh',
        hover_name='location',
        hover_data=['date', 'duration'],
        title='Charging Efficiency Analysis',
        labels={
            'total_kwh': 'Energy Delivered (kWh)',
            'peak_kw': 'Peak Power (kW)',
            'total_cost': 'Total Cost ($)',
            'cost_per_kwh': 'Cost per kWh ($)'
        },
        color_continuous_scale='Viridis'
    )
    
    figures['charging_duration'].update_layout(
        xaxis_title='Energy Delivered (kWh)',
        yaxis_title='Peak Power (kW)'
    )
    
    # Cost by location
    location_cost = data.groupby('location').agg({
        'total_cost': 'sum',
        'total_kwh': 'sum'
    }).reset_index()
    location_cost['avg_cost_per_kwh'] = location_cost['total_cost'] / location_cost['total_kwh']
    location_cost = location_cost.sort_values('total_cost', ascending=False)
    
    figures['cost_by_location'] = px.bar(
        location_cost,
        x='location',
        y='total_cost',
        title='Total Cost by Location',
        labels={
            'location': 'Location',
            'total_cost': 'Total Cost ($)'
        },
        color='avg_cost_per_kwh',
        color_continuous_scale='RdYlGn_r',
        hover_data=['total_kwh', 'avg_cost_per_kwh']
    )
    
    figures['cost_by_location'].update_layout(
        xaxis_title='Location',
        yaxis_title='Total Cost ($)',
        xaxis={'categoryorder':'total descending'}
    )
    
    return figures
