"""Параметры"""
from models.model_service import Pref

from db.connection import Session


def get_pref(name: str) -> Pref:
    session = Session()
    pref_item = session.query(Pref).get(name)
    session.close()
    return pref_item


def set_pref(name, intval=None, textval=None, dateval=None, datetimeval=None):
    session = Session()
    pref_item = session.query(Pref).get(name)
    if pref_item:
        pref_item.intval = intval
        pref_item.textval = textval
        pref_item.dateval = dateval
        pref_item.datetimeval = datetimeval
    else:
        pref_item = Pref(
            name=name,
            intval=intval,
            textval=textval,
            dateval=dateval,
            datetimeval=datetimeval
        )
    session.add(pref_item)
    session.commit()
    session.close()
    return True
