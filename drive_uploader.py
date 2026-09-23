import os
import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

PARENT_FOLDER_ID = "1NPYh-JHxjxF_kyu1ibkTO-AWhRCIJVmP"

def get_drive_service():
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN")
    
    if not client_id or not client_secret or not refresh_token:
        raise ValueError("Google Drive OAuth environment variables (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN) are missing or incomplete.")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token"
    )
    return build('drive', 'v3', credentials=creds)

def upload_pdf(file_path, file_title):
    service = get_drive_service()
    today_date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    try:
        # Check if today's date folder exists inside your main Google Drive folder
        query = f"name = '{today_date_str}' and '{PARENT_FOLDER_ID}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        folders = response.get('files', [])
        
        if folders:
            folder_id = folders[0]['id']
            print(f"Found existing date folder '{today_date_str}' in your Drive.")
        else:
            folder_metadata = {
                'name': today_date_str,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [PARENT_FOLDER_ID]
            }
            folder = service.files().create(body=folder_metadata, fields='id').execute()
            folder_id = folder.get('id')
            print(f"Created new date folder '{today_date_str}' inside your main Drive folder.")
            
        file_metadata = {
            'name': f"{file_title}.pdf",
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path, mimetype='application/pdf', resumable=True)
        
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"SUCCESS: Uploaded '{file_title}.pdf' to Google Drive folder '{today_date_str}' (ID: {file.get('id')})")
        return file.get('id')
    except Exception as e:
        print(f"Error during Google Drive upload: {e}")
        raise e
