import os
import imaplib
import email
import base64
import streamlit as st
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta

class GmailClient:
    """Class to handle Gmail authentication and email retrieval using IMAP"""
    
    def __init__(self):
        self.imap = None
        self.email_address = None
        self.app_password = None
        
    def get_auth_instructions(self):
        """
        Returns instructions for setting up an App Password for Gmail
        """
        return """
        To access your Gmail account safely, you'll need to create an App Password:
        
        1. Go to your Google Account settings: https://myaccount.google.com/
        
        2. Select "Security" from the left menu
        
        3. Under "Signing in to Google," select "2-Step Verification" and verify your identity
        
        4. At the bottom of the page, select "App passwords"
        
        5. Click "Select app" and choose "Mail"
        
        6. Click "Select device" and choose "Other"
        
        7. Enter "EV Charging Analyzer" and click "Generate"
        
        8. Google will display a 16-character app password
        
        9. Copy this password and paste it in the app password field below
           (Don't worry, this password only gives access to your Gmail and nothing else)
        """
    
    def authenticate(self, email_address, app_password):
        """
        Authenticate with Gmail using IMAP with an app password
        """
        if not email_address or not app_password:
            raise ValueError("Email address and app password are required")
        
        try:
            # Connect to Gmail IMAP server
            self.imap = imaplib.IMAP4_SSL("imap.gmail.com")
            
            # Login with credentials
            self.imap.login(email_address, app_password)
            
            # Store credentials for later use
            self.email_address = email_address
            self.app_password = app_password
            
            return True
        except Exception as e:
            raise ValueError(f"Authentication failed: {str(e)}")
    
    def get_emails(self, query="", max_results=100):
        """
        Retrieve emails matching search criteria using IMAP
        
        This method now supports multiple search terms separated by "OR"
        """
        if not self.imap:
            raise ValueError("Not authenticated. Please authenticate first.")
        
        try:
            # Select the mailbox
            self.imap.select('INBOX')
            
            # Split the query by "OR" to handle multiple search terms
            search_terms = query.split(" OR ")
            all_email_ids = set()
            
            # For each search term, perform separate searches
            for term in search_terms:
                term = term.strip()
                if not term:
                    continue
                    
                # Escape any quotes in the search term
                term = term.replace('"', '\\"')
                
                # Try searching by subject first
                search_criteria = f'SUBJECT "{term}"' if term else 'ALL'
                
                # Search for messages
                status, message_ids = self.imap.search(None, search_criteria)
                
                # If status is OK and we have results, add them to our set
                if status == 'OK' and message_ids[0]:
                    message_id_list = message_ids[0].split()
                    all_email_ids.update(message_id_list)
                
                # Try searching by text/body next
                search_criteria = f'TEXT "{term}"'
                status, message_ids = self.imap.search(None, search_criteria)
                
                # If status is OK and we have results, add them to our set
                if status == 'OK' and message_ids[0]:
                    message_id_list = message_ids[0].split()
                    all_email_ids.update(message_id_list)
            
            # Convert set back to list and limit results
            message_id_list = list(all_email_ids)[:max_results]
            
            # If we have no results, try a generic search for "charging"
            if not message_id_list and not query:
                status, message_ids = self.imap.search(None, 'SUBJECT "charging"')
                if status == 'OK' and message_ids[0]:
                    message_id_list = message_ids[0].split()[:max_results]
            
            emails = []
            for msg_id in message_id_list:
                # Fetch the email
                status, msg_data = self.imap.fetch(msg_id, '(RFC822)')
                
                if status != 'OK':
                    st.warning(f"Error fetching email {msg_id}: {status}")
                    continue
                
                # Parse the email
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Process the email
                email_data = self._process_email(msg)
                if email_data:
                    emails.append(email_data)
            
            return emails
        
        except Exception as e:
            # Make sure to properly close the connection on error
            try:
                self.imap.close()
            except:
                pass
            
            # Create a new IMAP connection for future use
            try:
                self.imap = imaplib.IMAP4_SSL("imap.gmail.com")
                self.imap.login(self.email_address, self.app_password)
            except:
                self.imap = None
                
            st.error(f"Error fetching emails: {str(e)}")
            return []
    
    def _process_email(self, msg):
        """
        Extract relevant information from an email message
        """
        try:
            # Get headers
            subject = msg.get('Subject', 'No Subject')
            from_email = msg.get('From', 'Unknown Sender')
            date_str = msg.get('Date')
            
            # Parse date
            date = None
            if date_str:
                try:
                    date = parsedate_to_datetime(date_str)
                except:
                    date = None
            
            # Initialize variables for attachments and body
            attachments = []
            body = ""
            
            # Check if this is an EVCC email with CSV data
            is_evcc_csv_email = "EVCC Charging Data" in subject
            
            # Process message parts
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    
                    # Handle attachments
                    if "attachment" in content_disposition:
                        # Get attachment filename
                        filename = part.get_filename()
                        if filename:
                            # For CSV files, extract content
                            if filename.lower().endswith('.csv'):
                                attachment_data = part.get_payload(decode=True)
                                if attachment_data:
                                    # Store CSV data in attachments list
                                    attachments.append({
                                        'filename': filename,
                                        'type': 'csv',
                                        'data': attachment_data
                                    })
                        continue
                    
                    # Get text parts for body
                    if content_type == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or 'utf-8'
                            body = payload.decode(charset, errors='replace')
                        break
            else:
                # Non-multipart message - just get the body
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or 'utf-8'
                    body = payload.decode(charset, errors='replace')
            
            # Generate unique ID if actual ID is not available
            msg_id = msg.get('Message-ID', f"generated-{hash(subject + from_email + str(date))}")
            
            # Return the processed email data
            return {
                'id': msg_id,
                'thread_id': msg_id,  # Use same ID for simplicity
                'subject': subject,
                'from': from_email,
                'date': date,
                'body': body,
                'attachments': attachments,
                'is_evcc_csv_email': is_evcc_csv_email
            }
            
        except Exception as e:
            st.warning(f"Error processing email: {str(e)}")
            return None
    
    def close(self):
        """Close the IMAP connection and reset it for future use"""
        if self.imap:
            try:
                # Try to properly close and logout
                try:
                    self.imap.close()
                except:
                    pass
                    
                try:
                    self.imap.logout()
                except:
                    pass
                
                # Create a new connection for future use if we have credentials
                if self.email_address and self.app_password:
                    try:
                        self.imap = imaplib.IMAP4_SSL("imap.gmail.com")
                        self.imap.login(self.email_address, self.app_password)
                    except:
                        self.imap = None
                else:
                    self.imap = None
            except:
                # Last resort - set to None if all else fails
                self.imap = None
