import os
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import email
from email.utils import parsedate_to_datetime
import streamlit as st
import tempfile
import json
import secrets
import urllib.parse

class GmailClient:
    """Class to handle Gmail API authentication and email retrieval"""
    
    # Get Google OAuth client credentials from environment variables
    @property
    def CLIENT_CONFIG(self):
        return {
            "web": {
                "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
                "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                # The redirect_uris will be passed dynamically when creating the Flow
                "redirect_uris": []
            }
        }
    
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
        self.creds = None
        self.service = None
        self.flow = None
        self.state = secrets.token_urlsafe(16)  # Generate a random state token
    
    def get_authorization_instructions(self):
        """
        Returns instructions for manual authorization without 
        using OAuth redirects or specific redirect URIs.
        """
        # Just return the OAuth consent screen URL - the user will need to manually copy the code
        return """
        1. Go to your Google Cloud Console: https://console.cloud.google.com/apis/credentials
        2. Find your OAuth 2.0 Client ID used for this app
        3. Go to the "OAuth consent screen" tab
        4. Click "PUBLISH APP" if not already published
        5. Go to https://accounts.google.com/o/oauth2/v2/auth?
           client_id={client_id}
           &redirect_uri=https://developers.google.com/oauthplayground
           &scope=https://www.googleapis.com/auth/gmail.readonly
           &access_type=offline
           &response_type=code
        
        Copy and paste this complete URL in your browser. After authenticating, you'll get 
        an authorization code that you can paste back in the app.
        """.format(
            client_id=self.CLIENT_CONFIG['web']['client_id']
        ).replace('\n           ', '')
    
    def authorize_with_code(self, code):
        """
        Authorize using the auth code provided by the user through the manual process
        """
        if not code:
            raise ValueError("No authorization code provided")
        
        try:
            # Create credentials manually using the authorization code
            client_id = self.CLIENT_CONFIG['web']['client_id']
            client_secret = self.CLIENT_CONFIG['web']['client_secret']
            
            # Create credentials object directly
            from google.oauth2.credentials import Credentials
            
            self.creds = Credentials(
                None,  # No token yet
                refresh_token=None,  # Will be filled with the response
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
                scopes=self.SCOPES,
            )
            
            # Manual token exchange
            import requests
            
            response = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "redirect_uri": "https://developers.google.com/oauthplayground",
                    "grant_type": "authorization_code",
                }
            )
            
            if response.status_code != 200:
                raise ValueError(f"Token exchange failed: {response.text}")
                
            token_data = response.json()
            
            # Update the credentials with the received tokens
            self.creds = Credentials(
                token_data.get('access_token'),
                refresh_token=token_data.get('refresh_token'),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
                scopes=self.SCOPES,
                expiry=None  # We don't parse the expiry for simplicity
            )
            
            # Initialize the Gmail API service
            self.service = build('gmail', 'v1', credentials=self.creds)
            
            return True
        except Exception as e:
            raise ValueError(f"Failed to authorize with code: {str(e)}")
    
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
