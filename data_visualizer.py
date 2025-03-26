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
    
    # Normalize datetime timezone handling for date column
    if 'date' in data.columns:
        # First ensure the column is datetime
        data['date'] = pd.to_datetime(data['date'], errors='coerce')
        
        # Handle mixed timezone-aware and timezone-naive timestamps by converting all to UTC and then removing timezone
        # Make timezone-naive timestamps timezone-aware (assume UTC)
        data['date'] = data['date'].apply(
            lambda x: x.tz_localize('UTC') if x is not None and x.tzinfo is None else x
        )
        
        # Then make all timestamps timezone-naive for consistent comparison
        data['date'] = data['date'].apply(
            lambda x: x.tz_localize(None) if x is not None and x.tzinfo is not None else x
        )
    
    # Now sort by date after timezone normalization
    try:
        data = data.sort_values('date')
    except TypeError:
        # If there's still an issue, we'll handle it gracefully
        print("Warning: Unable to sort by date due to inconsistent timezone information")
    
    # Ensure numeric fields are properly converted to float
    numeric_columns = ['total_kwh', 'peak_kw', 'cost_per_kwh', 'total_cost']
    for col in numeric_columns:
        if col in data.columns:
            # Handle NaN and None values by filling with 0
            data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
    
    # Pre-convert all series to lists for plotly
    # This prevents the "narwhals.stable.v1.Series" error
    plot_data = data.copy()
    
    # First ensure all numeric columns are proper Python floats
    for column in plot_data.columns:
        if column in ['total_kwh', 'peak_kw', 'cost_per_kwh', 'total_cost']:
            try:
                # Convert to numeric first, then fill NaN values, then convert to Python list
                plot_data[column] = pd.to_numeric(plot_data[column], errors='coerce').fillna(0).tolist()
            except Exception as e:
                print(f"Error converting {column}: {str(e)}")
                # If conversion fails, use a list of zeros with the same length
                plot_data[column] = [0] * len(plot_data)
        elif not pd.api.types.is_datetime64_any_dtype(plot_data[column]):
            try:
                # For non-numeric, non-datetime columns, just convert to list
                plot_data[column] = plot_data[column].tolist()
            except Exception as e:
                print(f"Error converting {column}: {str(e)}")
                # Skip columns that can't be converted
    
    # Time series of charging sessions
    # Use default size for missing values with explicit list
    peak_kw_values = data['peak_kw'].fillna(5).tolist()
    
    figures['time_series'] = px.scatter(
        plot_data,  # Use pre-converted data
        x='date',
        y='total_kwh',
        size=peak_kw_values,  # Pass as explicit list 
        color='cost_per_kwh',
        hover_name='location',
        hover_data=['provider', 'total_cost', 'peak_kw', 'duration'],
        title='Charging Sessions Over Time',
        labels={
            'date': 'Date',
            'total_kwh': 'Energy Delivered (kWh)',
            'peak_kw': 'Peak Power (kW)',
            'cost_per_kwh': 'Cost per kWh ($)',
            'provider': 'Provider'
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
    try:
        # Make sure we've got proper datetime objects
        monthly_data = data.copy()
        # Ensure date column is datetime
        if 'date' in monthly_data.columns:
            try:
                # Convert date to datetime if it's not already
                if not pd.api.types.is_datetime64_any_dtype(monthly_data['date']):
                    monthly_data['date'] = pd.to_datetime(monthly_data['date'], errors='coerce')
                
                # Ensure all dates have consistent timezone handling
                # First localize naive timestamps to UTC
                monthly_data['date'] = monthly_data['date'].apply(
                    lambda x: x.tz_localize('UTC') if x is not None and x.tzinfo is None else x
                )
                # Then make all timestamps naive for consistent comparison
                monthly_data['date'] = monthly_data['date'].apply(
                    lambda x: x.tz_localize(None) if x is not None and x.tzinfo is not None else x
                )
                
                # Extract month for aggregation without using dt accessor
                monthly_data['month_year'] = monthly_data['date'].apply(
                    lambda x: pd.Timestamp(year=x.year, month=x.month, day=1) if pd.notnull(x) else None
                )
                
                # Group by the extracted month/year
                monthly_agg = monthly_data.groupby('month_year').agg({
                    'total_cost': 'sum',
                    'total_kwh': 'sum'
                }).reset_index()
                
                # Rename column for consistency
                monthly_agg = monthly_agg.rename(columns={'month_year': 'month'})
            except Exception as e:
                # Fallback if date conversion fails
                print(f"Error in monthly aggregation: {str(e)}")
                monthly_agg = pd.DataFrame({
                    'month': [data['date'].min()],  # Use min date as a fallback
                    'total_cost': [data['total_cost'].sum()],
                    'total_kwh': [data['total_kwh'].sum()]
                })
        else:
            # Fallback if no date column
            monthly_agg = pd.DataFrame({
                'month': [pd.Timestamp.now()],
                'total_cost': [data['total_cost'].sum()],
                'total_kwh': [data['total_kwh'].sum()]
            })
    except Exception as e:
        # Last-resort fallback
        print(f"Monthly aggregation failed: {str(e)}")
        monthly_agg = pd.DataFrame({
            'month': [pd.Timestamp.now()],
            'total_cost': [0],
            'total_kwh': [0]
        })
    
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
        plot_data,  # Use pre-converted data
        x='date',
        y='cost_per_kwh',
        color='provider',  # Changed from location to provider
        size=total_kwh_values,  # Pass as explicit list
        title='Cost per kWh Over Time by Provider',
        labels={
            'date': 'Date',
            'cost_per_kwh': 'Cost per kWh ($)',
            'provider': 'Provider',
            'total_kwh': 'Energy Delivered (kWh)'
        },
        hover_data=['location', 'total_cost']
    )
    
    figures['cost_per_kwh'].update_layout(
        xaxis_title='Date',
        yaxis_title='Cost per kWh ($)'
    )
    
    # Charging duration analysis
    # Convert size parameter to list
    total_cost_values = data['total_cost'].fillna(5).tolist()  # Use default size for missing values
    
    figures['charging_duration'] = px.scatter(
        plot_data,  # Use pre-converted data
        x='total_kwh',
        y='peak_kw',
        size=total_cost_values,  # Pass as explicit list
        color='cost_per_kwh',
        hover_name='location',
        hover_data=['provider', 'date', 'duration'],
        title='Charging Efficiency Analysis',
        labels={
            'total_kwh': 'Energy Delivered (kWh)',
            'peak_kw': 'Peak Power (kW)',
            'total_cost': 'Total Cost ($)',
            'cost_per_kwh': 'Cost per kWh ($)',
            'provider': 'Provider'
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
