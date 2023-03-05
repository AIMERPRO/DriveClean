from spreadsheets import drive_api
from googleapiclient.http import MediaIoBaseUpload
from io import BytesIO
from sqlalchemy import text, select
from db.connection import engine
from db.workprocess import Outcheck


def save_outcheck_photo_to_cloud(file, name, folder_id):
    metadata = {
        'name': name,
        'parents': [folder_id]
    }

    media = MediaIoBaseUpload(
        BytesIO(file),
        chunksize=1024 * 1024,
        mimetype='image/jpeg',
        resumable=True
    )

    uploaded = drive_api.files().create(
        body=metadata,
        media_body=media
    ).execute()

    return uploaded.get('id')


def get_cloud_folder_id(parent_id, folder_name):
    files_list = drive_api.files().list(
        q=f"'{parent_id}' in parents and trashed = false and mimeType='application/vnd.google-apps.folder'",
        fields="files(id, name)"
    ).execute()
    folders = files_list.get('files', None)

    if folders and len(folders) != 0:
        for folder in folders:
            if folder_name.lower() == folder['name'].lower():
                return folder.get('id', None)
    return None


def create_folder_if_not_exist(parent_id, folder_name):
    folder_id = get_cloud_folder_id(parent_id, folder_name)
    if not folder_id:
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }
        folder = drive_api.files().create(body=folder_metadata).execute()
        return folder.get('id')

    return folder_id


def get_cloud_outcheck_folder_id(parent_id, id_outcheck):
    outcheck_folder_id = create_folder_if_not_exist(parent_id, 'Выездная проверка')

    query = select(
        Outcheck.gosnomer,
        Outcheck.datetime_create
    ).where(text(f'id={id_outcheck}'))

    gosnomer, datetime = engine.execute(query).fetchone()

    gosnomer_folder_id = create_folder_if_not_exist(outcheck_folder_id, gosnomer)

    date = str(datetime.date())
    date_folder_id = create_folder_if_not_exist(gosnomer_folder_id, date)

    return date_folder_id
