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
        """
        if not self.imap:
            raise ValueError("Not authenticated. Please authenticate first.")
        
        try:
            # Select the mailbox
            self.imap.select('INBOX')
            
            # Prepare search criteria with proper escaping
            query = query.replace('"', '\\"')  # Escape double quotes
            
            # Try searching by subject first
            search_criteria = f'SUBJECT "{query}"' if query else 'ALL'
            
            # Search for messages
            status, message_ids = self.imap.search(None, search_criteria)
            
            # If no results, try a broader search in the body
            if status == 'OK' and not message_ids[0]:
                search_criteria = f'TEXT "{query}"'
                status, message_ids = self.imap.search(None, search_criteria)
            
            if status != 'OK':
                raise ValueError(f"Error searching for emails: {status}")
            
            # Convert space-separated string of message IDs to a list
            message_id_list = message_ids[0].split()
            
            # Limit the number of messages to retrieve
            message_id_list = message_id_list[:max_results]
            
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
            
            # Get email body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    
                    # Skip attachments
                    if "attachment" in content_disposition:
                        continue
                    
                    # Get text parts
                    if content_type == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or 'utf-8'
                            body = payload.decode(charset, errors='replace')
                        break
            else:
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
                'body': body
            }
            
        except Exception as e:
            st.warning(f"Error processing email: {str(e)}")
            return None
    
    def close(self):
        """Close the IMAP connection"""
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
            except:
                pass  # Ignore errors on close
