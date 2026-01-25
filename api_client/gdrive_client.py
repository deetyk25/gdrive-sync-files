from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time

# Providing read-only access to metadata
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

class GDriveClient:
    # Handles authentication and error handling

    def __init__(self, service=None, credentials_file='client_credentials.json', token_file='token.json'):
        # OAuth client credentials + tokens
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.creds = None
        # Drive API for testing, only authenticated if the service isn't injected
        self.service = service

        if self.service is None:
            self.authenticate()

    # OAuth 2.0 authentication and initializes Google Drive API client 
    def authenticate(self):
        flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
        self.creds = flow.run_local_server(port=0)
        # Builds v3 API client
        self.service = build('drive', 'v3', credentials=self.creds)

    def list_files(self, page_size=100, page_token=None):
        # Lists files on next token
        try:
            results = self.service.files().list(
                pageSize=page_size,
                pageToken=page_token,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime)"
            ).execute()
            return results.get('files', []), results.get('nextPageToken', None)
        except HttpError as e:
            # Handles retryable errors (rate limit or server failures)
            if e.resp.status in (429, 500, 503):
                time.sleep(2)
                raise RuntimeError("Retryable API error") from e
            # Handles non-retryable errors with raised exception
            print("Nonretryable error!")
            raise