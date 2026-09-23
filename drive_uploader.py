import os
import datetime
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload

def get_drive_service():
    # Supports token or service account credentials configured in your environment
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    # Check for service account JSON in environment or default credentials
    if os.path.exists("credentials.json"):
        creds = service_account.Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    else:
        # Fallback to standard environment-based authentication if used previously
        from google.auth import default
        creds, _ = default(scopes=SCOPES)
        
    return build('drive', 'v3', credentials=creds)

def upload_pdf(file_path, file_title):
    service = get_drive_service()
    
    # Generate today's date folder name (e.g., 2026-09-23)
    today_date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Check if folder for today already exists in Google Drive
    query = f"name = '{today_date_str}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    folders = response.get('files', [])
    
    if folders:
        folder_id = folders[0]['id']
        print(f"Found existing Google Drive folder for today: {today_date_str}")
    else:
        # Create a new folder for today
        folder_metadata = {
            'name': today_date_str,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=folder_metadata, fields='id').execute()
        folder_id = folder.get('id')
        print(f"Created new Google Drive folder for today: {today_date_str}")
        
    # Upload PDF into today's date folder
    file_metadata = {
        'name': f"{file_title}.pdf",
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, mimetype='application/pdf', resumable=True)
    
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"SUCCESS: Uploaded '{file_title}.pdf' to Google Drive folder '{today_date_str}' (ID: {file.get('id')})")
    return file.get('id')
