import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

PARENT_FOLDER_ID = "1NPYh-JHxjxF_kyu1ibkTO-AWhRCIJVmP" # Your Markaz Product Images folder ID

def get_drive_service():
    creds = Credentials(
        token=None,
        refresh_token=os.environ.get("GOOGLE_REFRESH_TOKEN"),
        client_id=os.environ.get("GOOGLE_CLIENT_ID"),
        client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token"
    )
    return build('drive', 'v3', credentials=creds)

def get_or_create_folder(service, folder_name, parent_id):
    query = f"name = '{folder_name}' and '{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    folders = response.get('files', [])
    
    if folders:
        return folders[0]['id']
    
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')

def upload_product_folder(date_str, product_title, image_paths, title, price, description):
    service = get_drive_service()
    
    # 1. Get or create Today's Date folder inside Markaz Product Images
    date_folder_id = get_or_create_folder(service, date_str, PARENT_FOLDER_ID)
    
    # 2. Clean product title for folder name (remove special characters)
    safe_folder_name = "".(c for c in product_title if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
    product_folder_id = get_or_create_folder(service, safe_folder_name, date_folder_id)
    
    # 3. Save and upload details.txt containing SEO info
    details_path = "/tmp/details.txt"
    with open(details_path, "w", encoding="utf-8") as f:
        f.write(f"Title: {title}\nPrice: PKR {price}\n\nDescription:\n{description}")
        
    media = MediaFileUpload(details_path, mimetype='text/plain')
    service.files().create(
        body={'name': 'details.txt', 'parents': [product_folder_id]},
        media_body=media,
        fields='id'
    ).execute()
    
    # 4. Upload clean product images (.jpg)
    uploaded_images = []
    for idx, img_path in enumerate(image_paths, start=1):
        img_name = f"img_{idx}.jpg"
        media = MediaFileUpload(img_path, mimetype='image/jpeg')
        file_res = service.files().create(
            body={'name': img_name, 'parents': [product_folder_id]},
            media_body=media,
            fields='id'
        ).execute()
        uploaded_images.append(file_res.get('id'))
        
    print(f"✅ Successfully uploaded folder '{safe_folder_name}' with {len(uploaded_images)} images and SEO details to Google Drive!")
    return product_folder_id
