import os
import pickle
import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Scopes nécessaires pour accéder à Google Photos
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.appendonly',
          'https://www.googleapis.com/auth/photoslibrary.readonly.appcreateddata']

_CREDS_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = next(
    (os.path.join(_CREDS_DIR, f) for f in os.listdir(_CREDS_DIR) if f.startswith('client_secret') and f.endswith('.json')),
    os.path.join(_CREDS_DIR, 'credentials.json')
)
TOKEN_FILE = os.path.join(_CREDS_DIR, 'token.pickle')
ALBUM_NAME = 'Photobooth'


def authenticate():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    return creds


def get_or_create_album(service, album_title):
    albums = service.albums().list(
        pageSize=50,
        fields="albums(id,title)"
    ).execute().get('albums', [])

    for album in albums:
        if album['title'] == album_title:
            return album['id']

    new_album = service.albums().create(body={
        'album': {'title': album_title}
    }).execute()
    return new_album['id']


def upload_photo(photo_path, album_name=None):
    creds = authenticate()
    service = build('photoslibrary', 'v1', credentials=creds)
    album_id = get_or_create_album(service, album_name or ALBUM_NAME)

    # Lire le contenu de la photo
    with open(photo_path, 'rb') as photo_file:
        photo_bytes = photo_file.read()

    # Étape 1 : upload vers Google (upload token)
    upload_token = requests.post(
        url='https://photoslibrary.googleapis.com/v1/uploads',
        data=photo_bytes,
        headers={
            'Authorization': f'Bearer {creds.token}',
            'Content-type': 'application/octet-stream',
            'X-Goog-Upload-File-Name': os.path.basename(photo_path),
            'X-Goog-Upload-Protocol': 'raw',
        }
    ).text

    # Étape 2 : créer le média item dans l'album
    response = service.mediaItems().batchCreate(body={
        'albumId': album_id,
        'newMediaItems': [{
            'description': 'Photo prise par le Photobooth',
            'simpleMediaItem': {
                'uploadToken': upload_token
            }
        }]
    }).execute()

    print(f"Téléversé : {photo_path} => Google Photos")


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python google_photos_uploader.py <photo_path>")
    else:
        upload_photo(sys.argv[1])