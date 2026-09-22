import requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from config import CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN, TOKEN_URL, MAIN_DRIVE_FOLDER_ID

def get_drive_service():
    print("Requesting fresh OAuth access token...")
    token_res = requests.post(
        TOKEN_URL,
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": REFRESH_TOKEN,
            "grant_type": "refresh_token"
        },
        timeout=30
    )
    if token_res.status_code != 200:
        raise RuntimeError(f"Failed to refresh OAuth token: {token_res.text}")

    access_token = token_res.json().get("access_token")
    creds = Credentials(token=access_token)
    return build('drive', 'v3', credentials=creds)

def upload_pdf(pdf_path, pdf_filename):
    drive_service = get_drive_service()
    print(f"Uploading '{pdf_filename}.pdf' to Google Drive folder...")
    file_metadata = {
        'name': f"{pdf_filename}.pdf",
        'mimeType': 'application/pdf',
        'parents': [MAIN_DRIVE_FOLDER_ID]
    }
    media = MediaFileUpload(pdf_path, mimetype='application/pdf', resumable=True)
    uploaded = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()

    folder_link = uploaded.get('webViewLink')
    print(f"SUCCESS: Uploaded PDF to Drive -> {folder_link}")
    return folder_link
