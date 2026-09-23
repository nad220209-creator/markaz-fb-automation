import os
import datetime
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload

# Your specific Google Drive shared folder ID
PARENT_FOLDER_ID = "1NPYh-JHxjxF_kyu1ibkTO-AWhRCIJVmP"

def get_drive_service():
    SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
    if os.path.exists("credentials.json"):
        creds = service_account.Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    else:
        from google.auth import default
        creds, _ = default(scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def upload_pdf(file_path, file_title):
    service = get_drive_service()
    today_date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Check if today's date folder exists inside your main Google Drive folder
    query = f"name = '{today_date_str}' and '{PARENT_FOLDER_ID}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    folders = response.get('files', [])
    
    if folders:
        folder_id = folders[0]['id']
        print(f"Found existing date folder '{today_date_str}' in your Drive.")
    else:
        # Create today's date folder inside your main Google Drive folder
        folder_metadata = {
            'name': today_date_str,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [PARENT_FOLDER_ID]
        }
        folder = service.files().create(body=folder_metadata, fields='id').execute()
        folder_id = folder.get('id')
        print(f"Created new date folder '{today_date_str}' inside your main Drive folder.")
        
    # Upload PDF into today's date folder
    file_metadata = {
        'name': f"{file_title}.pdf",
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, mimetype='application/pdf', resumable=True)
    
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"SUCCESS: Uploaded '{file_title}.pdf' to Google Drive folder '{today_date_str}' (ID: {file.get('id')})")
    return file.get('id')
