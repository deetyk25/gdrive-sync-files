from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

class GDriveClient:
    def __init__(self, credentials_file='client_credentials.json', token_file='token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.creds = None
        self.service = None
        self.authenticate()

    def authenticate(self):
        flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
        self.creds = flow.run_local_server(port=0)
        self.service = build('drive', 'v3', credentials=self.creds)

    def list_files(self, page_size=100, page_token=None):
        results = self.service.files().list(
            pageSize=page_size,
            pageToken=page_token,
            fields="nextPageToken, files(id, name, mimeType, modifiedTime)"
        ).execute()
        return results.get('files', []), results.get('nextPageToken', None)