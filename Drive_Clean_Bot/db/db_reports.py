"""Отчёты текстовые"""
import datetime

from models.model_service import MEDIA_TYPES, ServiceChat
from models.model_smena import SmenaDate
from models.model_users import ROLES

from db.connection import Session

from . import connection_raw as db_conn


def get_service_chat(name: str) -> ServiceChat:
    session = Session()
    value = session.query(ServiceChat).get(name)
    session.close()
    return value


def get_all_service_chats() -> ServiceChat:
    session = Session()
    values_tuple = session.query(ServiceChat).all()
    session.close()
    return values_tuple


def get_whohowmuch_chatreport(id_city: int, district: int, id_smena_date: int) -> tuple:  # TODO переделать на sqlalchemy orm
    connection = db_conn.open_connection()
    try:
        cursor = connection.cursor()
        if district > 0:
            cursor.execute("""
                SELECT
                CONCAT(users.fam, ' ', users.im),
                COUNT(*) AS cnt
                FROM smenaservices
                LEFT JOIN smena ON (smena.id=smenaservices.id_smena)
                LEFT JOIN users ON (users.id=smena.id_user)
                WHERE smena.id_smena_date=%s
                AND users.id_city=%s
                AND users.district=%s
                GROUP BY users.id
                ORDER BY cnt DESC, users.fam, users.im ASC
            """, (id_smena_date, id_city, district))
        else:
            cursor.execute("""
                SELECT
                CONCAT(users.fam, ' ', users.im),
                COUNT(*) AS cnt
                FROM smenaservices
                LEFT JOIN smena ON (smena.id=smenaservices.id_smena)
                LEFT JOIN users ON (users.id=smena.id_user)
                WHERE smena.id_smena_date=%s
                AND users.id_city=%s
                AND users.district IS NULL
                GROUP BY users.id
                ORDER BY cnt DESC, users.fam, users.im ASC
            """, (id_smena_date, id_city))
        values_tuple = cursor.fetchall()
    finally:
        db_conn.close_connection(connection)
    return values_tuple


def get_appearance_chatreport(id_city: int, district: int, id_smena_date: int) -> tuple:
    connection = db_conn.open_connection()
    try:
        cursor = connection.cursor()
        if district > 0:
            cursor.execute("""
                SELECT
                CONCAT(users.fam, ' ', users.im),
                smena_notify.response,
                CASE WHEN smena_notify.response=1 THEN 'да' ELSE 'нет' END
                FROM smena_notify
                LEFT JOIN users ON (users.id=smena_notify.id_user)
                WHERE smena_notify.id_smena_date=%s
                AND users.id_city=%s
                AND users.district=%s
                AND users.id_role IN (%s,%s)
                GROUP BY users.id
                ORDER BY smena_notify.response DESC, users.fam, users.im ASC
            """, (id_smena_date, id_city, district, ROLES['worker'], ROLES['brigadir']))
        else:
            cursor.execute("""
                SELECT
                CONCAT(users.fam, ' ', users.im),
                smena_notify.response,
                CASE WHEN smena_notify.response=1 THEN 'да' ELSE 'нет' END
                FROM smena_notify
                LEFT JOIN users ON (users.id=smena_notify.id_user)
                WHERE smena_notify.id_smena_date=%s
                AND users.id_city=%s
                AND users.id_role IN (%s,%s)
                AND users.district IS null
                GROUP BY users.id
                ORDER BY smena_notify.response DESC, users.fam, users.im ASC
            """, (id_smena_date, id_city, ROLES['worker'], ROLES['brigadir']))
        values_tuple = cursor.fetchall()
    finally:
        db_conn.close_connection(connection)
    return values_tuple


def get_myworkerslist_chatreport(id_brigadir: int) -> tuple:
    connection = db_conn.open_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
            CONCAT(users.fam, ' ', users.im),
            users.phone,
            schedules.week_template
            FROM users
            LEFT JOIN brigadirs_districts ON (brigadirs_districts.id_city=users.id_city AND brigadirs_districts.district=users.district)
            LEFT JOIN schedules ON (schedules.id_user=users.id AND schedules.active=1)
            WHERE brigadirs_districts.id_brigadir=%s
            AND users.active=1
            GROUP BY users.id
            ORDER BY users.fam, users.im
        """, (id_brigadir,))
        values_tuple = cursor.fetchall()
    finally:
        db_conn.close_connection(connection)
    return values_tuple


def get_chatreport_mine_period_results(id_user: int, date_start: datetime.date, date_end: datetime.date) -> tuple:
    connection = db_conn.open_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT 
            COUNT(smenaservices.id) 
            FROM smenaservices 
            LEFT JOIN smena ON (smena.id=smenaservices.id_smena) 
            LEFT JOIN smena_dates ON (smena_dates.id=smena.id_smena_date) 
            WHERE smenaservices.id_user = %s 
            AND daily=0 
            AND (smena_dates.date_smena BETWEEN %s AND %s)
        """, (id_user, date_start, date_end))
        kol_night = cursor.fetchone()[0]

        cursor.execute("""
            SELECT 
            COUNT(smenaservices.id) 
            FROM smenaservices 
            WHERE id_user = %s 
            AND daily = 1 
            AND (DATE(date_create) BETWEEN %s AND %s)
        """, (id_user, date_start, date_end))
        kol_day = cursor.fetchone()[0]
    finally:
        db_conn.close_connection(connection)
    return (kol_night, kol_day)


def get_chatreport_mine_last_smena_results(id_user: int, date_smena: datetime.date) -> tuple:
    connection = db_conn.open_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT 
            COUNT(smenaservices.id) 
            FROM smenaservices 
            LEFT JOIN smena ON (smena.id=smenaservices.id_smena) 
            LEFT JOIN smena_dates ON (smena_dates.id=smena.id_smena_date) 
            WHERE smenaservices.id_user = %s 
            AND daily=0 
            AND smena_dates.date_smena = %s
        """, (id_user, date_smena))
        kol_night = cursor.fetchone()[0]

        cursor.execute("""
            SELECT 
            COUNT(smenaservices.id) 
            FROM smenaservices 
            WHERE id_user = %s 
            AND daily = 1 
            AND DATE(date_create) = %s
        """, (id_user, date_smena))
        kol_day = cursor.fetchone()[0]
    finally:
        db_conn.close_connection(connection)
    return (kol_night, kol_day)


def get_chatreport_major_smenaresults(id_city: int, datetime_start_text: str, datetime_end_text: str, last_smenadate_item: SmenaDate) -> tuple:
    connection = db_conn.open_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
                SELECT COUNT(smena.id)
                FROM smena
                LEFT JOIN users ON (users.id=smena.id_user)
                WHERE users.id_city=%s 
                AND smena.id_smena_date = %s
                AND smena.id_user NOT IN (SELECT id_user FROM smena LEFT JOIN users ON (users.id=smena.id_user) WHERE users.id_role IN (20,30) GROUP BY smena.id_user HAVING COUNT(smena.id)=1)
            """, (id_city, last_smenadate_item.id))
        kol_rab = cursor.fetchone()[0]

        cursor.execute("""
                SELECT users.id
                FROM users
                LEFT JOIN smenaservices ON (smenaservices.id_user=users.id)
                WHERE users.id_city=%s 
                AND smenaservices.daily=1
                AND (smenaservices.date_create BETWEEN %s AND %s)
                AND users.id NOT IN (SELECT id_user FROM smena LEFT JOIN users ON (users.id=smena.id_user) WHERE users.id_role IN (20,30) GROUP BY smena.id_user HAVING COUNT(smena.id)=1)
                GROUP BY users.id
            """, (id_city, datetime_start_text, datetime_end_text))
        kol_rab_dn = len(cursor.fetchall())

        cursor.execute("""
                SELECT COUNT(smena.id)
                FROM smena
                LEFT JOIN users ON (users.id=smena.id_user)
                WHERE users.id_city=%s 
                AND smena.id_smena_date = %s
                AND smena.id_user IN (SELECT id_user FROM smena LEFT JOIN users ON (users.id=smena.id_user) WHERE users.id_role IN (20,30) GROUP BY smena.id_user HAVING COUNT(smena.id)=1)
            """, (id_city, last_smenadate_item.id))
        kol_rab_new = cursor.fetchone()[0]

        cursor.execute("""
                SELECT COUNT(smenaservices.id)
                FROM smenaservices
                LEFT JOIN smena ON (smena.id=smenaservices.id_smena)
                LEFT JOIN users ON (users.id=smena.id_user)
                WHERE users.id_city=%s 
                AND smenaservices.daily=0
                AND (smenaservices.date_create BETWEEN %s AND %s)
                AND smenaservices.daily=0
                AND smena.id_user NOT IN (SELECT id_user FROM smena LEFT JOIN users ON (users.id=smena.id_user) WHERE users.id_role IN (20,30) GROUP BY smena.id_user HAVING COUNT(smena.id)=1)
            """, (id_city, datetime_start_text, datetime_end_text))
        kol_auto = cursor.fetchone()[0]

        cursor.execute("""
                SELECT COUNT(smenaservices.id)
                FROM smenaservices
                LEFT JOIN users ON (users.id=smenaservices.id_user)
                WHERE users.id_city=%s 
                AND smenaservices.daily=1
                AND (smenaservices.date_create BETWEEN %s AND %s)
                AND smenaservices.id_user NOT IN (SELECT id_user FROM smena LEFT JOIN users ON (users.id=smena.id_user) WHERE users.id_role IN (20,30) GROUP BY smena.id_user HAVING COUNT(smena.id)=1)
            """, (id_city, datetime_start_text, datetime_end_text))
        kol_auto_dn = cursor.fetchone()[0]

        cursor.execute("""
                SELECT COUNT(smenaservices.id)
                FROM smenaservices
                LEFT JOIN smena ON (smena.id=smenaservices.id_smena)
                LEFT JOIN users ON (users.id=smena.id_user)
                WHERE users.id_city=%s 
                AND (smenaservices.date_create BETWEEN %s AND %s)
                AND smena.id_user IN (SELECT id_user FROM smena LEFT JOIN users ON (users.id=smena.id_user) WHERE users.id_role IN (20,30) GROUP BY smena.id_user HAVING COUNT(smena.id)=1)
            """, (id_city, datetime_start_text, datetime_end_text))
        kol_auto_new = cursor.fetchone()[0]

        # cursor.execute("""
        #         SELECT
        #         COALESCE(SUM(serv_omyv), 0),
        #         COALESCE(TRUNCATE(SUM(serv_nzmrz_percent) / 100, 2), 0) AS nzmrz
        #         FROM smenaservices
        #         LEFT JOIN smena ON (smena.id=smenaservices.id_smena)
        #         LEFT JOIN users ON (users.id=smena.id_user)
        #         WHERE users.id_city=%s AND
        #         smena.datasmena=%s
        #     """, (id_city, datasmena))
        # omyv_tuple = cursor.fetchone()

        cursor.execute("""
                SELECT COUNT(*)
                FROM users
                WHERE id_city=%s
                AND date_uvol BETWEEN %s AND %s
            """, (id_city, datetime_start_text, datetime_end_text))
        kol_rab_lost = cursor.fetchone()[0]
    finally:
        db_conn.close_connection(connection)
    return kol_rab, kol_rab_dn, kol_rab_new, kol_auto, kol_auto_dn, kol_auto_new, kol_rab_lost


def get_smenaservice_media_dirtyclean_unsent():
    connection = db_conn.open_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
            smenaservices.id,
            smenaservices.gosnomer,
            DATE_FORMAT(smenaservices.date_create, "%d.%m.%Y %H:%i"),
            CONCAT(users.fam, ' ', users.im),
            CONCAT('+', users.phone),
            washes.name
            FROM smenaservices
            LEFT JOIN users ON (users.id=smenaservices.id_user)
            LEFT JOIN washes ON (washes.id=smenaservices.id_wash)
            WHERE smenaservices.id IN (SELECT DISTINCT id_smenaservice FROM media WHERE sent_to_chat=0)
            LIMIT 2
        """)
        smenaservices_info_tuple = cursor.fetchall()
        if not smenaservices_info_tuple:
            return None

        report_lst = []
        for smenaservice_info in smenaservices_info_tuple:
            id_smenaservice, gosnomer, date_create, fio, phone, wash_name = smenaservice_info

            cursor.execute("""
                SELECT 
                id,
                file_id
                FROM media
                WHERE id_smenaservice=%s
                AND id_media_type=%s
            """, (id_smenaservice, MEDIA_TYPES['smenaservice_dirty']))
            dirty_media_tuple = cursor.fetchall()

            cursor.execute("""
                SELECT 
                id,
                file_id
                FROM media
                WHERE id_smenaservice=%s
                AND id_media_type=%s
            """, (id_smenaservice, MEDIA_TYPES['smenaservice_clean']))
            clean_media_tuple = cursor.fetchall()

            report_lst.append((gosnomer, date_create, fio, phone, wash_name, dirty_media_tuple, clean_media_tuple))
    finally:
        db_conn.close_connection(connection)
    return report_lst
