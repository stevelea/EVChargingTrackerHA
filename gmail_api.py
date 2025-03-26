import os
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import email
from email.utils import parsedate_to_datetime
import streamlit as st
import tempfile
import json

class GmailClient:
    """Class to handle Gmail API authentication and email retrieval"""
    
    def __init__(self, credentials_data=None):
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
        self.credentials_data = credentials_data
        self.creds = None
        self.service = None
        self.flow = None
    
    def get_authorization_url(self):
        """Get the authorization URL for the user to authenticate with Google"""
        # Create a temporary file to store credentials
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            json.dump(self.credentials_data, f)
            temp_creds_file = f.name
        
        # Create the flow using the credentials file
        self.flow = InstalledAppFlow.from_client_secrets_file(
            temp_creds_file,
            scopes=self.SCOPES,
            redirect_uri='urn:ietf:wg:oauth:2.0:oob'  # For console-based auth
        )
        
        # Generate the auth URL
        auth_url, _ = self.flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        # Clean up the temporary file
        os.unlink(temp_creds_file)
        
        return auth_url
    
    def authorize_with_code(self, code):
        """Exchange the authorization code for credentials"""
        if not self.flow:
            raise ValueError("Authorization flow not initialized. Call get_authorization_url first.")
        
        # Exchange the code for credentials
        self.flow.fetch_token(code=code)
        self.creds = self.flow.credentials
        
        # Initialize the Gmail API service
        self.service = build('gmail', 'v1', credentials=self.creds)
        
        return True
    
    def get_emails(self, query="", max_results=100):
        """Retrieve emails matching the query"""
        if not self.service:
            raise ValueError("Gmail service not initialized. Please authenticate first.")
        
        try:
            # Search for messages matching the query
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return []
            
            # Get full email content for each message ID
            emails = []
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me', 
                    id=message['id'],
                    format='full'
                ).execute()
                
                # Process email data
                email_data = self._process_email(msg)
                if email_data:
                    emails.append(email_data)
            
            return emails
            
        except Exception as error:
            st.error(f"An error occurred: {error}")
            return []
    
    def _process_email(self, msg):
        """Extract relevant information from an email message"""
        try:
            # Get headers
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
            from_email = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
            date_str = next((h['value'] for h in headers if h['name'].lower() == 'date'), None)
            
            # Parse date
            try:
                date = parsedate_to_datetime(date_str) if date_str else None
            except:
                date = None
            
            # Get email body
            body = ""
            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        body = base64.urlsafe_b64decode(part['body']['data'].encode('ASCII')).decode('utf-8')
                        break
            elif 'body' in msg['payload'] and 'data' in msg['payload']['body']:
                body = base64.urlsafe_b64decode(msg['payload']['body']['data'].encode('ASCII')).decode('utf-8')
            
            # Return the processed email data
            return {
                'id': msg['id'],
                'thread_id': msg['threadId'],
                'subject': subject,
                'from': from_email,
                'date': date,
                'body': body
            }
            
        except Exception as e:
            st.warning(f"Error processing email: {str(e)}")
            return None
