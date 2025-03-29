import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def safe_convert_to_list(series_obj, default_value=None):
    """
    Safely convert any type of Series object to a standard Python list.
    
    Args:
        series_obj: The Series-like object to convert
        default_value: Default value to use for failed conversions
        
    Returns:
        A standard Python list
    """
    # Handle None or already-list objects
    if series_obj is None:
        return [] if default_value is None else [default_value]
    if isinstance(series_obj, list):
        return series_obj
        
    # Try different conversion methods
    try:
        # Check object type to detect Series objects (including narwhals.stable.v1.Series)
        obj_type = str(type(series_obj))
        if "Series" in obj_type:
            # For Series, manually iterate through values
            result = []
            for i in range(len(series_obj)):
                try:
                    if hasattr(series_obj, "iloc"):
                        val = series_obj.iloc[i]
                    elif hasattr(series_obj, "__getitem__"):
                        val = series_obj[i]
                    else:
                        val = default_value
                    result.append(val)
                except:
                    result.append(default_value)
            return result
        
        # For pandas Series with to_list method
        elif hasattr(series_obj, "to_list"):
            return series_obj.to_list()
            
        # For numpy arrays or other objects with tolist method
        elif hasattr(series_obj, "tolist"):
            return series_obj.tolist()
            
        # For standard iterables that can be directly converted to list
        elif hasattr(series_obj, "__iter__"):
            return list(series_obj)
            
        # Otherwise, wrap in a list 
        else:
            return [series_obj]
            
    except Exception as e:
        print(f"Error in safe_convert_to_list: {str(e)}")
        if default_value is None:
            return []
        return [default_value]

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
    
    # Check which column names are being used (for backwards compatibility)
    cost_col = 'cost' if 'cost' in df.columns else 'total_cost'
    energy_col = 'energy_kwh' if 'energy_kwh' in df.columns else 'total_kwh'
    
    # Calculate cost per km where possible
    df['cost_per_km'] = df[cost_col] / df['distance']
    df['kwh_per_km'] = df[energy_col] / df['distance']
    
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
    
    # Check which column names are being used (for backwards compatibility)
    energy_col = 'energy_kwh' if 'energy_kwh' in data.columns else 'total_kwh'
    cost_col = 'cost' if 'cost' in data.columns else 'total_cost'
    
    # Create column mappings for consistency
    column_mappings = {
        'total_kwh': energy_col,
        'total_cost': cost_col
    }
    
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
            # Generate a list of default values first
            peak_kw_values = [5.0] * len(data)
            print(f"Creating default peak_kw_values list with {len(peak_kw_values)} items")
            
            # Skip complex conversion if the data is empty
            if len(data) == 0:
                print("Data is empty, using default values")
            else:
                print(f"Converting peak_kw column of type: {type(data['peak_kw'])}")
                
                # Handle different types that might be in the peak_kw column
                
                # Special handling for any Series objects (including narwhals.stable.v1.Series)
                if "Series" in str(type(data['peak_kw'])):
                    print(f"Detected a Series object: {type(data['peak_kw'])}, using item-by-item conversion")
                    
                    # For narwhals Series, we use a completely different approach that doesn't rely on built-in methods
                    # We'll use a for loop with index access and explicit type conversion
                    for i in range(len(data)):
                        try:
                            # Use a more reliable way to extract individual values from Series
                            if hasattr(data['peak_kw'], 'iloc'):
                                val = data['peak_kw'].iloc[i]
                            else:
                                # Try direct index access as fallback
                                val = data['peak_kw'][i]
                                
                            # Handle None and convert valid values to Python float
                            if val is None or pd.isna(val) or val == 0:
                                peak_kw_values[i] = 5.0
                            else:
                                try:
                                    float_val = float(val)
                                    # Use default for negative or very small values
                                    peak_kw_values[i] = float_val if float_val > 0.1 else 5.0
                                except (ValueError, TypeError):
                                    # Keep default for conversion errors
                                    peak_kw_values[i] = 5.0
                        except (IndexError, KeyError, AttributeError) as e:
                            print(f"Error accessing peak_kw at index {i}: {str(e)}")
                            # Keep default value
                            peak_kw_values[i] = 5.0
                
                # For pandas Series or other types with standard attributes
                elif hasattr(data['peak_kw'], 'to_list'):
                    print("Using pandas Series to_list() method")
                    # This is a pandas Series with to_list method
                    try:
                        raw_values = data['peak_kw'].to_list()
                        for i, val in enumerate(raw_values):
                            if val is None or pd.isna(val) or val == 0:
                                peak_kw_values[i] = 5.0
                            else:
                                try:
                                    peak_kw_values[i] = float(val)
                                except (ValueError, TypeError):
                                    peak_kw_values[i] = 5.0
                    except Exception as e:
                        print(f"Error converting with to_list(): {str(e)}")
                
                # For numpy arrays or other objects with tolist method
                elif hasattr(data['peak_kw'], 'tolist'):
                    print("Using tolist() method")
                    try:
                        raw_values = data['peak_kw'].tolist()
                        for i, val in enumerate(raw_values):
                            if val is None or pd.isna(val) or val == 0:
                                peak_kw_values[i] = 5.0
                            else:
                                try:
                                    peak_kw_values[i] = float(val)
                                except (ValueError, TypeError):
                                    peak_kw_values[i] = 5.0
                    except Exception as e:
                        print(f"Error converting with tolist(): {str(e)}")
                
                # For standard objects that can be directly converted to list
                elif hasattr(data['peak_kw'], '__iter__'):
                    print("Using direct list conversion")
                    try:
                        raw_values = list(data['peak_kw'])
                        for i, val in enumerate(raw_values):
                            if val is None or pd.isna(val) or val == 0:
                                peak_kw_values[i] = 5.0
                            else:
                                try:
                                    peak_kw_values[i] = float(val)
                                except (ValueError, TypeError):
                                    peak_kw_values[i] = 5.0
                    except Exception as e:
                        print(f"Error converting with list(): {str(e)}")
                
                else:
                    # Unable to convert with standard methods, use item-by-item conversion with for loop
                    print("Fallback to manual item-by-item conversion")
                    for i in range(len(data)):
                        try:
                            # Try to extract the value at this index
                            val = None
                            try:
                                # Try different common access methods
                                if hasattr(data['peak_kw'], 'iat'):
                                    val = data['peak_kw'].iat[i]
                                elif hasattr(data['peak_kw'], 'iloc'):
                                    val = data['peak_kw'].iloc[i]
                                elif hasattr(data['peak_kw'], '__getitem__'):
                                    val = data['peak_kw'][i]
                                else:
                                    # Give up and use default
                                    continue
                                    
                                # Convert the value to float
                                if val is None or pd.isna(val) or val == 0:
                                    peak_kw_values[i] = 5.0
                                else:
                                    try:
                                        peak_kw_values[i] = float(val)
                                    except (ValueError, TypeError):
                                        peak_kw_values[i] = 5.0
                            except Exception as e:
                                print(f"Error accessing peak_kw at position {i}: {str(e)}")
                        except Exception as e:
                            print(f"Unexpected error at position {i}: {str(e)}")
            
            # Final validation - ensure all values are Python floats and handle any remaining issue
            print(f"Final validation of {len(peak_kw_values)} peak_kw values")
            for i in range(len(peak_kw_values)):
                try:
                    # Make sure each value is a valid Python float
                    peak_kw_values[i] = float(peak_kw_values[i]) if peak_kw_values[i] is not None else 5.0
                    # Replace any invalid values (NaN, negative, etc)
                    if pd.isna(peak_kw_values[i]) or peak_kw_values[i] <= 0:
                        peak_kw_values[i] = 5.0
                except Exception:
                    # Final fallback
                    peak_kw_values[i] = 5.0
                
        except Exception as e:
            print(f"Error in peak_kw conversion: {str(e)}")
            # If all conversion attempts fail, create a list of fixed values
            peak_kw_values = [5.0] * len(data)
        
        # Final size check
        if len(peak_kw_values) != len(data):
            print(f"Final length mismatch: peak_kw_values ({len(peak_kw_values)}) vs data ({len(data)})")
            peak_kw_values = [5.0] * len(data)
    
    # Create scatter plot with or without variable size
    if peak_kw_values:
        # Ensure all data is in compatible format for plotly using our safe converter
        plot_dict = {
            'date': safe_convert_to_list(plot_data['date']),
            energy_col: safe_convert_to_list(plot_data[energy_col], 0.0),
            'cost_per_kwh': safe_convert_to_list(plot_data['cost_per_kwh'], 0.0),
            'location': safe_convert_to_list(plot_data['location'], 'Unknown'),
            'provider': safe_convert_to_list(plot_data['provider'] if 'provider' in plot_data else ['Unknown'] * len(plot_data), 'Unknown'),
            cost_col: safe_convert_to_list(plot_data[cost_col], 0.0)
        }
        
        # Convert peak_kw_values to a list of standard Python floats to avoid any Series issues
        # First double-check the values are all standard Python floats
        safe_peak_kw = []
        for val in peak_kw_values:
            try:
                safe_peak_kw.append(float(val))
            except (TypeError, ValueError):
                safe_peak_kw.append(5.0)
        
        figures['time_series'] = px.scatter(
            plot_dict,  # Use dictionary instead of DataFrame to avoid Series conversion issues
            x='date',
            y=energy_col,  # Use the correct column name
            size=safe_peak_kw,  # Pass as explicit list of Python floats
            color='cost_per_kwh',
            hover_name='location',
            hover_data={
                "provider": True,  # Include in hover data
                cost_col: True  # Include in hover data
            },
            title='Charging Sessions Over Time',
            labels={
                'date': 'Date',
                energy_col: 'Energy Delivered (kWh)',  # Use the correct column name
                'peak_kw': 'Peak Power (kW)',
                'cost_per_kwh': 'Cost per kWh ($)',
                'provider': 'Provider',
                cost_col: 'Total Cost ($)'  # Use the correct column name
            },
            color_continuous_scale='Viridis'
        )
    else:
        # Create scatter plot without variable size
        # Convert to dictionary using our safe conversion helper to avoid Series issues
        plot_dict = {
            'date': safe_convert_to_list(plot_data['date']),
            energy_col: safe_convert_to_list(plot_data[energy_col], 0.0),
            'cost_per_kwh': safe_convert_to_list(plot_data['cost_per_kwh'], 0.0),
            'location': safe_convert_to_list(plot_data['location'], 'Unknown'),
            'provider': safe_convert_to_list(plot_data['provider'] if 'provider' in plot_data else ['Unknown'] * len(plot_data), 'Unknown'),
            cost_col: safe_convert_to_list(plot_data[cost_col], 0.0)
        }
        
        figures['time_series'] = px.scatter(
            plot_dict,  # Use dictionary instead of DataFrame
            x='date',
            y=energy_col,  # Use the correct column name
            color='cost_per_kwh',
            hover_name='location',
            hover_data={
                "provider": True,  # Include in hover data
                cost_col: True  # Include in hover data
            },
            title='Charging Sessions Over Time',
            labels={
                'date': 'Date',
                energy_col: 'Energy Delivered (kWh)',  # Use the correct column name
                'cost_per_kwh': 'Cost per kWh ($)',
                'provider': 'Provider',
                cost_col: 'Total Cost ($)'  # Use the correct column name
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
    location_kwh = data.groupby('location')[energy_col].sum().reset_index()
    location_kwh = location_kwh.sort_values(energy_col, ascending=False)
    
    figures['kwh_by_location'] = px.bar(
        location_kwh,
        x='location',
        y=energy_col,
        title='Total Energy by Location',
        labels={
            'location': 'Location',
            energy_col: 'Total Energy (kWh)'
        },
        color=energy_col,
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
        y=cost_col,
        title='Charging Costs Over Time',
        labels={
            'date': 'Date',
            cost_col: 'Total Cost ($)'
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
                agg_dict = {
                    cost_col: 'sum',
                    energy_col: 'sum'
                }
                monthly_agg = monthly_data.groupby('month_year').agg(agg_dict).reset_index()
                
                # Rename column for consistency
                monthly_agg = monthly_agg.rename(columns={'month_year': 'month'})
                
                # Ensure we have 'total_cost' for compatibility with older code
                if 'total_cost' not in monthly_agg.columns:
                    monthly_agg['total_cost'] = monthly_agg[cost_col]
            except Exception as e:
                # Fallback if date conversion fails
                print(f"Error in monthly aggregation: {str(e)}")
                monthly_agg = pd.DataFrame({
                    'month': [data['date'].min()],  # Use min date as a fallback
                    'total_cost': [data[cost_col].sum()],
                    energy_col: [data[energy_col].sum()]
                })
        else:
            # Fallback if no date column
            monthly_agg = pd.DataFrame({
                'month': [pd.Timestamp.now()],
                'total_cost': [data[cost_col].sum()],
                energy_col: [data[energy_col].sum()]
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
    total_kwh_values = []
    
    # Process each value individually to ensure proper conversion
    for val in data[energy_col]:
        try:
            # First convert to float safely
            num_val = float(val) if val is not None and pd.notna(val) else 5.0
            # Use default if value is 0
            total_kwh_values.append(5.0 if num_val == 0 else num_val)
        except (ValueError, TypeError):
            # Handle conversion errors
            total_kwh_values.append(5.0)
            
    # Double-check that we have the correct number of values
    if len(total_kwh_values) != len(data):
        print(f"Energy values length mismatch: {len(total_kwh_values)} vs {len(data)}")
        total_kwh_values = [5.0] * len(data)
    
    # Create a clean dictionary for plotly using our safe conversion helper
    cost_plot_dict = {
        'date': safe_convert_to_list(plot_data['date']),
        'cost_per_kwh': safe_convert_to_list(plot_data['cost_per_kwh'], 0.0),
        'provider': safe_convert_to_list(plot_data['provider'] if 'provider' in plot_data else ['Unknown'] * len(plot_data), 'Unknown'),
        'location': safe_convert_to_list(plot_data['location'], 'Unknown'),
        'total_cost': safe_convert_to_list(plot_data['total_cost'] if 'total_cost' in plot_data else [0] * len(plot_data), 0.0)
    }
    
    figures['cost_per_kwh'] = px.scatter(
        cost_plot_dict,  # Use dictionary instead of DataFrame
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
        hover_data={
            'location': True,  # Include in hover data
            'total_cost': True  # Include in hover data
        }
    )
    
    figures['cost_per_kwh'].update_layout(
        xaxis_title='Date',
        yaxis_title='Cost per kWh ($)'
    )
    
    # Charging duration analysis
    # Convert size parameter to list and ensure it contains proper numeric values
    total_cost_values = []
    
    # Process each value individually to ensure proper conversion
    for val in data[cost_col]:
        try:
            # First convert to float safely
            num_val = float(val) if val is not None and pd.notna(val) else 5.0
            # Use default if value is 0
            total_cost_values.append(5.0 if num_val == 0 else num_val)
        except (ValueError, TypeError):
            # Handle conversion errors
            total_cost_values.append(5.0)
            
    # Double-check that we have the correct number of values
    if len(total_cost_values) != len(data):
        print(f"Cost values length mismatch: {len(total_cost_values)} vs {len(data)}")
        total_cost_values = [5.0] * len(data)
    
    # Create a fallback version if peak_kw is missing or problematic
    if 'peak_kw' in data.columns and data['peak_kw'].notna().any():
        try:
            # Create a clean dictionary for plotly using our safe conversion helper
            duration_plot_dict = {
                'total_kwh': safe_convert_to_list(plot_data['total_kwh'], 0.0),
                'peak_kw': safe_convert_to_list(plot_data['peak_kw'], 0.0),
                'cost_per_kwh': safe_convert_to_list(plot_data['cost_per_kwh'], 0.0),
                'location': safe_convert_to_list(plot_data['location'], 'Unknown'),
                'provider': safe_convert_to_list(plot_data['provider'] if 'provider' in plot_data else ['Unknown'] * len(plot_data), 'Unknown'),
                'date': safe_convert_to_list(plot_data['date'])
            }
            
            figures['charging_duration'] = px.scatter(
                duration_plot_dict,  # Use dictionary instead of DataFrame
                x='total_kwh',
                y='peak_kw',
                size=total_cost_values,  # Pass as explicit list
                color='cost_per_kwh',
                hover_name='location',
                hover_data={
                    "provider": True,  # Include in hover data
                    "date": True  # Include in hover data
                },
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
            # Create a clean dictionary for plotly using our safe conversion helper
            fallback_dict = {
                'total_kwh': safe_convert_to_list(plot_data['total_kwh'], 0.0),
                'total_cost': safe_convert_to_list(plot_data['total_cost'], 0.0),
                'cost_per_kwh': safe_convert_to_list(plot_data['cost_per_kwh'], 0.0),
                'location': safe_convert_to_list(plot_data['location'], 'Unknown'),
                'provider': safe_convert_to_list(plot_data['provider'] if 'provider' in plot_data else ['Unknown'] * len(plot_data), 'Unknown'),
                'date': safe_convert_to_list(plot_data['date'])
            }
            
            figures['charging_duration'] = px.scatter(
                fallback_dict,  # Use dictionary instead of DataFrame
                x='total_kwh',
                y='total_cost',
                size=total_cost_values,
                color='cost_per_kwh',
                hover_name='location',
                hover_data={
                    "provider": True,  # Include in hover data
                    "date": True  # Include in hover data
                },
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
        # Create a clean dictionary for plotly using our safe conversion helper
        alt_dict = {
            'total_kwh': safe_convert_to_list(plot_data['total_kwh'], 0.0),
            'total_cost': safe_convert_to_list(plot_data['total_cost'], 0.0),
            'cost_per_kwh': safe_convert_to_list(plot_data['cost_per_kwh'], 0.0),
            'location': safe_convert_to_list(plot_data['location'], 'Unknown'),
            'provider': safe_convert_to_list(plot_data['provider'] if 'provider' in plot_data else ['Unknown'] * len(plot_data), 'Unknown'),
            'date': safe_convert_to_list(plot_data['date'])
        }
        
        figures['charging_duration'] = px.scatter(
            alt_dict,  # Use dictionary instead of DataFrame
            x='total_kwh',
            y='total_cost',
            size=total_cost_values,
            color='cost_per_kwh',
            hover_name='location',
            hover_data={
                "provider": True,  # Include in hover data
                "date": True  # Include in hover data
            },
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
    agg_dict = {
        cost_col: 'sum',
        energy_col: 'sum'
    }
    location_cost = data.groupby('location').agg(agg_dict).reset_index()
    location_cost['avg_cost_per_kwh'] = location_cost[cost_col] / location_cost[energy_col]
    location_cost = location_cost.sort_values(cost_col, ascending=False)
    
    # Ensure we have 'total_cost' and 'total_kwh' for compatibility with older code
    if 'total_cost' not in location_cost.columns:
        location_cost['total_cost'] = location_cost[cost_col]
    if 'total_kwh' not in location_cost.columns:
        location_cost['total_kwh'] = location_cost[energy_col]
    
    figures['cost_by_location'] = px.bar(
        location_cost,
        x='location',
        y=cost_col,
        title='Total Cost by Location',
        labels={
            'location': 'Location',
            cost_col: 'Total Cost ($)'
        },
        color='avg_cost_per_kwh',
        color_continuous_scale='RdYlGn_r',
        hover_data={
            energy_col: True,  # Include in hover data
            'avg_cost_per_kwh': True  # Include in hover data
        }
    )
    
    figures['cost_by_location'].update_layout(
        xaxis_title='Location',
        yaxis_title='Total Cost ($)',
        xaxis={'categoryorder':'total descending'}
    )
    
    # Provider comparison - added for Tesla API integration
    if 'provider' in data.columns and len(data['provider'].unique()) > 1:
        # Group by provider for comparison
        agg_dict = {
            cost_col: 'sum',
            energy_col: 'sum',
            'peak_kw': 'mean',
            'date': 'count'  # Count of sessions
        }
        provider_stats = data.groupby('provider').agg(agg_dict).reset_index()
        
        # Calculate average cost per kWh for each provider
        provider_stats['avg_cost_per_kwh'] = provider_stats[cost_col] / provider_stats[energy_col]
        provider_stats = provider_stats.rename(columns={'date': 'sessions'})
        
        # Ensure we have 'total_cost' and 'total_kwh' for compatibility with older code
        if 'total_cost' not in provider_stats.columns:
            provider_stats['total_cost'] = provider_stats[cost_col]
        if 'total_kwh' not in provider_stats.columns:
            provider_stats['total_kwh'] = provider_stats[energy_col]
        
        # Sort by total cost
        provider_stats = provider_stats.sort_values(cost_col, ascending=False)
        
        # Create cost comparison chart
        figures['provider_cost_comparison'] = px.bar(
            provider_stats,
            x='provider',
            y=cost_col,
            title='Cost Comparison by Provider',
            labels={
                'provider': 'Provider',
                cost_col: 'Total Cost ($)'
            },
            color='avg_cost_per_kwh',
            color_continuous_scale='RdYlGn_r',
            hover_data={
                energy_col: True,  # Include in hover data
                'avg_cost_per_kwh': True,  # Include in hover data
                'sessions': True  # Include in hover data
            }
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
                    y=energy_col,
                    title='Energy Delivered by Provider',
                    labels={
                        'provider': 'Provider', 
                        energy_col: 'Total Energy (kWh)'
                    },
                    color='peak_kw',
                    color_continuous_scale='Viridis',
                    hover_data={
                        'sessions': True,  # Include in hover data
                        'avg_cost_per_kwh': True  # Include in hover data
                    }
                )
            else:
                # Create without problematic peak_kw coloring
                figures['provider_kwh_comparison'] = px.bar(
                    provider_stats,
                    x='provider',
                    y=energy_col,
                    title='Energy Delivered by Provider',
                    labels={
                        'provider': 'Provider', 
                        energy_col: 'Total Energy (kWh)'
                    },
                    color='avg_cost_per_kwh',  # Use cost instead of peak_kw
                    color_continuous_scale='RdYlGn_r',
                    hover_data={
                        'sessions': True,  # Include in hover data
                        'avg_cost_per_kwh': True  # Include in hover data
                    }
                )
        except Exception as e:
            print(f"Error creating provider_kwh_comparison: {str(e)}")
            # Fallback to simpler version without color scale
            figures['provider_kwh_comparison'] = px.bar(
                provider_stats,
                x='provider',
                y=energy_col,
                title='Energy Delivered by Provider',
                labels={
                    'provider': 'Provider', 
                    energy_col: 'Total Energy (kWh)'
                },
                hover_data={
                    'sessions': True,  # Include in hover data
                    'avg_cost_per_kwh': True  # Include in hover data
                }
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
                # Sort data and ensure we have Python native types
                efficiency_data_sorted = efficiency_data.sort_values('date').copy()
                
                # Extract values for size parameter to avoid Series objects
                size_values = []
                for val in efficiency_data_sorted[energy_col]:
                    try:
                        num_val = float(val) if val is not None and pd.notna(val) else 5.0
                        size_values.append(5.0 if num_val == 0 else num_val)
                    except (ValueError, TypeError):
                        size_values.append(5.0)
                        
                # Make sure we have the right number of values
                if len(size_values) != len(efficiency_data_sorted):
                    size_values = [5.0] * len(efficiency_data_sorted)
                    
                figures['energy_efficiency'] = px.scatter(
                    efficiency_data_sorted,
                    x='date',
                    y='kwh_per_km',
                    size=size_values,  # Use converted list of values
                    color='provider',
                    hover_name='location',
                    hover_data={
                        'distance': True,  # Include in hover data
                        energy_col: True  # Include in hover data 
                    },
                    title='Energy Efficiency Over Time (kWh per km)',
                    labels={
                        'date': 'Date',
                        'kwh_per_km': 'Energy Consumption (kWh/km)',
                        'provider': 'Provider',
                        'distance': 'Distance (km)',
                        energy_col: 'Energy (kWh)'
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
                # Sort data and ensure we have Python native types
                cost_per_km_data_sorted = cost_per_km_data.sort_values('date').copy()
                
                # Extract values for size parameter to avoid Series objects
                cost_size_values = []
                for val in cost_per_km_data_sorted[cost_col]:
                    try:
                        num_val = float(val) if val is not None and pd.notna(val) else 5.0
                        cost_size_values.append(5.0 if num_val == 0 else num_val)
                    except (ValueError, TypeError):
                        cost_size_values.append(5.0)
                        
                # Make sure we have the right number of values
                if len(cost_size_values) != len(cost_per_km_data_sorted):
                    cost_size_values = [5.0] * len(cost_per_km_data_sorted)
                
                figures['cost_per_km'] = px.scatter(
                    cost_per_km_data_sorted,
                    x='date',
                    y='cost_per_km',
                    size=cost_size_values,  # Use converted list of values
                    color='provider',
                    hover_name='location',
                    hover_data={
                        'distance': True,  # Include in hover data
                        cost_col: True  # Include in hover data
                    },
                    title='Cost Efficiency Over Time ($ per km)',
                    labels={
                        'date': 'Date',
                        'cost_per_km': 'Cost per km ($)',
                        'provider': 'Provider',
                        'distance': 'Distance (km)',
                        cost_col: 'Total Cost ($)'
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
