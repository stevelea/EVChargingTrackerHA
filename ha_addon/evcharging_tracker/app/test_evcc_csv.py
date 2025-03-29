"""
Test script for EVCC CSV parsing functionality.
This script allows testing the EVCC CSV parser with the sample CSV file.
"""
import os
import sys
import re
import pandas as pd
from data_parser import parse_evcc_csv
import streamlit as st

def extract_peak_kw_from_duration(df):
    """
    Extract peak kW from duration and energy for records without peak_kw values
    """
    # Create a copy of the dataframe
    result_df = df.copy()
    
    # Ensure total_kwh is numeric
    result_df['total_kwh'] = pd.to_numeric(result_df['total_kwh'], errors='coerce')
    
    # Process duration strings to extract hours
    for idx, row in result_df.iterrows():
        if pd.isna(row['peak_kw']) and not pd.isna(row['duration']) and not pd.isna(row['total_kwh']):
            try:
                duration_str = row['duration']
                # Parse duration with format like "1h15m30s"
                hours, minutes, seconds = 0, 0, 0
                
                # Extract hours
                hours_match = re.search(r'(\d+)h', duration_str)
                if hours_match:
                    hours = int(hours_match.group(1))
                
                # Extract minutes
                minutes_match = re.search(r'(\d+)m', duration_str)
                if minutes_match:
                    minutes = int(minutes_match.group(1))
                
                # Extract seconds
                seconds_match = re.search(r'(\d+)s', duration_str)
                if seconds_match:
                    seconds = int(seconds_match.group(1))
                
                # Calculate total hours
                total_hours = hours + (minutes / 60) + (seconds / 3600)
                
                # Calculate peak kW
                if total_hours > 0 and row['total_kwh'] > 0:
                    peak_kw = row['total_kwh'] / total_hours
                    
                    # Cap at reasonable value
                    if peak_kw > 350:  # Max real-world DC charger
                        peak_kw = 350
                        
                    result_df.at[idx, 'peak_kw'] = peak_kw
                    result_df.at[idx, 'peak_kw_calculated'] = True
            except Exception as e:
                print(f"Error calculating peak kW for row {idx}: {str(e)}")
    
    return result_df

def test_parse_evcc_csv():
    """Test the EVCC CSV parser with the sample file"""
    # Set up to support running with or without streamlit
    is_streamlit = 'streamlit' in sys.modules and hasattr(st, 'title')
    
    if is_streamlit:
        st.title("EVCC CSV Parser Test")
        st.write("This tool tests parsing EVCC CSV data")
    
    # Check if sample file exists
    sample_file_path = 'attached_assets/session (2).csv'
    if not os.path.exists(sample_file_path):
        msg = f"Sample file not found at {sample_file_path}"
        print(msg)
        if is_streamlit:
            st.error(msg)
        return
    
    msg = f"Found sample file at {sample_file_path}"
    print(msg)
    if is_streamlit:
        st.success(msg)
    
    # Open and parse the file
    with open(sample_file_path, 'rb') as csv_file:
        msg = "Parsing CSV file..."
        print(msg)
        if is_streamlit:
            st.info(msg)
        
        # Set default cost per kWh to 0.01 as per requirement
        charging_data = parse_evcc_csv(csv_file, default_cost_per_kwh=0.01)
    
    # Print the results
    if charging_data:
        msg = f"Successfully parsed {len(charging_data)} records from EVCC CSV"
        print(msg)
        if is_streamlit:
            st.success(msg)
        
        # Convert to DataFrame for better viewing
        df = pd.DataFrame(charging_data)
        
        # Process duration to extract peak kW when missing
        df = extract_peak_kw_from_duration(df)
        
        # Display sample data
        msg = "\nSample of parsed data (first 5 rows):"
        print(msg)
        print(df.head(5))
        if is_streamlit:
            st.subheader("Sample Data")
            st.dataframe(df.head(10))
        
        # Print column statistics
        print("\nColumns statistics:")
        stats = {}
        for col in df.columns:
            if col in ['date', 'time', 'location', 'provider', 'vehicle']:
                # For string columns, show unique values count
                unique_count = df[col].nunique()
                print(f"{col}: {unique_count} unique values")
                stats[col] = f"{unique_count} unique values"
            elif col in ['total_kwh', 'peak_kw', 'cost_per_kwh', 'total_cost', 'odometer', 'solar_percent']:
                # For numeric columns, show min/max/mean
                try:
                    numeric_col = pd.to_numeric(df[col], errors='coerce')
                    min_val = numeric_col.min()
                    max_val = numeric_col.max()
                    mean_val = numeric_col.mean()
                    print(f"{col}: min={min_val}, max={max_val}, mean={mean_val}")
                    stats[col] = f"min={min_val:.2f}, max={max_val:.2f}, mean={mean_val:.2f}"
                except:
                    print(f"{col}: non-numeric data")
                    stats[col] = "non-numeric data"
                    
        if is_streamlit:
            st.subheader("Column Statistics")
            stats_df = pd.DataFrame(list(stats.items()), columns=['Column', 'Statistics'])
            st.table(stats_df)
            
            # Visualizations
            st.subheader("Visualizations")
            
            try:
                import plotly.express as px
                
                # Ensure date is datetime for plotting
                df['date'] = pd.to_datetime(df['date'])
                
                # Energy over time
                st.subheader("Energy (kWh) Over Time")
                energy_fig = px.scatter(
                    df, 
                    x='date', 
                    y='total_kwh', 
                    size='total_kwh',
                    color='location',
                    hover_data=['vehicle', 'duration']
                )
                st.plotly_chart(energy_fig)
                
                # Duration breakdown
                st.subheader("Charging Duration vs Energy")
                if 'duration' in df.columns:
                    df['duration_str'] = df['duration']
                    duration_fig = px.scatter(
                        df,
                        x='duration_str',
                        y='total_kwh',
                        size='peak_kw',
                        color='location',
                        hover_data=['date', 'vehicle']
                    )
                    st.plotly_chart(duration_fig)
                else:
                    st.warning("Duration data not available")
                
                # Solar percentage
                if 'solar_percent' in df.columns:
                    st.subheader("Solar Percentage")
                    solar_fig = px.histogram(
                        df,
                        x='solar_percent',
                        nbins=20,
                        title='Distribution of Solar Percentage'
                    )
                    st.plotly_chart(solar_fig)
                    
                    # Solar vs Time of day
                    if 'time' in df.columns:
                        df['hour'] = pd.to_datetime(df['time'], format='%H:%M:%S').dt.hour
                        solar_time_fig = px.scatter(
                            df,
                            x='hour',
                            y='solar_percent',
                            color='solar_percent',
                            size='total_kwh',
                            title='Solar Percentage by Hour of Day'
                        )
                        st.plotly_chart(solar_time_fig)
            except Exception as e:
                st.error(f"Error creating visualizations: {str(e)}")
    else:
        msg = "No data parsed from EVCC CSV."
        print(msg)
        if is_streamlit:
            st.error(msg)

if __name__ == "__main__":
    test_parse_evcc_csv()