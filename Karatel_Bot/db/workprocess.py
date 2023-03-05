"""Рабочие процессы"""
import logging

from db.connection import Session
from models.workprocess import (Outcheck, OutcheckChecklist, Washcheck,
                                WashcheckChecklist, WashcheckElements)

from . import connection_raw as db_conn

LOGGER = logging.getLogger('applog')


def get_smenaservice_id_by_gosnomer(gosnomer: str) -> int:
    connection = db_conn.open_connection_driveclean()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
            id
            FROM smenaservices
            WHERE gosnomer = %s
            AND date_create >= NOW() - INTERVAL 2 DAY
            ORDER BY id DESC LIMIT 1
        """, (gosnomer,))
        value = cursor.fetchone()
    finally:
        db_conn.close_connection(connection)

    if value:
        return value[0]
    return None


def get_washcheck_washes():
    connection = db_conn.open_connection_driveclean()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
            id, name
            FROM washes
            WHERE used_in_karatel_washcheck=1
        """)
        values_tuple = cursor.fetchall()
    finally:
        db_conn.close_connection(connection)
    return values_tuple


def get_washcheck_wash_by_name(name_wash: str):
    connection = db_conn.open_connection_driveclean()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
            id
            FROM washes
            WHERE name=%s
            AND used_in_karatel_washcheck=1
        """, (name_wash,))
        value = cursor.fetchone()
    finally:
        db_conn.close_connection(connection)

    if value:
        return value[0]
    return None


def create_new_washcheck(id_user: int, id_wash: int, gosnomer: str) -> int:
    session = Session()
    washcheck_item = Washcheck(
        id_user=id_user,
        id_wash=id_wash,
        gosnomer=gosnomer
    )
    session.add(washcheck_item)
    session.commit()
    id_washcheck = washcheck_item.id
    session.close()
    return id_washcheck


def get_washcheck_elements(exclude_elements_lst: list):
    session = Session()
    values_tuple = session.query(WashcheckElements).filter(WashcheckElements.active == 1,
                                                           WashcheckElements.id.notin_(exclude_elements_lst)).all()
    session.close()
    return values_tuple


def save_washcheck_elements(id_washcheck: int, washcheck_elements_results_lst: list) -> bool:
    session = Session()

    washcheck_item = session.query(Washcheck).get(id_washcheck)
    washcheck_item.complete = 1
    session.add(washcheck_item)

    for washcheck_elements_results_tuple in washcheck_elements_results_lst:
        id_element, result = washcheck_elements_results_tuple
        washcheck_checklist_item = WashcheckChecklist(
            id_washcheck=id_washcheck,
            id_element=id_element,
            result=result
        )
        session.add(washcheck_checklist_item)

    session.commit()
    session.close()
    return True


def create_new_outcheck(id_user: int, gosnomer: str) -> int:
    session = Session()
    outcheck_item = Outcheck(
        id_user=id_user,
        gosnomer=gosnomer
    )
    session.add(outcheck_item)
    session.commit()
    id_outcheck = outcheck_item.id
    session.close()
    return id_outcheck


def save_outcheck_elements(id_outcheck: int, outcheck_elements_results_lst: list) -> bool:
    session = Session()

    outcheck_item = session.query(Outcheck).get(id_outcheck)
    outcheck_item.complete = 1
    session.add(outcheck_item)

    for outcheck_elements_results_tuple in outcheck_elements_results_lst:
        id_element, result = outcheck_elements_results_tuple
        outcheck_checklist_item = OutcheckChecklist(
            id_outcheck=id_outcheck,
            id_element=id_element,
            result=result
        )
        session.add(outcheck_checklist_item)

    session.commit()
    session.close()
    return True
