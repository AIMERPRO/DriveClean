"""Фото и видео из бота"""
from db.connection import Session
from models.service import Media


def save_media(id_user, id_media_format, id_media_type, file_id, cloud_file_id, id_outcheck=None, id_washcheck_element=None):
    session = Session()
    new_media = Media(
        id_user=id_user,
        id_media_format=id_media_format,
        id_media_type=id_media_type,
        file_id=file_id,
        id_outcheck=id_outcheck,
        id_washcheck_element=id_washcheck_element,
        cloud_file_id=cloud_file_id
    )
    session.add(new_media)
    session.commit()
    session.close()
    return True


def get_media_tuple(id_user, id_media_type, id_outcheck=None, id_washcheck_element=None):
    session = Session()
    values_tuple = session.query(Media).filter(Media.id_user == id_user, Media.id_media_type ==
                                               id_media_type, Media.id_outcheck == id_outcheck,
                                               Media.id_washcheck_element == id_washcheck_element).all()
    session.close()
    return values_tuple
