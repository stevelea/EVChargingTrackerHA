import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def calculate_distances(data):
    """
    Calculate distances traveled between charging sessions based on odometer readings
    
    Args:
        data: DataFrame containing charging data with odometer column
        
    Returns:
        DataFrame with additional distance column
    """
    # Check if there are any odometer readings
    if 'odometer' not in data.columns or data['odometer'].isna().all():
        # No odometer data available
        return data
    
    # Make a copy of the dataframe to avoid modifying the original
    df = data.copy()
    
    # Ensure the data is sorted by date
    df = df.sort_values('date')
    
    # Calculate the distance traveled since last charge
    df['distance'] = df['odometer'].diff()
    
    # Replace negative values with NaN (happens if odometer readings aren't in sequence)
    df.loc[df['distance'] < 0, 'distance'] = np.nan
    
    # Calculate cost per km where possible
    df['cost_per_km'] = df['total_cost'] / df['distance']
    df['kwh_per_km'] = df['total_kwh'] / df['distance']
    
    # Replace infinite values with NaN
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    
    return df

def create_visualizations(data):
    """
    Create interactive visualizations of the charging data
    
    Args:
        data: DataFrame containing charging data
        
    Returns:
        Dictionary of plotly figures
    """
    # Calculate distances if odometer data is available
    data = calculate_distances(data)
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
    # Create a fixed size value for all points if peak_kw is missing or contains invalid values
    peak_kw_values = None
    if 'peak_kw' in data.columns:
        try:
            # First ensure it's a numeric series, coercing invalid values to NaN
            numeric_peak_kw = pd.to_numeric(data['peak_kw'], errors='coerce')
            
            # Then replace NaN values with a default
            numeric_peak_kw = numeric_peak_kw.fillna(5.0)
            
            # Replace 0 values with the default
            numeric_peak_kw = numeric_peak_kw.replace(0, 5.0)
            
            # Convert to a Python list (not a pandas Series)
            peak_kw_values = numeric_peak_kw.tolist()
            
            # Verify each value is actually a float (or an int)
            peak_kw_values = [float(val) for val in peak_kw_values]
        except Exception as e:
            print(f"Error converting peak_kw: {str(e)}")
            # If conversion fails, create a list of fixed values
            peak_kw_values = [5.0] * len(data)
    
    # Create scatter plot with or without variable size
    if peak_kw_values:
        figures['time_series'] = px.scatter(
            plot_data,  # Use pre-converted data
            x='date',
            y='total_kwh',
            size=peak_kw_values,  # Pass as explicit list of numeric values
            color='cost_per_kwh',
            hover_name='location',
            hover_data=['provider', 'total_cost', 'duration'],
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
    else:
        # Create scatter plot without variable size
        figures['time_series'] = px.scatter(
            plot_data,  # Use pre-converted data
            x='date',
            y='total_kwh',
            color='cost_per_kwh',
            hover_name='location',
            hover_data=['provider', 'total_cost', 'duration'],
            title='Charging Sessions Over Time',
            labels={
                'date': 'Date',
                'total_kwh': 'Energy Delivered (kWh)',
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
    
    # Histogram of peak power - with error handling for missing or invalid peak_kw data
    if 'peak_kw' in data.columns and data['peak_kw'].notna().any():
        try:
            # Ensure we have valid numeric data
            valid_peak_data = data[data['peak_kw'].notna()].copy()
            valid_peak_data['peak_kw'] = pd.to_numeric(valid_peak_data['peak_kw'], errors='coerce')
            valid_peak_data = valid_peak_data.dropna(subset=['peak_kw'])
            
            if len(valid_peak_data) > 0:
                figures['peak_kw_histogram'] = px.histogram(
                    valid_peak_data,
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
            else:
                # Fallback for no valid peak_kw data
                figures['peak_kw_histogram'] = go.Figure()
                figures['peak_kw_histogram'].add_annotation(
                    text="No valid peak power data available",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16)
                )
                figures['peak_kw_histogram'].update_layout(
                    title='Distribution of Peak Charging Power (No Data)'
                )
        except Exception as e:
            print(f"Error creating peak_kw_histogram: {str(e)}")
            # Create an empty figure with error message
            figures['peak_kw_histogram'] = go.Figure()
            figures['peak_kw_histogram'].add_annotation(
                text="Error creating peak power histogram",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            figures['peak_kw_histogram'].update_layout(
                title='Distribution of Peak Charging Power (Error)'
            )
    else:
        # If peak_kw column doesn't exist or has no data
        figures['peak_kw_histogram'] = go.Figure()
        figures['peak_kw_histogram'].add_annotation(
            text="No peak power data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        figures['peak_kw_histogram'].update_layout(
            title='Distribution of Peak Charging Power (No Data)'
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
    # Convert size parameter explicitly and ensure it's properly converted to numeric values
    total_kwh_values = data['total_kwh'].apply(lambda x: float(x) if pd.notnull(x) else 5.0).tolist()
    
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
    # Convert size parameter to list and ensure it contains proper numeric values
    total_cost_values = []
    for val in data['total_cost']:
        try:
            if pd.notnull(val) and val != 0:
                total_cost_values.append(float(val))
            else:
                total_cost_values.append(5.0)  # Default size
        except:
            total_cost_values.append(5.0)  # Default for unconvertible values
    
    # Create a fallback version if peak_kw is missing or problematic
    if 'peak_kw' in data.columns and data['peak_kw'].notna().any():
        try:
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
        except Exception as e:
            print(f"Error creating charging_duration scatter plot: {str(e)}")
            # Fallback to a different visualization without peak_kw
            figures['charging_duration'] = px.scatter(
                plot_data,
                x='total_kwh',
                y='total_cost',
                size=total_cost_values,
                color='cost_per_kwh',
                hover_name='location',
                hover_data=['provider', 'date', 'duration'],
                title='Charging Cost vs Energy Analysis',
                labels={
                    'total_kwh': 'Energy Delivered (kWh)',
                    'total_cost': 'Total Cost ($)',
                    'cost_per_kwh': 'Cost per kWh ($)',
                    'provider': 'Provider'
                },
                color_continuous_scale='Viridis'
            )
    else:
        # If peak_kw is not available, create an alternative visualization
        figures['charging_duration'] = px.scatter(
            plot_data,
            x='total_kwh',
            y='total_cost',
            size=total_cost_values,
            color='cost_per_kwh',
            hover_name='location',
            hover_data=['provider', 'date', 'duration'],
            title='Charging Cost vs Energy Analysis',
            labels={
                'total_kwh': 'Energy Delivered (kWh)',
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
    
    # Provider comparison - added for Tesla API integration
    if 'provider' in data.columns and len(data['provider'].unique()) > 1:
        # Group by provider for comparison
        provider_stats = data.groupby('provider').agg({
            'total_cost': 'sum',
            'total_kwh': 'sum',
            'peak_kw': 'mean',
            'date': 'count'  # Count of sessions
        }).reset_index()
        
        # Calculate average cost per kWh for each provider
        provider_stats['avg_cost_per_kwh'] = provider_stats['total_cost'] / provider_stats['total_kwh']
        provider_stats = provider_stats.rename(columns={'date': 'sessions'})
        
        # Sort by total cost
        provider_stats = provider_stats.sort_values('total_cost', ascending=False)
        
        # Create cost comparison chart
        figures['provider_cost_comparison'] = px.bar(
            provider_stats,
            x='provider',
            y='total_cost',
            title='Cost Comparison by Provider',
            labels={
                'provider': 'Provider',
                'total_cost': 'Total Cost ($)'
            },
            color='avg_cost_per_kwh',
            color_continuous_scale='RdYlGn_r',
            hover_data=['total_kwh', 'avg_cost_per_kwh', 'sessions']
        )
        
        figures['provider_cost_comparison'].update_layout(
            xaxis_title='Provider',
            yaxis_title='Total Cost ($)'
        )
        
        # Create kwh comparison chart - safely handle peak_kw coloring
        try:
            # Check if peak_kw has any valid data
            if 'peak_kw' in provider_stats.columns and provider_stats['peak_kw'].notna().any():
                # Create with peak_kw coloring
                figures['provider_kwh_comparison'] = px.bar(
                    provider_stats,
                    x='provider',
                    y='total_kwh',
                    title='Energy Delivered by Provider',
                    labels={
                        'provider': 'Provider', 
                        'total_kwh': 'Total Energy (kWh)'
                    },
                    color='peak_kw',
                    color_continuous_scale='Viridis',
                    hover_data=['sessions', 'avg_cost_per_kwh']
                )
            else:
                # Create without problematic peak_kw coloring
                figures['provider_kwh_comparison'] = px.bar(
                    provider_stats,
                    x='provider',
                    y='total_kwh',
                    title='Energy Delivered by Provider',
                    labels={
                        'provider': 'Provider', 
                        'total_kwh': 'Total Energy (kWh)'
                    },
                    color='avg_cost_per_kwh',  # Use cost instead of peak_kw
                    color_continuous_scale='RdYlGn_r',
                    hover_data=['sessions', 'avg_cost_per_kwh']
                )
        except Exception as e:
            print(f"Error creating provider_kwh_comparison: {str(e)}")
            # Fallback to simpler version without color scale
            figures['provider_kwh_comparison'] = px.bar(
                provider_stats,
                x='provider',
                y='total_kwh',
                title='Energy Delivered by Provider',
                labels={
                    'provider': 'Provider', 
                    'total_kwh': 'Total Energy (kWh)'
                },
                hover_data=['sessions', 'avg_cost_per_kwh']
            )
        
        figures['provider_kwh_comparison'].update_layout(
            xaxis_title='Provider',
            yaxis_title='Total Energy (kWh)'
        )
        
        # Add to dashboard preferences in the app (this will be handled in app.py)
    
    # Add odometer and efficiency visualizations if data is available
    # First, check if we have odometer and distance columns
    if 'odometer' in data.columns and data['odometer'].notna().any():
        # Odometer readings over time
        figures['odometer_time_series'] = px.line(
            data.sort_values('date'),
            x='date',
            y='odometer',
            title='Odometer Readings Over Time',
            labels={
                'date': 'Date',
                'odometer': 'Odometer Reading (km)'
            },
            markers=True
        )
        
        figures['odometer_time_series'].update_layout(
            xaxis_title='Date',
            yaxis_title='Odometer Reading (km)'
        )
        
        # If we have calculated distances between charges
        if 'distance' in data.columns and data['distance'].notna().any():
            # Energy efficiency visualization (kWh per km)
            efficiency_data = data[data['kwh_per_km'].notna() & 
                                  (data['kwh_per_km'] > 0) & 
                                  (data['kwh_per_km'] < 1)]  # Filter out extreme outliers
            
            if len(efficiency_data) > 0:
                figures['energy_efficiency'] = px.scatter(
                    efficiency_data.sort_values('date'),
                    x='date',
                    y='kwh_per_km',
                    size='total_kwh',
                    color='provider',
                    hover_name='location',
                    hover_data=['distance', 'total_kwh'],
                    title='Energy Efficiency Over Time (kWh per km)',
                    labels={
                        'date': 'Date',
                        'kwh_per_km': 'Energy Consumption (kWh/km)',
                        'provider': 'Provider',
                        'distance': 'Distance (km)',
                        'total_kwh': 'Energy (kWh)'
                    }
                )
                
                # Add a rolling average line
                if len(efficiency_data) >= 3:  # Need at least 3 points for moving average
                    # Sort by date for proper rolling average
                    eff_sorted = efficiency_data.sort_values('date')
                    eff_sorted['rolling_efficiency'] = eff_sorted['kwh_per_km'].rolling(
                        window=3, min_periods=1).mean()
                    
                    figures['energy_efficiency'].add_trace(
                        go.Scatter(
                            x=eff_sorted['date'],
                            y=eff_sorted['rolling_efficiency'],
                            mode='lines',
                            name='3-point Moving Avg',
                            line=dict(color='red', width=2)
                        )
                    )
                
                figures['energy_efficiency'].update_layout(
                    xaxis_title='Date',
                    yaxis_title='Energy Consumption (kWh/km)'
                )
            
            # Cost per km visualization
            cost_per_km_data = data[data['cost_per_km'].notna() & 
                                   (data['cost_per_km'] > 0) & 
                                   (data['cost_per_km'] < 1)]  # Filter outliers
            
            if len(cost_per_km_data) > 0:
                figures['cost_per_km'] = px.scatter(
                    cost_per_km_data.sort_values('date'),
                    x='date',
                    y='cost_per_km',
                    size='total_cost',
                    color='provider',
                    hover_name='location',
                    hover_data=['distance', 'total_cost'],
                    title='Cost Efficiency Over Time ($ per km)',
                    labels={
                        'date': 'Date',
                        'cost_per_km': 'Cost per km ($)',
                        'provider': 'Provider',
                        'distance': 'Distance (km)',
                        'total_cost': 'Total Cost ($)'
                    }
                )
                
                # Add a rolling average line
                if len(cost_per_km_data) >= 3:  # Need at least 3 points for moving average
                    # Sort by date for proper rolling average
                    cost_sorted = cost_per_km_data.sort_values('date')
                    cost_sorted['rolling_cost_per_km'] = cost_sorted['cost_per_km'].rolling(
                        window=3, min_periods=1).mean()
                    
                    figures['cost_per_km'].add_trace(
                        go.Scatter(
                            x=cost_sorted['date'],
                            y=cost_sorted['rolling_cost_per_km'],
                            mode='lines',
                            name='3-point Moving Avg',
                            line=dict(color='red', width=2)
                        )
                    )
                
                figures['cost_per_km'].update_layout(
                    xaxis_title='Date',
                    yaxis_title='Cost per km ($)'
                )
    
    return figures
