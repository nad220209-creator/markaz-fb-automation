import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

PARENT_FOLDER_ID = "1NPYh-JHxjxF_kyu1ibkTO-AWhRCIJVmP"

def get_drive_service():
    creds_json = os.environ.get("GOOGLE_DRIVE_CREDENTIALS")
    if creds_json:
        creds_dict = json.loads(creds_json)
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=['https://www.googleapis.com/auth/drive']
        )
        return build('drive', 'v3', credentials=creds)
    return None

def create_folder(service, name, parent_id):
    query = f"name='{name}' and parents='{parent_id}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    if files:
        return files[0]['id']
    
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')

def upload_product_to_drive(product_data, local_images, details_content, date_str):
    service = get_drive_service()
    if not service:
        print("Google Drive service unavailable.")
        return

    date_folder_id = create_folder(service, date_str, PARENT_FOLDER_ID)
    shoes_folder_id = create_folder(service, "Shoes", date_folder_id)
    
    safe_title = "".join(c for c in product_data['title'][:30] if c.isalnum() or c in (' ', '_', '-')).strip()
    product_folder_id = create_folder(service, safe_title, shoes_folder_id)

    details_path = "temp_details.txt"
    with open(details_path, "w", encoding="utf-8") as f:
        f.write(details_content)
    
    media = MediaFileUpload(details_path, mimetype='text/plain')
    service.files().create(
        body={'name': 'details.txt', 'parents': [product_folder_id]},
        media_body=media,
        fields='id'
    ).execute()
    os.remove(details_path)

    for img_path in local_images:
        if os.path.exists(img_path):
            media_img = MediaFileUpload(img_path, mimetype='image/jpeg')
            service.files().create(
                body={'name': os.path.basename(img_path), 'parents': [product_folder_id]},
                media_body=media_img,
                fields='id'
            ).execute()
