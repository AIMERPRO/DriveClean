"""Файловые ресурсы"""
import datetime

from models.model_service import Resource

from db.connection import Session


def get_unloaded_resources():
    session = Session()
    values_tuple = session.query(Resource).filter(Resource.file_id == None).all()
    session.close()
    return values_tuple


def set_file_id(res_name, file_id):
    session = Session()
    res_item = session.query(Resource).get(res_name)
    if res_item:
        res_item.file_id = file_id
        res_item.date_update = datetime.datetime.now()
        session.add(res_item)
        session.commit()
    session.close()
    return True


def get_res(res_name):
    session = Session()
    value = session.query(Resource).get(res_name)
    session.close()
    return value
