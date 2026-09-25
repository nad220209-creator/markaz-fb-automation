import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

PARENT_FOLDER_ID = "1NPYh-JHxjxF_kyu1ibkTO-AWhRCIJVmP"

def get_drive_service():
    return build('drive', 'v3', credentials=Credentials(
        token=None,
        refresh_token=os.environ.get("GOOGLE_REFRESH_TOKEN"),
        client_id=os.environ.get("GOOGLE_CLIENT_ID"),
        client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token"
    ))

def get_or_create_folder(service, folder_name, parent_id):
    query = f"name = '{folder_name}' and '{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    res = service.files().list(q=query, spaces='drive', fields='files(id)').execute()
    folders = res.get('files', [])
    if folders:
        return folders[0]['id']
    
    metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]}
    return service.files().create(body=metadata, fields='id').execute().get('id')

def upload_product_folder(date_str, product_id, product_title, image_paths, title, price, description):
    service = get_drive_service()
    
    # 1. Today's date folder
    date_folder_id = get_or_create_folder(service, date_str, PARENT_FOLDER_ID)
    
    # 2. Unique safe product subfolder (combines title + unique product ID to prevent duplicates)
    safe_title = "".join(c for c in product_title if c.isalnum() or c in (' ', '-', '_')).strip()[:35]
    unique_folder_name = f"{safe_title}_{str(product_id)[-6:]}"
    product_folder_id = get_or_create_folder(service, unique_folder_name, date_folder_id)
    
    # 3. Upload details.txt
    details_path = "/tmp/details.txt"
    with open(details_path, "w", encoding="utf-8") as f:
        f.write(f"Title: {title}\nPrice: PKR {price}\n\nDescription:\n{description}")
    service.files().create(
        body={'name': 'details.txt', 'parents': [product_folder_id]},
        media_body=MediaFileUpload(details_path, mimetype='text/plain'),
        fields='id'
    ).execute()
    
    # 4. Upload clean images
    for idx, img_path in enumerate(image_paths, start=1):
        service.files().create(
            body={'name': f"img_{idx}.jpg", 'parents': [product_folder_id]},
            media_body=MediaFileUpload(img_path, mimetype='image/jpeg'),
            fields='id'
        ).execute()
        
    print(f"✅ Uploaded unique folder '{unique_folder_name}' with {len(image_paths)} images and SEO details.")
