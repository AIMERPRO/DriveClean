"""Отчёты в таблицах"""
import datetime
import logging

import config
from models.reports import Spreadsheet
from models.workprocess import Outcheck, Washcheck

from db.connection import Session

from . import connection_raw as db_conn

LOGGER = logging.getLogger('applog')


def get_spreadsheet(id_type, id_city=None, period=None):
    session = Session()
    value = session.query(Spreadsheet).filter(Spreadsheet.id_type == id_type,
                                              Spreadsheet.id_city == id_city, Spreadsheet.period == period).first()
    session.close()
    return value


def create_spreadsheet(id_type, id_drive, id_city=None, period=None):
    session = Session()
    new_sheet = Spreadsheet(
        id_city=id_city,
        id_type=id_type,
        id_drive=id_drive,
        period=period
    )
    session.add(new_sheet)
    session.commit()
    session.close()
    return True


def mark_spreadsheet_need_update(id_type, id_city=None, date_period_to_update=None):
    session = Session()
    sheet_item = session.query(Spreadsheet).filter(Spreadsheet.id_type ==
                                                   id_type, Spreadsheet.id_city == id_city).first()
    if sheet_item:
        sheet_item.need_update = 1
        sheet_item.date_period_to_update = date_period_to_update
        session.commit()
    session.close()
    return True


def get_spreadsheets_to_update():
    session = Session()
    values_tuple = session.query(Spreadsheet).filter(Spreadsheet.need_update == 1).all()
    session.close()
    return values_tuple


def mark_spreadsheet_updated(id_sheet):
    session = Session()
    sheet_item = session.query(Spreadsheet).get(id_sheet)
    if sheet_item:
        sheet_item.need_update = 0
        sheet_item.date_update = datetime.datetime.now()
        sheet_item.date_period_to_update = None
        session.commit()
    session.close()
    return True


def get_report_data_checklist_avg(date_start, date_end):
    connection = db_conn.open_connection()
    result_lst = []
    try:
        cursor = connection.cursor()

        cursor.execute(f"""
            SELECT
            id, name
            FROM {config.DB_NAME_DRIVECLEAN_BOT}.washes 
            WHERE active=1
            ORDER BY name
        """)
        washes_tuple = cursor.fetchall()
        for wash in washes_tuple:
            id_wash, name_wash = wash
            outcheck_kol = None
            washcheck_kol = None

            cursor.execute(f"""
                SELECT
                SUM(outcheck_checklist.result*n_washcheck_elements.score)/(SELECT COUNT(*) FROM outcheck LEFT JOIN {config.DB_NAME_DRIVECLEAN_BOT}.smenaservices smsrv_inner ON (smsrv_inner.gosnomer=outcheck.gosnomer) WHERE smsrv_inner.date_create >= NOW() - INTERVAL 1 DAY AND outcheck.complete=1 AND smsrv_inner.id_wash=%s) DIV 1
                FROM outcheck out_ch
                LEFT JOIN outcheck_checklist ON (outcheck_checklist.id_outcheck=out_ch.id)
                LEFT JOIN n_washcheck_elements ON (n_washcheck_elements.id=outcheck_checklist.id_element)
                LEFT JOIN {config.DB_NAME_DRIVECLEAN_BOT}.smenaservices smserv ON (smserv.gosnomer=out_ch.gosnomer)
                WHERE out_ch.complete=1 AND smserv.id_wash=%s
                AND smserv.date_create >= NOW() - INTERVAL 1 DAY
                AND DATE(out_ch.datetime_create) BETWEEN %s AND %s
            """, (id_wash, id_wash, date_start, date_end))
            outcheck_kol_item = cursor.fetchone()
            if outcheck_kol_item:
                outcheck_kol = outcheck_kol_item[0]

            cursor.execute("""
                SELECT
                SUM(washcheck_checklist.result*n_washcheck_elements.score)/(SELECT COUNT(*) FROM washcheck WHERE id_wash=%s AND DATE(wsh_ch.datetime_create) BETWEEN %s AND %s) DIV 1
                FROM washcheck wsh_ch
                LEFT JOIN washcheck_checklist ON (washcheck_checklist.id_washcheck=wsh_ch.id)
                LEFT JOIN n_washcheck_elements ON (n_washcheck_elements.id=washcheck_checklist.id_element)
                WHERE wsh_ch.complete=1
                AND wsh_ch.id_wash=%s
                AND DATE(wsh_ch.datetime_create) BETWEEN %s AND %s
            """, (id_wash, date_start, date_end, id_wash, date_start, date_end))
            washcheck_kol_item = cursor.fetchone()
            if washcheck_kol_item:
                washcheck_kol = washcheck_kol_item[0]

            if outcheck_kol or washcheck_kol:
                result_lst.append((name_wash, outcheck_kol, washcheck_kol))

            # cursor.execute(f"""
            #     SELECT
            #     wsh.name,
            #     NULL,
            #     SUM(washcheck_checklist.result*n_washcheck_elements.score)/(SELECT COUNT(*) FROM washcheck WHERE id_wash=wsh_ch.id_wash AND DATE(wsh_ch.datetime_create) BETWEEN %s AND %s) DIV 1
            #     FROM washcheck wsh_ch
            #     LEFT JOIN washcheck_checklist ON (washcheck_checklist.id_washcheck=wsh_ch.id)
            #     LEFT JOIN n_washcheck_elements ON (n_washcheck_elements.id=washcheck_checklist.id_element)
            #     LEFT JOIN {config.DB_NAME_DRIVECLEAN_BOT}.washes wsh ON (wsh.id=wsh_ch.id_wash)
            #     WHERE wsh_ch.complete=1
            #     AND DATE(wsh_ch.datetime_create) BETWEEN %s AND %s
            #     GROUP BY wsh_ch.id_wash
            #     ORDER BY wsh.name
            # """, (date_start, date_end, date_start, date_end))
            # values_tuple = cursor.fetchall()

    finally:
        db_conn.close_connection(connection)
    return result_lst


def is_exist_unsent_washcheck():
    session = Session()
    value = session.query(Washcheck).filter(Washcheck.sent_to_sheet == 0).first()
    session.close()
    return value


def is_exist_unsent_outcheck():
    session = Session()
    value = session.query(Outcheck).filter(Outcheck.sent_to_sheet == 0).first()
    session.close()
    return value


def get_report_data_check_report_washcheck():
    connection = db_conn.open_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(f"""
            SELECT
            washcheck.id,
            DATE_FORMAT(washcheck.datetime_create, "%d.%m.%Y %H:%i"),
            DATE_FORMAT(CASE WHEN HOUR(washcheck.datetime_create)>=10 THEN DATE(washcheck.datetime_create) WHEN HOUR(washcheck.datetime_create)<=9 THEN DATE(washcheck.datetime_create) - INTERVAL 1 DAY ELSE NULL END, "%d.%m.%Y"),
            CONCAT(users.fam, ' ', users.im),
            wsh.name,
            washcheck.gosnomer,
            (SELECT CASE WHEN result=1 THEN "выполнен" WHEN result=0 THEN "не выполнен" END FROM washcheck_checklist WHERE id_washcheck=washcheck.id AND id_element=1) AS kuzov,
            (SELECT CASE WHEN result=1 THEN "выполнен" WHEN result=0 THEN "не выполнен" END FROM washcheck_checklist WHERE id_washcheck=washcheck.id AND id_element=4) AS porogi,
            (SELECT CASE WHEN result=1 THEN "выполнен" WHEN result=0 THEN "не выполнен" END FROM washcheck_checklist WHERE id_washcheck=washcheck.id AND id_element=12) AS zerk,
            (SELECT CASE WHEN result=1 THEN "выполнен" WHEN result=0 THEN "не выполнен" END FROM washcheck_checklist WHERE id_washcheck=washcheck.id AND id_element=5) AS bag,
            (SELECT CASE WHEN result=1 THEN "выполнен" WHEN result=0 THEN "не выполнен" END FROM washcheck_checklist WHERE id_washcheck=washcheck.id AND id_element=13) AS sid,
            (SELECT CASE WHEN result=1 THEN "выполнен" WHEN result=0 THEN "не выполнен" END FROM washcheck_checklist WHERE id_washcheck=washcheck.id AND id_element=14) AS kovr
            FROM washcheck
            LEFT JOIN users ON (users.id=washcheck.id_user)
            LEFT JOIN {config.DB_NAME_DRIVECLEAN_BOT}.washes wsh ON (wsh.id=washcheck.id_wash)
            WHERE washcheck.complete=1
            AND washcheck.sent_to_sheet=0
        """)
        values_washcheck_tuple = cursor.fetchall()

        cursor.execute(f"""
            SELECT
            DATE_FORMAT(washcheck.datetime_create, "%d.%m.%Y %H:%i"),
            DATE_FORMAT(CASE WHEN HOUR(washcheck.datetime_create)>=10 THEN DATE(washcheck.datetime_create) WHEN HOUR(washcheck.datetime_create)<=9 THEN DATE(washcheck.datetime_create) - INTERVAL 1 DAY ELSE NULL END, "%d.%m.%Y"),
            CONCAT(users.fam, ' ', users.im),
            wsh.name,
            washcheck.gosnomer,          
            (SELECT CONCAT(usr.fam, ' ', usr.im) FROM {config.DB_NAME_DRIVECLEAN_BOT}.smenaservices srv LEFT JOIN {config.DB_NAME_DRIVECLEAN_BOT}.users usr ON (usr.id=srv.id_user) WHERE srv.gosnomer=washcheck.gosnomer AND srv.date_create <= washcheck.datetime_create ORDER BY srv.id DESC LIMIT 1),
            (SELECT elems.penalty_rub FROM washcheck_checklist wch LEFT JOIN n_washcheck_elements elems ON (elems.id=wch.id_element) WHERE wch.id_washcheck=washcheck.id AND wch.result=0 AND wch.id_element=1) AS kuzov,
            (SELECT elems.penalty_rub FROM washcheck_checklist wch LEFT JOIN n_washcheck_elements elems ON (elems.id=wch.id_element) WHERE wch.id_washcheck=washcheck.id AND wch.result=0 AND wch.id_element=4) AS porogi,
            (SELECT elems.penalty_rub FROM washcheck_checklist wch LEFT JOIN n_washcheck_elements elems ON (elems.id=wch.id_element) WHERE wch.id_washcheck=washcheck.id AND wch.result=0 AND wch.id_element=12) AS zerk,
            (SELECT elems.penalty_rub FROM washcheck_checklist wch LEFT JOIN n_washcheck_elements elems ON (elems.id=wch.id_element) WHERE wch.id_washcheck=washcheck.id AND wch.result=0 AND wch.id_element=5) AS bag,
            (SELECT elems.penalty_rub FROM washcheck_checklist wch LEFT JOIN n_washcheck_elements elems ON (elems.id=wch.id_element) WHERE wch.id_washcheck=washcheck.id AND wch.result=0 AND wch.id_element=13) AS sid,
            (SELECT elems.penalty_rub FROM washcheck_checklist wch LEFT JOIN n_washcheck_elements elems ON (elems.id=wch.id_element) WHERE wch.id_washcheck=washcheck.id AND wch.result=0 AND wch.id_element=14) AS kovr
            FROM washcheck
            LEFT JOIN users ON (users.id=washcheck.id_user)
            LEFT JOIN {config.DB_NAME_DRIVECLEAN_BOT}.washes wsh ON (wsh.id=washcheck.id_wash)
            WHERE washcheck.complete=1
            AND washcheck.sent_to_sheet=0
        """)
        values_washcheck_penalty_tuple = cursor.fetchall()

    finally:
        db_conn.close_connection(connection)
    return (values_washcheck_tuple, values_washcheck_penalty_tuple)


def mark_washcheck_sent_to_sheet(ids_lst: list) -> bool:
    session = Session()
    for id_washcheck in ids_lst:
        washcheck_item = session.query(Washcheck).get(id_washcheck)
        if washcheck_item:
            washcheck_item.sent_to_sheet = 1
            session.commit()
    session.close()
    return True


def get_report_data_check_report_outcheck():
    connection = db_conn.open_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(f"""
            SELECT
            out_ch.id,
            DATE_FORMAT(out_ch.datetime_create, "%d.%m.%Y %H:%i"),
            DATE_FORMAT(CASE WHEN HOUR(out_ch.datetime_create)>=10 THEN DATE(out_ch.datetime_create) WHEN HOUR(out_ch.datetime_create)<=9 THEN DATE(out_ch.datetime_create) - INTERVAL 1 DAY ELSE NULL END, "%d.%m.%Y"),
            CONCAT(users.fam, ' ', users.im),
            out_ch.gosnomer,
            SUM(outcheck_checklist.result*n_washcheck_elements.score) DIV 1,
            (SELECT wsh.name FROM {config.DB_NAME_DRIVECLEAN_BOT}.smenaservices srv LEFT JOIN {config.DB_NAME_DRIVECLEAN_BOT}.washes wsh ON (wsh.id=srv.id_wash) WHERE srv.gosnomer=out_ch.gosnomer AND srv.date_create <= out_ch.datetime_create ORDER BY srv.id DESC LIMIT 1),
            (SELECT CONCAT(usr.fam, ' ', usr.im) FROM {config.DB_NAME_DRIVECLEAN_BOT}.smenaservices srv LEFT JOIN {config.DB_NAME_DRIVECLEAN_BOT}.users usr ON (usr.id=srv.id_user) WHERE srv.gosnomer=out_ch.gosnomer AND srv.date_create <= out_ch.datetime_create ORDER BY srv.id DESC LIMIT 1)
            FROM outcheck out_ch
            LEFT JOIN users ON (users.id=out_ch.id_user)
            LEFT JOIN outcheck_checklist ON (outcheck_checklist.id_outcheck=out_ch.id)
            LEFT JOIN n_washcheck_elements ON (n_washcheck_elements.id=outcheck_checklist.id_element)
            WHERE out_ch.complete=1 AND out_ch.sent_to_sheet=0
            GROUP BY out_ch.id
        """)
        values_outcheck_tuple = cursor.fetchall()

        cursor.execute(f"""
            SELECT
            DATE_FORMAT(outcheck.datetime_create, "%d.%m.%Y %H:%i"),
            DATE_FORMAT(CASE WHEN HOUR(outcheck.datetime_create)>=10 THEN DATE(outcheck.datetime_create) WHEN HOUR(outcheck.datetime_create)<=9 THEN DATE(outcheck.datetime_create) - INTERVAL 1 DAY ELSE NULL END, "%d.%m.%Y"),
            CONCAT(users.fam, ' ', users.im),
            outcheck.gosnomer,          
            (SELECT CONCAT(usr.fam, ' ', usr.im) FROM {config.DB_NAME_DRIVECLEAN_BOT}.smenaservices srv LEFT JOIN {config.DB_NAME_DRIVECLEAN_BOT}.users usr ON (usr.id=srv.id_user) WHERE srv.gosnomer=outcheck.gosnomer AND srv.date_create <= outcheck.datetime_create ORDER BY srv.id DESC LIMIT 1),
            (SELECT elems.penalty_rub FROM outcheck_checklist och LEFT JOIN n_washcheck_elements elems ON (elems.id=och.id_element) WHERE och.id_outcheck=outcheck.id AND och.result=0 AND och.id_element=1) AS kuzov,
            (SELECT elems.penalty_rub FROM outcheck_checklist och LEFT JOIN n_washcheck_elements elems ON (elems.id=och.id_element) WHERE och.id_outcheck=outcheck.id AND och.result=0 AND och.id_element=4) AS porogi,
            (SELECT elems.penalty_rub FROM outcheck_checklist och LEFT JOIN n_washcheck_elements elems ON (elems.id=och.id_element) WHERE och.id_outcheck=outcheck.id AND och.result=0 AND och.id_element=12) AS zerk,
            (SELECT elems.penalty_rub FROM outcheck_checklist och LEFT JOIN n_washcheck_elements elems ON (elems.id=och.id_element) WHERE och.id_outcheck=outcheck.id AND och.result=0 AND och.id_element=5) AS bag,
            (SELECT elems.penalty_rub FROM outcheck_checklist och LEFT JOIN n_washcheck_elements elems ON (elems.id=och.id_element) WHERE och.id_outcheck=outcheck.id AND och.result=0 AND och.id_element=13) AS sid,
            (SELECT elems.penalty_rub FROM outcheck_checklist och LEFT JOIN n_washcheck_elements elems ON (elems.id=och.id_element) WHERE och.id_outcheck=outcheck.id AND och.result=0 AND och.id_element=14) AS kovr
            FROM outcheck
            LEFT JOIN users ON (users.id=outcheck.id_user)
            WHERE outcheck.complete=1
            AND outcheck.sent_to_sheet=0
        """)
        values_outcheck_penalty_tuple = cursor.fetchall()

    finally:
        db_conn.close_connection(connection)
    return (values_outcheck_tuple, values_outcheck_penalty_tuple)


def mark_outcheck_sent_to_sheet(ids_lst: list) -> bool:
    session = Session()
    for id_outcheck in ids_lst:
        outcheck_item = session.query(Outcheck).get(id_outcheck)
        if outcheck_item:
            outcheck_item.sent_to_sheet = 1
            session.commit()
    session.close()
    return True
