import re
from datetime import datetime
import pandas as pd
import streamlit as st

def parse_charging_emails(emails):
    """
    Extract EV charging data from email receipts.
    
    This function attempts to parse various formats of EV charging receipts 
    to extract key information like date, time, location, kWh, cost, etc.
    
    Args:
        emails: List of email dictionaries containing subject, body, date, etc.
        
    Returns:
        List of dictionaries containing extracted charging data
    """
    charging_data = []
    
    # Common patterns for different charging networks
    patterns = {
        # Match date patterns in various formats
        'date': [
            r'Date:\s*(\d{1,2}/\d{1,2}/\d{2,4})',
            r'Date:\s*(\w+ \d{1,2}, \d{4})',
            r'Charging Date:\s*(\d{1,2}-\d{1,2}-\d{2,4})',
            r'Transaction Date:\s*(\d{4}-\d{2}-\d{2})'
        ],
        # Match time patterns
        'time': [
            r'Time:\s*(\d{1,2}:\d{2} [APM]{2})',
            r'Start Time:\s*(\d{1,2}:\d{2}:\d{2})',
            r'Charging Time:\s*(\d{1,2}:\d{2} [APM]{2})'
        ],
        # Match location patterns
        'location': [
            r'Location:\s*(.+?)(?:\n|\r|$)',
            r'Station:\s*(.+?)(?:\n|\r|$)',
            r'Charger Location:\s*(.+?)(?:\n|\r|$)'
        ],
        # Match total kWh delivered
        'total_kwh': [
            r'Energy Delivered:\s*([\d.]+)\s*kWh',
            r'Total Energy:\s*([\d.]+)\s*kWh',
            r'kWh:\s*([\d.]+)',
            r'(\d+\.\d+)\s*kWh'
        ],
        # Match peak kW rate
        'peak_kw': [
            r'Peak Power:\s*([\d.]+)\s*kW',
            r'Max Power:\s*([\d.]+)\s*kW',
            r'Peak kW:\s*([\d.]+)'
        ],
        # Match charging duration
        'duration': [
            r'Duration:\s*(.+?)(?:\n|\r|$)',
            r'Charging Time:\s*(.+?)(?:\n|\r|$)',
            r'Time Connected:\s*(.+?)(?:\n|\r|$)'
        ],
        # Match cost per kWh
        'cost_per_kwh': [
            r'Rate:\s*\$([\d.]+)/kWh',
            r'Price per kWh:\s*\$([\d.]+)',
            r'\$([\d.]+)\s*per kWh'
        ],
        # Match total cost
        'total_cost': [
            r'Total:\s*\$([\d.]+)',
            r'Amount:\s*\$([\d.]+)',
            r'Total Cost:\s*\$([\d.]+)',
            r'Total Amount:\s*\$([\d.]+)'
        ]
    }
    
    for email in emails:
        try:
            # Skip emails without bodies
            if not email.get('body'):
                continue
                
            email_body = email['body']
            
            # Initialize data dictionary for this email
            data = {
                'email_id': email['id'],
                'email_date': email.get('date'),
                'email_subject': email.get('subject', ''),
                'date': None,
                'time': None,
                'location': None,
                'total_kwh': None,
                'peak_kw': None,
                'duration': None,
                'cost_per_kwh': None,
                'total_cost': None
            }
            
            # Try to extract each piece of data using our patterns
            for field, field_patterns in patterns.items():
                for pattern in field_patterns:
                    match = re.search(pattern, email_body, re.IGNORECASE)
                    if match:
                        data[field] = match.group(1).strip()
                        break
            
            # Process the extracted data
            
            # Handle date and time
            if data['date']:
                # Try different date formats
                date_formats = [
                    '%m/%d/%Y', '%m/%d/%y', '%B %d, %Y', 
                    '%d-%m-%Y', '%d-%m-%y', '%Y-%m-%d'
                ]
                
                parsed_date = None
                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(data['date'], fmt)
                        break
                    except ValueError:
                        continue
                
                if parsed_date:
                    # Successfully parsed the date string (timezone-naive)
                    data['date'] = parsed_date
                elif email.get('date'):
                    # Use email date as fallback (might be timezone-aware)
                    data['date'] = email['date']
                else:
                    # Last resort fallback to today (timezone-naive)
                    data['date'] = datetime.now()
                
                # Normalize timezone handling
                # First, if the date is timezone-naive, make it timezone-aware (UTC)
                if hasattr(data['date'], 'tzinfo') and data['date'].tzinfo is None:
                    try:
                        import pytz
                        data['date'] = data['date'].replace(tzinfo=pytz.UTC)
                    except ImportError:
                        # If pytz is not available, use simpler approach
                        try:
                            from datetime import timezone
                            data['date'] = data['date'].replace(tzinfo=timezone.utc)
                        except:
                            pass  # If replace fails, keep the original
                
                # Then, strip timezone info to make all dates timezone-naive
                if hasattr(data['date'], 'tzinfo') and data['date'].tzinfo is not None:
                    try:
                        data['date'] = data['date'].replace(tzinfo=None)
                    except:
                        pass  # If replace fails, keep the original
                
            elif email.get('date'):
                # Use email date as fallback (might be timezone-aware)
                data['date'] = email['date']
                
                # Normalize timezone
                if hasattr(data['date'], 'tzinfo') and data['date'].tzinfo is not None:
                    try:
                        data['date'] = data['date'].replace(tzinfo=None)
                    except:
                        pass  # If replace fails, keep the original
            else:
                # Last resort fallback - timezone-naive datetime
                data['date'] = datetime.now()
            
            # Convert time to standard format if possible
            if data['time']:
                try:
                    # Try 12-hour format with AM/PM
                    if 'AM' in data['time'] or 'PM' in data['time']:
                        data['time'] = datetime.strptime(data['time'], '%I:%M %p').time()
                    # Try 24-hour format
                    else:
                        data['time'] = datetime.strptime(data['time'], '%H:%M:%S').time()
                except ValueError:
                    # Keep as string if conversion fails
                    pass
            
            # Convert numeric values
            for field in ['total_kwh', 'peak_kw', 'cost_per_kwh', 'total_cost']:
                if data[field]:
                    try:
                        data[field] = float(data[field])
                    except ValueError:
                        data[field] = None
            
            # Skip entries that don't have the minimum required data
            if (data['date'] is not None and 
                (data['total_kwh'] is not None or data['total_cost'] is not None)):
                charging_data.append(data)
                
        except Exception as e:
            # Log the error and continue with next email
            st.warning(f"Error parsing email: {str(e)}")
            continue
    
    return charging_data

def clean_charging_data(charging_data):
    """
    Clean and prepare the charging data for analysis
    
    Args:
        charging_data: List of charging data dictionaries
        
    Returns:
        Pandas DataFrame with cleaned data
    """
    # Convert to DataFrame
    df = pd.DataFrame(charging_data)
    
    # Ensure all numeric columns are correctly converted to float
    numeric_cols = ['total_kwh', 'peak_kw', 'cost_per_kwh', 'total_cost']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Ensure date column is datetime with consistent timezone handling
    if 'date' in df.columns:
        # Convert to datetime
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        # Fill missing dates with current date as fallback
        df['date'] = df['date'].fillna(pd.Timestamp.now())
        
        # Handle mixed timezone-aware and timezone-naive datetimes
        # First make timezone-naive datetimes timezone-aware (UTC)
        try:
            df['date'] = df['date'].apply(
                lambda x: x.tz_localize('UTC') if pd.notnull(x) and x.tzinfo is None else x
            )
            
            # Then make all datetimes timezone-naive for consistent comparison
            df['date'] = df['date'].apply(
                lambda x: x.tz_localize(None) if pd.notnull(x) and x.tzinfo is not None else x
            )
        except:
            # Fallback if timezone handling fails
            print("Warning: Unable to normalize timezones in date column")
    
    # Fill missing values
    if 'peak_kw' in df.columns and 'total_kwh' in df.columns and 'duration' in df.columns:
        # Try to infer peak_kw from total_kwh and duration where possible
        for idx, row in df.iterrows():
            if pd.isna(row['peak_kw']) and not pd.isna(row['total_kwh']) and not pd.isna(row['duration']):
                # Parse duration (assuming format like "1h 30m" or "45 minutes")
                duration_str = str(row['duration']).lower()
                hours = 0
                minutes = 0
                
                # Extract hours
                h_match = re.search(r'(\d+)\s*h', duration_str)
                if h_match:
                    hours = int(h_match.group(1))
                
                # Extract minutes
                m_match = re.search(r'(\d+)\s*m', duration_str)
                if m_match:
                    minutes = int(m_match.group(1))
                
                # If no pattern matched, try to convert directly to minutes
                if hours == 0 and minutes == 0:
                    minutes_match = re.search(r'(\d+)\s*min', duration_str)
                    if minutes_match:
                        minutes = int(minutes_match.group(1))
                
                # Calculate total hours
                total_hours = hours + (minutes / 60)
                
                # Calculate peak_kw if duration is non-zero
                if total_hours > 0:
                    df.at[idx, 'peak_kw'] = row['total_kwh'] / total_hours
    
    # Calculate missing cost values where possible
    if 'total_kwh' in df.columns and 'cost_per_kwh' in df.columns and 'total_cost' in df.columns:
        for idx, row in df.iterrows():
            if pd.isna(row['total_cost']) and not pd.isna(row['total_kwh']) and not pd.isna(row['cost_per_kwh']):
                df.at[idx, 'total_cost'] = row['total_kwh'] * row['cost_per_kwh']
            elif pd.isna(row['cost_per_kwh']) and not pd.isna(row['total_kwh']) and not pd.isna(row['total_cost']) and row['total_kwh'] > 0:
                df.at[idx, 'cost_per_kwh'] = row['total_cost'] / row['total_kwh']
    
    return df
