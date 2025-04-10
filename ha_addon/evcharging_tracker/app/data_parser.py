import re
import csv
import io
from datetime import datetime
import pandas as pd
import streamlit as st

def parse_charging_emails(emails):
    """
    Extract EV charging data from email receipts.
    
    This function attempts to parse various formats of EV charging receipts 
    to extract key information like date, time, location, kWh, cost, etc.
    Also processes EVCC CSV files attached to emails.
    
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
        # Match location patterns - expanded to capture more formats
        'location': [
            r'Location:\s*(.+?)(?:\n|\r|$)',
            r'Station:\s*(.+?)(?:\n|\r|$)',
            r'Charger Location:\s*(.+?)(?:\n|\r|$)',
            r'Charging Station:\s*(.+?)(?:\n|\r|$)',
            r'Address:\s*(.+?)(?:\n|\r|$)',
            r'Station Address:\s*(.+?)(?:\n|\r|$)',
            r'at\s+(.+?)\s+charging station',
            r'Thank you for charging at\s+(.+?)[\.\n\r]',
            r'You charged at\s+(.+?)[,\.\n\r]',
            # Specific patterns for Evie Networks format
            r'Your charging session receipt\s*\n+.*\n+\s*(.+?)\s*\n',
            r'Warners Bay Grove\s*[\n\r]+\s*(.+?)[,\.\n\r]',
            r'(\d+\s+[A-Za-z]+\s+(?:Rd|Road|St|Street|Ave|Avenue|Blvd|Boulevard|Dr|Drive)[^\n\r,]*)',
            r'Your charging session at\s+(.+?)[,\.\n\r]',
            # Match for address format with street number
            r'\n(\d+\s+[^\n,]+(?:Road|Rd|Street|St|Avenue|Ave|Drive|Dr|Hwy|Highway|Lane|Ln)[^\n,]*)',
            # Match for location name at top of receipt
            r'^\s*([^\n]+?)\s*\n+(?:Your charging session|Charging session)'
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
        # Match cost per kWh with more flexible patterns
        'cost_per_kwh': [
            r'Rate:\s*\$?([\d.]+)/kWh',
            r'Price per kWh:\s*\$?([\d.]+)',
            r'\$?([\d.]+)\s*per kWh',
            r'Rate:\s*\$?([\d.]+)\s*kWh',
            r'@\s*\$?([\d.]+)/kWh',
            r'Cost/kWh:\s*\$?([\d.]+)',
            r'Price/kWh:\s*\$?([\d.]+)',
            r'Unit Price:\s*\$?([\d.]+)',
            r'@\s*\$?([\d.]+)',
            r'at\s*\$?([\d.]+)/kWh'
        ],
        # Match total cost with more flexible patterns
        'total_cost': [
            r'Total:\s*\$?([\d.]+)',
            r'Amount:\s*\$?([\d.]+)',
            r'Total Cost:\s*\$?([\d.]+)',
            r'Total Amount:\s*\$?([\d.]+)',
            r'Cost:\s*\$?([\d.]+)',
            r'Payment Amount:\s*\$?([\d.]+)',
            r'Charged:\s*\$?([\d.]+)',
            r'Bill Amount:\s*\$?([\d.]+)',
            r'Total Charge:\s*\$?([\d.]+)',
            r'Fee:\s*\$?([\d.]+)',
            r'Amount Paid:\s*\$?([\d.]+)',
            r'Total Payment:\s*\$?([\d.]+)',
            r'Paid:\s*\$?([\d.]+)',
            r'USD\s*([\d.]+)'
        ]
    }
    
    # Specific patterns for Ampol AmpCharge receipts
    ampol_patterns = {
        'location': [
            r'Location:\s*(.+?)(?:\n|\r|$)',
            r'Charging station:\s*(.+?)(?:\n|\r|$)',
            # Pattern for AmpCharge format with location and address on separate lines
            r'AmpCharge Pty Ltd\s*\n+\s*([^,\n]+(?:Highway|Road|Street|Avenue|Lane|Drive)(?:[^,\n]+)?,\s*[^,\n]+\s*\d{4})',
            # Pattern for location with street number, name, and suburb with postcode
            r'(?:Pacific|Princes|Hume|Western|Eastern|Northern|Southern)\s+Highway\s+(\d+-\d+|\d+),\s*([^,\n]+)\s+(\d{4})',
            # Address formats on separate lines
            r'(?:AmpCharge|Ampol)[^\n]*\n+([^\n]+(?:Highway|Road|Street|Avenue|Lane|Drive)[^\n]*(?:,|\n)[^\n]*\d{4})',
        ],
        'total_kwh': [
            r'Energy delivered:\s*([\d.]+)\s*kWh',
            r'Energy consumed:\s*([\d.]+)\s*kWh',
        ],
        'total_cost': [
            r'Total amount:\s*\$?([\d.]+)',
            r'Amount:\s*\$?([\d.]+)',
        ]
    }
    
    for email in emails:
        try:
            # Check for EVCC Charging Data emails with CSV attachments
            email_subject = email.get('subject', '')
            if "EVCC Charging Data" in email_subject and 'attachments' in email and email['attachments']:
                for attachment in email['attachments']:
                    if attachment['type'] == 'csv':
                        try:
                            # Create file-like object from attachment data
                            import io
                            csv_file = io.BytesIO(attachment['data'])
                            
                            # Parse EVCC CSV file
                            evcc_data = parse_evcc_csv(csv_file)
                            
                            # Add all EVCC data to our result with source marker
                            if evcc_data:
                                for item in evcc_data:
                                    item['source'] = 'EVCC CSV'
                                charging_data.extend(evcc_data)
                                st.success(f"Extracted {len(evcc_data)} charging sessions from EVCC CSV attachment")
                        except Exception as e:
                            st.error(f"Error processing EVCC CSV attachment: {str(e)}")
                            import traceback
                            st.error(traceback.format_exc())
                # Continue to next email after processing EVCC CSV
                continue
                
            # Skip emails without bodies
            if not email.get('body'):
                continue
                
            email_body = email['body']
            email_subject = email.get('subject', '')
            
            # Initialize data dictionary for this email
            data = {
                'email_id': email['id'],
                'email_date': email.get('date'),
                'email_subject': email_subject,
                'date': None,
                'time': None,
                'location': None,
                'provider': None,  # New field for charging provider
                'total_kwh': None,
                'peak_kw': None,
                'duration': None,
                'cost_per_kwh': None,
                'total_cost': None
            }
            
            # Check if this is an Ampol AmpCharge receipt
            is_ampol = 'ampol' in email_subject.lower() or 'ampcharge' in email_subject.lower()
            is_evie = 'evie' in email_subject.lower() or 'evie' in email_body.lower()
            
            # Detect and set the provider based on email subject and body
            if is_ampol:
                data['provider'] = 'AmpCharge'
                # For AmpCharge, try to extract more location details if empty
                if not data['location']:
                    ampol_locations = [
                        "AmpCharge Alexandria", "AmpCharge Belconnen", "AmpCharge Melbourne CBD",
                        "AmpCharge Brisbane", "AmpCharge Sydney Airport", "AmpCharge Perth",
                        "AmpCharge Adelaide", "AmpCharge Canberra"
                    ]
                    # Check if any of these locations appear in the email
                    for loc in ampol_locations:
                        if loc.lower() in email_body.lower() or loc.lower() in email_subject.lower():
                            data['location'] = loc
                            break
                    
            elif is_evie:
                data['provider'] = 'Evie Networks'
                
                # For Evie Networks, check for the specific location format in their receipts first
                if not data['location']:
                    # Try to extract location from Evie Networks receipt format
                    # Pattern for location name followed by address on next line(s)
                    evie_pattern = r'(?:Warners Bay Grove|[A-Za-z\s]+(?:Hub|Station|Grove|Centre))\s*\n+\s*([^\n]+?(?:Rd|Road|St|Street|Ave|Avenue|Dr|Drive|Hwy|Highway)[^\n]*(?:,|\n)[^\n]*)'
                    
                    match = re.search(evie_pattern, email_body, re.IGNORECASE)
                    if match:
                        data['location'] = match.group(1).strip()
                    
                    # If still no location, look for any address line followed by suburb and postcode
                    if not data['location']:
                        address_pattern = r'(\d+\s+[A-Za-z\s]+(?:Rd|Road|St|Street|Ave|Avenue|Dr|Drive|Hwy|Highway)\s+[A-Za-z\s]+,\s*[A-Z]{2,3}\s+\d{4})'
                        match = re.search(address_pattern, email_body, re.IGNORECASE)
                        if match:
                            data['location'] = match.group(1).strip()
                
                # Fall back to generic locations if specific pattern fails
                if not data['location']:
                    evie_locations = [
                        "Evie Networks Brisbane", "Evie Networks Sydney", "Evie Networks Melbourne",
                        "Evie Networks Perth", "Evie Networks Adelaide", "Evie Networks Canberra",
                        "Evie Networks Hobart", "Evie Networks Darwin"
                    ]
                    # Check if any of these locations appear in the email
                    for loc in evie_locations:
                        if loc.lower() in email_body.lower() or loc.lower() in email_subject.lower():
                            data['location'] = loc
                            break
                    
            elif 'chargefox' in email_subject.lower() or 'chargefox' in email_body.lower():
                data['provider'] = 'Chargefox'
                # For Chargefox, try to extract more location details if empty
                if not data['location']:
                    chargefox_locations = [
                        "Chargefox Sydney CBD", "Chargefox Melbourne CBD", "Chargefox Brisbane CBD",
                        "Chargefox Perth CBD", "Chargefox Adelaide CBD", "Chargefox Canberra CBD",
                        "Chargefox Hobart", "Chargefox Darwin"
                    ]
                    # Check if any of these locations appear in the email
                    for loc in chargefox_locations:
                        if loc.lower() in email_body.lower() or loc.lower() in email_subject.lower():
                            data['location'] = loc
                            break
                    
            elif 'chargepoint' in email_subject.lower() or 'chargepoint' in email_body.lower():
                data['provider'] = 'ChargePoint'
            elif 'tesla' in email_subject.lower() or 'tesla' in email_body.lower():
                data['provider'] = 'Tesla'
                # For Tesla, try to extract more location details if empty
                if not data['location']:
                    tesla_locations = [
                        "Tesla Supercharger Sydney", "Tesla Supercharger Melbourne", 
                        "Tesla Supercharger Brisbane", "Tesla Supercharger Perth",
                        "Tesla Supercharger Adelaide", "Tesla Supercharger Canberra",
                        "Tesla Supercharger Hobart", "Tesla Supercharger Darwin",
                        "Tesla Supercharger Gold Coast", "Tesla Supercharger Newcastle"
                    ]
                    # Check if any of these locations appear in the email
                    for loc in tesla_locations:
                        if loc.lower() in email_body.lower() or loc.lower() in email_subject.lower():
                            data['location'] = loc
                            break
                    
            elif 'electrify' in email_subject.lower() or 'electrify' in email_body.lower():
                data['provider'] = 'Electrify America'
            elif 'jolt' in email_subject.lower() or 'jolt' in email_body.lower():
                data['provider'] = 'Jolt'
            elif 'evup' in email_subject.lower() or 'evup' in email_body.lower():
                data['provider'] = 'EVUP'
            elif 'bp pulse' in email_subject.lower() or 'bp pulse' in email_body.lower():
                data['provider'] = 'BPPulse'
            else:
                # Try to extract from location or station info if available
                # Default to "Unknown" if we can't identify the provider
                data['provider'] = 'Unknown'
            
            # Use Ampol specific patterns if this is an Ampol email
            if is_ampol:
                # Try to extract each piece of data using Ampol-specific patterns
                for field, field_patterns in ampol_patterns.items():
                    for pattern in field_patterns:
                        match = re.search(pattern, email_body, re.IGNORECASE)
                        if match:
                            # For special highway pattern with multiple groups
                            if field == 'location' and 'Highway' in pattern and match.lastindex and match.lastindex > 1:
                                # Combine highway, number, suburb and postcode into a proper address
                                highway = match.group(1) if match.group(1) else "Pacific Highway"
                                number = match.group(2) if match.group(2) else ""
                                suburb = match.group(3) if match.group(3) and match.lastindex >= 3 else ""
                                postcode = match.group(4) if match.lastindex >= 4 and match.group(4) else ""
                                
                                # Build a clean address string
                                address_parts = []
                                if highway: address_parts.append(highway)
                                if number: address_parts.append(number)
                                if suburb: address_parts.append(suburb)
                                if postcode: address_parts.append(postcode)
                                
                                data[field] = "AmpCharge " + ", ".join(address_parts).strip()
                            else:
                                # Standard extraction for other fields
                                data[field] = match.group(1).strip()
                            break
                
                # Use regular patterns for fields not in ampol_patterns
                for field, field_patterns in patterns.items():
                    if field not in ampol_patterns or data[field] is None:
                        for pattern in field_patterns:
                            match = re.search(pattern, email_body, re.IGNORECASE)
                            if match:
                                data[field] = match.group(1).strip()
                                break
            else:
                # For non-Ampol emails, use the regular patterns
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
                
                # Normalize timezone handling and extract time if needed
                try:
                    # If it's already a datetime, get date and time parts separately
                    year = data['date'].year
                    month = data['date'].month
                    day = data['date'].day
                    
                    # If we don't have a time component yet, extract it from the datetime
                    if data['time'] is None and hasattr(data['date'], 'hour') and hasattr(data['date'], 'minute'):
                        # Extract time part from the datetime to the time field
                        data['time'] = data['date'].time()
                    
                    # Set date to just the date part (no time)
                    data['date'] = datetime(year, month, day)
                except:
                    # If extraction fails for any reason, keep the original
                    pass
                
            elif email.get('date'):
                # Use email date as fallback (might be timezone-aware)
                data['date'] = email['date']
                
                # If we don't have a time component yet, extract it from the email date
                if data['time'] is None and hasattr(data['date'], 'hour') and hasattr(data['date'], 'minute'):
                    # Extract time part from the datetime to the time field
                    data['time'] = data['date'].time()
                
                # Normalize timezone
                if hasattr(data['date'], 'tzinfo') and data['date'].tzinfo is not None:
                    try:
                        data['date'] = data['date'].replace(tzinfo=None)
                    except:
                        pass  # If replace fails, keep the original
                        
                # Strip time component from date (keep only the date part)
                try:
                    year = data['date'].year
                    month = data['date'].month
                    day = data['date'].day
                    data['date'] = datetime(year, month, day)
                except:
                    pass  # If extraction fails for any reason, keep the original
            else:
                # Last resort fallback - timezone-naive datetime
                now = datetime.now()
                # Extract time part to time field if it's not already set
                if data['time'] is None:
                    data['time'] = now.time()
                # Use only date part for date field
                data['date'] = datetime(now.year, now.month, now.day)
            
            # Convert time to standard format if possible
            if data['time']:
                # Check if time is already a time object
                if hasattr(data['time'], 'hour') and hasattr(data['time'], 'minute'):
                    # Already a time object, no conversion needed
                    pass
                elif isinstance(data['time'], str):
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
            
            # If we still don't have a location but have a provider, create a generic location
            if not data['location'] and data['provider'] != 'Unknown':
                # Create a generic location based on provider name
                locations_by_city = ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Canberra"]
                # If we find a city name in the email, use it
                found_city = False
                for city in locations_by_city:
                    if city.lower() in email_body.lower() or city.lower() in email_subject.lower():
                        data['location'] = f"{data['provider']} {city}"
                        found_city = True
                        break
                
                # If no city found, default to a generic location
                if not found_city:
                    data['location'] = f"{data['provider']} Charging Station"
            
            # Skip entries that don't have the minimum required data
            if (data['date'] is not None and 
                (data['total_kwh'] is not None or data['total_cost'] is not None)):
                charging_data.append(data)
                
        except Exception as e:
            # Log the error and continue with next email
            st.warning(f"Error parsing email: {str(e)}")
            continue
    
    return charging_data

def parse_evcc_csv(csv_file, default_cost_per_kwh=0.01):
    """
    Parse charging data from EVCC CSV export file.
    
    Args:
        csv_file: File object containing EVCC CSV data
        default_cost_per_kwh: Default cost per kWh to use for EVCC sessions (default: 0.01)
        
    Returns:
        List of dictionaries containing extracted charging data
    """
    charging_data = []
    
    try:
        # Read CSV content
        content = csv_file.read()
        
        # Handle byte string if needed
        if isinstance(content, bytes):
            content = content.decode('utf-8')
            
        # Create CSV reader
        csv_data = csv.reader(io.StringIO(content), delimiter=',')
        headers = next(csv_data, None)  # Get headers
        
        # Remove BOM if present
        if headers and len(headers) > 0 and headers[0].startswith('\ufeff'):
            headers[0] = headers[0].replace('\ufeff', '')
        
        # Check if this is a valid EVCC CSV file by looking for common fields
        required_fields = ['Created', 'Energy (kWh)']  # Updated required fields for the sample
        
        # Make sure headers is not None before checking
        if headers is None:
            st.error("CSV file appears to be empty or invalid.")
            return []
            
        has_required_fields = all(field in headers for field in required_fields)
        
        if not has_required_fields:
            st.error(f"Invalid EVCC CSV format. Required fields: {', '.join(required_fields)}")
            st.info(f"Found headers: {', '.join(headers)}")
            return []
            
        # Map CSV columns to our data structure
        column_mapping = {
            'Created': 'date',
            'Finished': 'end_date',
            'Charging point': 'location',
            'Vehicle': 'vehicle',
            'Mileage (km)': 'odometer', 
            'Energy (kWh)': 'total_kwh',
            'Duration': 'duration',
            'Price': 'total_cost',
            'Price/kWh': 'cost_per_kwh'
        }
        
        # Get column indices
        column_indices = {}
        for csv_col, our_col in column_mapping.items():
            # headers is already checked for None above
            if headers and csv_col in headers:
                column_indices[our_col] = headers.index(csv_col)
        
        # Process each row
        for row in csv_data:
            if not row or len(row) < len(headers):  # Skip empty or incomplete rows
                continue
                
            # Create data entry with default values
            data = {
                'date': None,
                'time': None,
                'location': 'Home Charging Station',  # Generic home location name to avoid conflicts
                'provider': 'EVCC',  # Set provider to EVCC
                'source': 'EVCC CSV',  # Mark the source for identification in replace operations
                'total_kwh': None,
                'peak_kw': None,
                'id': None,  # Ensure we have an ID field
                'duration': None,
                'cost_per_kwh': default_cost_per_kwh,  # Use default cost
                'total_cost': None,
                'vehicle': None,
                'odometer': None
            }
            
            # Map data from CSV columns
            for our_col, idx in column_indices.items():
                if idx < len(row) and row[idx]:
                    data[our_col] = row[idx]
            
            # Process start date/time
            if 'date' in column_indices and row[column_indices['date']]:
                try:
                    # Try to parse format (YYYY-MM-DD HH:MM:SS)
                    timestamp = pd.to_datetime(row[column_indices['date']])
                    data['date'] = timestamp.date()
                    data['time'] = timestamp.time()
                except Exception as e:
                    # Fallback to current time
                    now = datetime.now()
                    data['date'] = now.date()
                    data['time'] = now.time()
            
            # Use location data if available
            if 'location' in column_indices and row[column_indices['location']]:
                location = row[column_indices['location']].strip()
                if location:  # Only override default if non-empty
                    data['location'] = location
            
            # Process numeric values - total_kwh
            if 'total_kwh' in column_indices and row[column_indices['total_kwh']]:
                try:
                    data['total_kwh'] = float(row[column_indices['total_kwh']])
                except ValueError:
                    data['total_kwh'] = None
            
            # Process cost per kWh if available
            if 'cost_per_kwh' in column_indices and row[column_indices['cost_per_kwh']]:
                try:
                    cost_str = row[column_indices['cost_per_kwh']].replace('$', '').strip()
                    if cost_str:
                        data['cost_per_kwh'] = float(cost_str)
                except ValueError:
                    # Keep default
                    pass
            
            # Process total cost if available
            if 'total_cost' in column_indices and row[column_indices['total_cost']]:
                try:
                    cost_str = row[column_indices['total_cost']].replace('$', '').strip()
                    if cost_str:
                        data['total_cost'] = float(cost_str)
                except ValueError:
                    data['total_cost'] = None
            
            # Calculate total cost if not provided but kWh is available
            if data['total_cost'] is None and data['total_kwh'] is not None and data['cost_per_kwh'] is not None:
                data['total_cost'] = data['total_kwh'] * data['cost_per_kwh']
            
            # Skip entries that don't have minimum required data
            if data['date'] is not None and data['total_kwh'] is not None:
                charging_data.append(data)
        
    except Exception as e:
        st.error(f"Error parsing EVCC CSV: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return []
    
    st.success(f"Successfully parsed {len(charging_data)} charging sessions from EVCC CSV")
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
    
    # Enhanced missing cost value calculation with more robust logic
    if 'total_kwh' in df.columns and 'cost_per_kwh' in df.columns and 'total_cost' in df.columns:
        # Calculate missing total_cost values
        for idx, row in df.iterrows():
            # Determine if this is an Ampol receipt
            is_ampol = False
            if 'email_subject' in df.columns:
                email_subject = str(row.get('email_subject', '')).lower()
                is_ampol = 'ampol' in email_subject or 'ampcharge' in email_subject
            
            # For Ampol receipts, always calculate cost_per_kwh from total_cost and total_kwh
            if is_ampol and not pd.isna(row['total_cost']) and not pd.isna(row['total_kwh']) and row['total_kwh'] > 0:
                df.at[idx, 'cost_per_kwh'] = row['total_cost'] / row['total_kwh']
                st.info(f"Calculated cost per kWh for Ampol AmpCharge: ${df.at[idx, 'cost_per_kwh']:.2f}")
            
            # For other receipts or if we're missing values, use standard calculations
            elif pd.isna(row['total_cost']) and not pd.isna(row['total_kwh']) and not pd.isna(row['cost_per_kwh']):
                # If we have energy and rate but no cost, calculate it
                df.at[idx, 'total_cost'] = row['total_kwh'] * row['cost_per_kwh']
            
            elif pd.isna(row['cost_per_kwh']) and not pd.isna(row['total_kwh']) and not pd.isna(row['total_cost']) and row['total_kwh'] > 0:
                # If we have total cost and energy but no rate, calculate it
                df.at[idx, 'cost_per_kwh'] = row['total_cost'] / row['total_kwh']

        # Some standard defaults if values are still missing
        # Use the median cost per kWh as a fallback if available and total_kwh is known
        median_cost_per_kwh = df['cost_per_kwh'].median()
        if not pd.isna(median_cost_per_kwh):
            for idx, row in df.iterrows():
                if pd.isna(row['total_cost']) and not pd.isna(row['total_kwh']):
                    df.at[idx, 'total_cost'] = row['total_kwh'] * median_cost_per_kwh
                    # Also set the cost_per_kwh if it's missing
                    if pd.isna(row['cost_per_kwh']):
                        df.at[idx, 'cost_per_kwh'] = median_cost_per_kwh
        
        # If we have total_cost but not total_kwh and we know the median cost/kWh, we can infer total_kwh
        median_total_kwh = df['total_kwh'].median()
        if not pd.isna(median_cost_per_kwh) and not pd.isna(median_total_kwh):
            for idx, row in df.iterrows():
                if pd.isna(row['total_kwh']) and not pd.isna(row['total_cost']):
                    df.at[idx, 'total_kwh'] = row['total_cost'] / median_cost_per_kwh
                    # Also set the cost_per_kwh if it's missing
                    if pd.isna(row['cost_per_kwh']):
                        df.at[idx, 'cost_per_kwh'] = median_cost_per_kwh
                        
    # Replace any remaining NaN values in numeric columns with 0
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    
    return df
