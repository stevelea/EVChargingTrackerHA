import os
import re
import io
import tempfile
import streamlit as st
from datetime import datetime
from pypdf import PdfReader
import pytesseract
from pdf2image import convert_from_bytes
from data_parser import clean_charging_data  # Import existing cleaning function

def extract_text_from_pdf(pdf_file):
    """
    Extract text from a PDF file using both PDF extraction and OCR.
    
    Args:
        pdf_file: A file object containing the PDF data
        
    Returns:
        String containing the extracted text
    """
    try:
        # Store the uploaded PDF file to a temporary file
        pdf_bytes = pdf_file.read()
        
        # Try normal PDF text extraction first
        pdf_text = ""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pdf_text += page_text + "\n"
        except Exception as e:
            st.warning(f"Error extracting text directly from PDF: {str(e)}")
        
        # If we got reasonable text, return it
        if len(pdf_text.strip()) > 100:  # Assuming meaningful text is at least 100 chars
            return pdf_text
            
        # If direct extraction failed or returned too little text, try OCR
        try:
            # Convert PDF to images
            with tempfile.TemporaryDirectory() as temp_dir:
                images = convert_from_bytes(pdf_bytes)
                
                # Perform OCR on each image
                ocr_text = ""
                for i, image in enumerate(images):
                    text = pytesseract.image_to_string(image, lang='eng')
                    ocr_text += text + "\n"
                    
            # Return OCR text if it's more substantial
            if len(ocr_text.strip()) > len(pdf_text.strip()):
                return ocr_text
            else:
                return pdf_text
                
        except Exception as e:
            st.warning(f"Error performing OCR on PDF: {str(e)}")
            # If OCR failed but we have some text from direct extraction, return that
            if pdf_text.strip():
                return pdf_text
            else:
                raise ValueError("Could not extract text from PDF by any method")
    
    except Exception as e:
        st.error(f"Failed to process PDF file: {str(e)}")
        return ""

def parse_charging_pdf(pdf_file):
    """
    Extract EV charging data from PDF receipts.
    
    Args:
        pdf_file: A file object containing the PDF receipt
        
    Returns:
        Dictionary containing extracted charging data
    """
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_file)
    
    if not text:
        st.error("Could not extract text from PDF.")
        return None
    
    # Create data dictionary with default values
    data = {
        'date': None,
        'time': None,
        'location': None,
        'provider': None,
        'total_kwh': None,
        'peak_kw': None,
        'duration': None,
        'cost_per_kwh': None,
        'total_cost': None,
        'pdf_filename': pdf_file.name,
        'source': 'PDF Upload'
    }
    
    # Common patterns for different charging networks - similar to email parser
    patterns = {
        # Match date patterns in various formats
        'date': [
            r'Date:\s*(\d{1,2}/\d{1,2}/\d{2,4})',
            r'Date:\s*(\w+ \d{1,2}, \d{4})',
            r'Charging Date:\s*(\d{1,2}-\d{1,2}-\d{2,4})',
            r'Transaction Date:\s*(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}/\d{1,2}/\d{2,4})',
            r'(\d{2}-\d{2}-\d{4})'
        ],
        # Match time patterns
        'time': [
            r'Time:\s*(\d{1,2}:\d{2} [APM]{2})',
            r'Start Time:\s*(\d{1,2}:\d{2}:\d{2})',
            r'Charging Time:\s*(\d{1,2}:\d{2} [APM]{2})',
            r'(\d{1,2}:\d{2} [APM]{2})'
        ],
        # Match location patterns
        'location': [
            r'Location:\s*(.+?)(?:\n|\r|$)',
            r'Station:\s*(.+?)(?:\n|\r|$)',
            r'Charger Location:\s*(.+?)(?:\n|\r|$)',
            r'Address:\s*(.+?)(?:\n|\r|$)'
        ],
        # Match total kWh delivered
        'total_kwh': [
            r'Energy Delivered:\s*([\d.]+)\s*kWh',
            r'Total Energy:\s*([\d.]+)\s*kWh',
            r'kWh:\s*([\d.]+)',
            r'(\d+\.\d+)\s*kWh',
            r'Energy:\s*([\d.]+)\s*kWh'
        ],
        # Match peak kW rate
        'peak_kw': [
            r'Peak Power:\s*([\d.]+)\s*kW',
            r'Max Power:\s*([\d.]+)\s*kW',
            r'Peak kW:\s*([\d.]+)',
            r'Power:\s*([\d.]+)\s*kW'
        ],
        # Match charging duration
        'duration': [
            r'Duration:\s*(.+?)(?:\n|\r|$)',
            r'Charging Time:\s*(.+?)(?:\n|\r|$)',
            r'Time Connected:\s*(.+?)(?:\n|\r|$)',
            r'Session Length:\s*(.+?)(?:\n|\r|$)'
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
            r'USD\s*([\d.]+)',
            r'\$\s*([\d.]+)'
        ]
    }
    
    # Try to detect the provider from the text
    provider_patterns = {
        'AmpCharge': [r'AmpCharge', r'Ampol', r'AmpCharge', r'Amp[ -]?Charge'],
        'Evie Networks': [r'Evie', r'Evie Networks'],
        'Chargefox': [r'Chargefox'],
        'ChargePoint': [r'ChargePoint'],
        'Tesla': [r'Tesla', r'Supercharger', r'Tesla Supercharger'],
        'Electrify America': [r'Electrify America', r'Electrify'],
        'Jolt': [r'Jolt'],
        'EVUP': [r'EVUP', r'EV[ -]?UP'],
        'BPPulse': [r'BP Pulse', r'BPPulse', r'BP[ -]Pulse']
    }
    
    # Detect provider
    for provider, patterns_list in provider_patterns.items():
        for pattern in patterns_list:
            if re.search(pattern, text, re.IGNORECASE):
                data['provider'] = provider
                break
        if data['provider']:
            break
    
    # If we couldn't detect a provider, default to "Unknown"
    if not data['provider']:
        data['provider'] = "Unknown"
    
    # Extract other data using patterns
    for field, field_patterns in patterns.items():
        for pattern in field_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data[field] = match.group(1).strip()
                break
    
    # Process the extracted data
    
    # Handle date
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
            # Successfully parsed the date string
            data['date'] = parsed_date
        else:
            # Default to today if parsing fails
            data['date'] = datetime.now()
            
    else:
        # Use PDF filename to try to extract date if it's in a common format like YYYY-MM-DD
        filename = pdf_file.name
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_match:
            try:
                data['date'] = datetime.strptime(date_match.group(1), '%Y-%m-%d')
            except ValueError:
                data['date'] = datetime.now()
        else:
            # Last resort fallback
            data['date'] = datetime.now()
    
    # Convert time to standard format if possible
    if data['time'] and isinstance(data['time'], str):
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
    
    # If we have total_cost but not cost_per_kwh, try to calculate it
    if data['total_cost'] is not None and data['total_kwh'] is not None and data['cost_per_kwh'] is None:
        if data['total_kwh'] > 0:
            data['cost_per_kwh'] = data['total_cost'] / data['total_kwh']
    
    # Skip entries that don't have the minimum required data
    if data['date'] is not None and (data['total_kwh'] is not None or data['total_cost'] is not None):
        return data
    else:
        st.warning("Could not extract sufficient charging data from the PDF.")
        return None

def parse_multiple_pdfs(pdf_files):
    """
    Process multiple PDF files and extract charging data.
    
    Args:
        pdf_files: List of uploaded PDF files
        
    Returns:
        List of dictionaries containing extracted charging data
    """
    charging_data = []
    
    for pdf_file in pdf_files:
        try:
            st.info(f"Processing PDF: {pdf_file.name}")
            data = parse_charging_pdf(pdf_file)
            if data:
                charging_data.append(data)
                st.success(f"Successfully extracted data from {pdf_file.name}")
            # Reset file pointer for potential future use
            pdf_file.seek(0)
        except Exception as e:
            st.error(f"Error processing {pdf_file.name}: {str(e)}")
    
    return charging_data