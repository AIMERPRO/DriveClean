"""Фото и видео из бота"""
from models.model_service import Media

from db.connection import Session


def save_media(id_user, id_media_type, file_id, id_smena=None, id_req_tphelp=None, id_req_rpn=None, id_req_kapot=None, id_req_dopusl=None, id_smenaservice=None, sent_to_chat=None):
    session = Session()
    new_media = Media(
        id_user=id_user,
        id_media_type=id_media_type,
        file_id=file_id,
        id_smena=id_smena,
        id_req_tphelp=id_req_tphelp,
        id_req_rpn=id_req_rpn,
        id_req_kapot=id_req_kapot,
        id_req_dopusl=id_req_dopusl,
        id_smenaservice=id_smenaservice,
        sent_to_chat=sent_to_chat
    )
    session.add(new_media)
    session.commit()
    session.close()
    return True


def get_media_tuple(id_user, id_media_type, id_smena=None, id_req_tphelp=None, id_req_rpn=None, id_req_kapot=None, id_req_dopusl=None, id_smenaservice=None):
    session = Session()
    values_tuple = session.query(Media).filter(Media.id_user == id_user, Media.id_media_type == id_media_type, Media.id_smena == id_smena,
                                               Media.id_req_tphelp == id_req_tphelp, Media.id_req_rpn == id_req_rpn,
                                               Media.id_req_kapot == id_req_kapot, Media.id_req_dopusl == id_req_dopusl, Media.id_smenaservice == id_smenaservice).all()
    session.close()
    return values_tuple


def mark_media_sent(media_ids_lst: list) -> bool:  # TODO может как то группой помечать, по id_smenaservice например
    session = Session()
    for id_media in media_ids_lst:
        media_item = session.query(Media).get(id_media)
        if media_item:
            media_item.sent_to_chat = 1
    session.commit()
    session.close()
    return True
