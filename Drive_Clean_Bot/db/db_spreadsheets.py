"""Отчёты в таблицах"""
import datetime
import logging

import config
from db.connection import Session
from models.model_contragents import ContragentOplReestr
from models.model_spreadsheets import Spreadsheet
from models.model_users import ROLES
from models.model_workprocess import PENALTY_CATEGORIES

from . import connection_raw as db_conn

LOGGER = logging.getLogger('applog')


def get_spreadsheet(id_city, id_type, id_user=None, period=None) -> Spreadsheet:
    session = Session()
    # subquery = session.query(Spreadsheet.id_type).filter(Spreadsheet.id_city == id_city).group_by(Spreadsheet.id_type).all()
    # values_tuple = session.query(SpreadsheetType).filter(SpreadsheetType.id.notin_(subquery)).all()
    value = session.query(Spreadsheet).filter(Spreadsheet.id_city == id_city, Spreadsheet.id_user == id_user,
                                              Spreadsheet.id_type == id_type, Spreadsheet.period == period).first()
    session.close()
    return value


def create_spreadsheet(id_city, id_type, id_drive, id_user=None, period=None):
    session = Session()
    new_sheet = Spreadsheet(
        id_city=id_city,
        id_user=id_user,
        id_type=id_type,
        id_drive=id_drive,
        period=period
    )
    session.add(new_sheet)
    session.commit()
    session.close()
    return True


def mark_spreadsheet_need_update(id_type, id_city, date_period_to_update=None):
    session = Session()
    sheets_tuple = session.query(Spreadsheet).filter(
        Spreadsheet.id_type == id_type, Spreadsheet.id_city == id_city).all()
    if sheets_tuple:
        for sheet_item in sheets_tuple:
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


def get_report_data_schedules(id_city, date_start, date_end, id_brigadir: int = None):
    connection = db_conn.open_connection()
    try:
        cursor = connection.cursor()
        if id_brigadir:
            cursor.execute("""
                SELECT
                id
                FROM users
                WHERE users.id_role=%s 
                AND users.id_city=(SELECT id_city FROM users WHERE id=%s) 
                AND users.active=1 
                AND users.district IN (SELECT district FROM brigadirs_districts WHERE id_city=(SELECT id_city FROM users WHERE id=%s) AND id_brigadir=%s)
            """, (ROLES['worker'], id_brigadir, id_brigadir, id_brigadir))
            users_ids_tuple = cursor.fetchall()
        else:
            cursor.execute("""
                SELECT
                id
                FROM users
                WHERE id_role IN (%s,%s)
                AND id_city = %s
                AND active=1
            """, (ROLES['worker'], ROLES['brigadir'], id_city))
            users_ids_tuple = cursor.fetchall()

        if not users_ids_tuple:
            return None
        users_ids_str = ",".join(str(x[0]) for x in users_ids_tuple)

        if id_brigadir:
            users_ids_str = f'{id_brigadir},{users_ids_str}'
            order_str = 'ORDER BY users.id_role, users.district, users.fam, users.im'
        else:
            order_str = 'ORDER BY users.district, users.fam, users.im'

        cursor.execute(f"""
            SELECT
            users.id,
            COALESCE(users.district,0),
            CONCAT(users.fam, ' ', users.im),
            users.phone,
            users.nick,
            users.active,
            schedules.week_template,
            GROUP_CONCAT(DISTINCT dopsmena.date_smena SEPARATOR ';'),
            GROUP_CONCAT(DISTINCT otmazki.date_smena SEPARATOR ';'),
            (SELECT GROUP_CONCAT(DISTINCT smena_dates.date_smena SEPARATOR ';') FROM smena_dates LEFT JOIN penalty ON (penalty.id_smena_date=smena_dates.id) WHERE penalty.id_user=users.id AND penalty.id_penalty_category=%s AND smena_dates.date_smena BETWEEN %s AND %s) AS progul_dates,
            (SELECT COUNT(id) FROM smenaservices WHERE smenaservices.id_user=users.id AND id_carsharing=1),
            (SELECT COUNT(id) FROM smenaservices WHERE smenaservices.id_user=users.id AND id_carsharing=2)
            FROM users
            LEFT JOIN schedules ON (schedules.id_user=users.id AND schedules.active=1)
            LEFT JOIN dopsmena ON (dopsmena.id_user=users.id AND dopsmena.approoved=1 AND dopsmena.date_smena BETWEEN %s AND %s)
            LEFT JOIN otmazki ON (otmazki.id_user=users.id AND otmazki.approoved=1 AND otmazki.date_smena BETWEEN %s AND %s)
            WHERE users.id IN ({users_ids_str})
            GROUP BY users.id
            {order_str}
        """, (PENALTY_CATEGORIES['progul'], date_start, date_end, date_start, date_end, date_start, date_end))
        values_tuple = cursor.fetchall()

        cursor.execute("""
            SELECT
            CONCAT(users.fam, ' ', users.im),
            users.phone,
            CASE WHEN users.active=1 THEN 'Активно' ELSE 'Неактивно' END
            FROM users
            WHERE id_role = %s
            AND id_city=%s
            AND (users.active=1 OR (users.active=0 AND users.date_uvol >= NOW() - INTERVAL 1 month))
        """, (ROLES['specprojects'], id_city))
        specprojects_tuple = cursor.fetchall()

    finally:
        db_conn.close_connection(connection)
    return (values_tuple, specprojects_tuple)


# TODO переделать на sqlalchemy orm
def get_report_data_smena_results(id_city, date_start, date_end, datetime_start_text, datetime_end_text):
    connection = db_conn.open_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
            CASE WHEN smena_dates.date_smena IS NOT NULL THEN DATE_FORMAT(smena_dates.date_smena, '%%d.%%m.%%Y') ELSE DATE_FORMAT(smenaservices.date_create, '%%d.%%m.%%Y') END,
            CONCAT(users.fam, ' ', users.im),
            users.phone,
            users.district,
            washes.name,
            DATE_FORMAT(smenaservices.date_create, '%%H:%%i'),
            smenaservices.gosnomer,
            n_carsharings.name,
            n_auto_class.name,
            n_auto_sr_type.name,
            n_wash_usl_type.name,
            smenaservices.omyv_percent,
            CASE WHEN smenaservices.daily=1 THEN 'да' ELSE 'нет' END,
            COUNT(dop_pb.id) AS pb,
            COUNT(dop_ps.id) AS ps,
            COALESCE(dop_chem.kol_elem,0) AS chem,
            COUNT(dop_bitum.id) AS bitum
            FROM smenaservices
            LEFT JOIN smena ON (smena.id = smenaservices.id_smena)
            LEFT JOIN smena_dates ON (smena_dates.id = smena.id_smena_date)
            LEFT JOIN users ON (users.id = smenaservices.id_user)
            LEFT JOIN washes ON (washes.id = smenaservices.id_wash)
            LEFT JOIN n_carsharings ON (n_carsharings.id = smenaservices.id_carsharing)
            LEFT JOIN n_auto_class ON (n_auto_class.id = smenaservices.id_auto_class)
            LEFT JOIN n_auto_sr_type ON (n_auto_sr_type.id = smenaservices.id_auto_sr_type)
            LEFT JOIN n_wash_usl_type ON (n_wash_usl_type.id = smenaservices.id_wash_usl_type)
            LEFT JOIN reqs_dopusl dop_pb ON (dop_pb.gosnomer=smenaservices.gosnomer AND dop_pb.id_user=smenaservices.id_user AND dop_pb.id_purity=2 AND dop_pb.decision=1 AND dop_pb.id_dopusl_type=1 AND (dop_pb.date_create BETWEEN %s AND %s))
            LEFT JOIN reqs_dopusl dop_ps ON (dop_ps.gosnomer=smenaservices.gosnomer AND dop_ps.id_user=smenaservices.id_user AND dop_ps.id_purity=2 AND dop_ps.decision=1 AND dop_ps.id_dopusl_type=2 AND (dop_ps.date_create BETWEEN %s AND %s))
            LEFT JOIN reqs_dopusl dop_chem ON (dop_chem.gosnomer=smenaservices.gosnomer AND dop_chem.id_user=smenaservices.id_user AND dop_chem.id_purity=2 AND dop_chem.decision=1 AND dop_chem.id_dopusl_type=3 AND (dop_chem.date_create BETWEEN %s AND %s))
            LEFT JOIN reqs_dopusl dop_bitum ON (dop_bitum.gosnomer=smenaservices.gosnomer AND dop_bitum.id_user=smenaservices.id_user AND dop_bitum.id_purity=2 AND dop_bitum.decision=1 AND dop_bitum.id_dopusl_type=4 AND (dop_bitum.date_create BETWEEN %s AND %s))
            WHERE users.id_city=%s
            AND ((smenaservices.daily=0 AND smena_dates.date_smena BETWEEN %s AND %s) OR (smenaservices.daily=1 AND smenaservices.date_create BETWEEN %s AND %s))
            GROUP BY smenaservices.id
            ORDER BY smenaservices.id
        """, (datetime_start_text, datetime_end_text, datetime_start_text, datetime_end_text, datetime_start_text, datetime_end_text, datetime_start_text, datetime_end_text, id_city, date_start, date_end, datetime_start_text, datetime_end_text))
        values_tuple = cursor.fetchall()
    finally:
        db_conn.close_connection(connection)
    return values_tuple


def get_report_data_konsol(id_city, date_start, date_end, datetime_start_text, datetime_end_text):
    connection = db_conn.open_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT 
            CONCAT(users.fam, ' ', users.im),
            users.phone,
            (SELECT COUNT(*) FROM smena LEFT JOIN smena_dates ON (smena_dates.id=smena.id_smena_date) WHERE id_user=users.id AND (smena_dates.date_smena BETWEEN %s AND %s)) AS smena_count,
            (SELECT COUNT(*) FROM smenaservices LEFT JOIN smena ON (smena.id=smenaservices.id_smena) LEFT JOIN smena_dates ON (smena_dates.id=smena.id_smena_date) WHERE smenaservices.id_user=users.id AND daily=0 AND (smena_dates.date_smena BETWEEN %s AND %s)) AS kol_night,
            (SELECT COUNT(*) FROM smenaservices WHERE id_user=users.id AND daily=1 AND (date_create BETWEEN %s AND %s)) AS kol_day,
            0 AS photo
            FROM users
            WHERE users.id_city=%s 
            AND users.id_role IN (%s, %s)
            ORDER BY users.fam, users.im
        """, (date_start, date_end, date_start, date_end, datetime_start_text, datetime_end_text, id_city, ROLES['worker'], ROLES['brigadir']))
        values_tuple = cursor.fetchall()
    finally:
        db_conn.close_connection(connection)
    return values_tuple


def get_workers_payment_registry_report_data_peregon(date_start, date_end, datetime_start_text, datetime_end_text, specprojects_phones_str):
    connection = db_conn.open_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(f"""
            SELECT
            users.id,
            users.id_city,
            users.id_role,
            CASE WHEN users.phone_opl_service="-" THEN 'Cash' ELSE 'Konsol' END AS opl_type,
            CONCAT(users.fam, ' ', users.im, ' ', users.ot) AS fio,
            users.phone AS phone_bot,
            CASE WHEN users.phone_opl_service IS NOT NULL THEN users.phone_opl_service ELSE 'нет данных' END AS phone_konsol,
            n_city.name AS city_name,
            users.district AS district,
            (SELECT COUNT(smena.id) FROM smena LEFT JOIN smena_dates ON (smena_dates.id=smena.id_smena_date) WHERE id_user=users.id AND smena_dates.date_smena BETWEEN %s AND %s) AS smena_kol,
            (SELECT COUNT(id) FROM smenaservices WHERE id_user=users.id AND daily=0 AND date_create BETWEEN %s AND %s) AS night_cars_kol,
            (SELECT COUNT(id) FROM smenaservices WHERE id_user=users.id AND daily=0 AND id_carsharing=1 AND date_create BETWEEN %s AND %s) AS noch_ya,
            (SELECT COUNT(id) FROM smenaservices WHERE id_user=users.id AND daily=0 AND id_carsharing=2 AND date_create BETWEEN %s AND %s) AS noch_city,
            (SELECT COUNT(id) FROM smenaservices WHERE id_user=users.id AND daily=1 AND id_carsharing=1 AND date_create BETWEEN %s AND %s) AS day_ya,
            0 AS transit_ya,
            0 AS renov_ya
            FROM users
            LEFT JOIN n_city ON (n_city.id=users.id_city)
            WHERE users.id_role IN (%s,%s,%s,%s,%s)
            AND 
            (users.id IN (SELECT DISTINCT id_user FROM smenaservices WHERE smenaservices.date_create BETWEEN %s AND %s) 
            OR users.id IN (SELECT id_support FROM reqs_dopusl WHERE id_purity=2 AND decision=1 AND date_create BETWEEN %s AND %s) 
            OR users.id IN (SELECT id FROM users WHERE id_role=20 AND id_city=1 AND (active=1 OR (active=0 AND date_uvol BETWEEN %s AND %s))) 
            OR users.id IN (SELECT DISTINCT id_user FROM {config.DB_NAME_KARATEL}.outcheck WHERE complete=1 AND datetime_create BETWEEN %s AND %s) 
            OR users.id IN (SELECT DISTINCT id_user FROM {config.DB_NAME_KARATEL}.washcheck WHERE complete=1 AND datetime_create BETWEEN %s AND %s) 
            OR (users.id_role IN (%s,%s) AND users.active=1 AND users.id_city IN (1,2)) 
            OR users.phone IN ({specprojects_phones_str}))
        """, (date_start, date_end, datetime_start_text, datetime_end_text, datetime_start_text, datetime_end_text, datetime_start_text, datetime_end_text, datetime_start_text, datetime_end_text, ROLES['worker'], ROLES['brigadir'], ROLES['karatel'], ROLES['pending'], ROLES['specprojects'], datetime_start_text, datetime_end_text, datetime_start_text, datetime_end_text, datetime_start_text, datetime_end_text, datetime_start_text, datetime_end_text, datetime_start_text, datetime_end_text, ROLES['brigadir'], ROLES['specprojects']))
        common_tuple = cursor.fetchall()

        # TODO а вот это делается конечно в спешке, и очень неоптимально (проходится по каждому юзеру), нужна оптимизация
        novichok_lst = []
        for common_item in common_tuple:
            id_user = common_item[0]
            cursor.execute("""
                SELECT 
                smenaservices.id, 
                smenaservices.date_create 
                FROM smenaservices
                WHERE smenaservices.daily=0 AND id_smena IN 
                    (SELECT * FROM
                        (SELECT 
                        id
                        FROM smena
                        WHERE id_user=%s
                        LIMIT 5) 
                    AS t)
                AND smenaservices.date_create BETWEEN %s AND %s
                LIMIT 50
            """, (id_user, datetime_start_text, datetime_end_text))
            novichok_tuple = cursor.fetchall(
            )  # берём первые 5 смен и 50 машин (максимум), если они попадают в отчётный период (то есть по итогу может быть и меньше)
            if novichok_tuple:
                novichok_lst.append((id_user, len(novichok_tuple)))

        cursor.execute("""
            SELECT
            penalty.id_user, 
            COUNT(penalty.id)
            FROM penalty
            LEFT JOIN smena_dates ON (smena_dates.id=penalty.id_smena_date)
            WHERE id_penalty_category=%s AND smena_dates.date_smena BETWEEN %s AND %s
            GROUP BY penalty.id_user
        """, (PENALTY_CATEGORIES['progul'], date_start, date_end))
        penalty_progul_tuple = cursor.fetchall()

        cursor.execute("""
            SELECT
            id_user, 
            COUNT(id)
            FROM penalty
            WHERE id_penalty_category=%s AND date_nazn BETWEEN %s AND %s
            GROUP BY id_user
        """, (PENALTY_CATEGORIES['photo_before_after'], datetime_start_text, datetime_end_text))
        penalty_photo_tuple = cursor.fetchall()

        # TODO дальше блок расчётов по бригадирам, он у нас такой пока только по МСК, так что город жёстко задан
        leftovers_percents_lst = []
        kol_auto_total = 0

        cursor.execute("""
            SELECT
            DISTINCT(smena_dates.date_smena),
            car_leftovers.kol_leftover
            FROM car_leftovers
            LEFT JOIN smena_dates ON (smena_dates.id=car_leftovers.id_smena_date)
            WHERE smena_dates.date_smena BETWEEN %s AND %s
            AND car_leftovers.id_city=1
        """, (date_start, date_end))
        car_leftovers_tuple = cursor.fetchall()

        for car_leftover in car_leftovers_tuple:
            cur_date_smena, kol_leftover = car_leftover
            cur_datetime_start_text = cur_date_smena.strftime("%Y-%m-%d 10:00:00")
            cur_datetime_end_text = (cur_date_smena + datetime.timedelta(days=1)).strftime("%Y-%m-%d 09:59:59")

            cursor.execute("""
                SELECT
                COUNT(smenaservices.id)
                FROM smenaservices
                LEFT JOIN users ON (users.id=smenaservices.id_user)
                WHERE users.id_city=1
                AND smenaservices.date_create BETWEEN %s AND %s
            """, (cur_datetime_start_text, cur_datetime_end_text))
            cur_kol_auto = cursor.fetchone()[0]
            kol_auto_total += cur_kol_auto

            if cur_kol_auto + kol_leftover > 0:
                leftovers_percent = round(kol_leftover * 100 / (cur_kol_auto + kol_leftover))
            else:
                continue

            leftovers_percents_lst.append(leftovers_percent)

        if len(leftovers_percents_lst) > 0:
            msk_leftover_percent_average = round(sum(leftovers_percents_lst) / len(leftovers_percents_lst))
        else:
            msk_leftover_percent_average = 100

        cursor.execute("""
            SELECT
            id
            FROM users
            WHERE id_role=20
            AND id_city=1
            AND (active=1 OR (active=0 AND date_uvol BETWEEN %s AND %s))
        """, (datetime_start_text, datetime_end_text))
        brigadirs_tuple = cursor.fetchall()

        if len(brigadirs_tuple) > 0:
            msk_kol_brig_cars_divided_pabratski = round(kol_auto_total / len(brigadirs_tuple))
        else:
            msk_kol_brig_cars_divided_pabratski = 0

    finally:
        db_conn.close_connection(connection)

    karatel_ids_lst = []
    karatel_outcheck_carskol_tuple = None
    karatel_washcheck_carskol_tuple = None
    try:
        connection_karatel = db_conn.open_connection_karatelbot()
        cursor_karatel = connection_karatel.cursor()

        cursor_karatel.execute("""
            SELECT  
            id 
            FROM users
            WHERE id_role=40 AND active=1
        """)
        karatels_values_tuple = cursor_karatel.fetchall()

        for karatel_value in karatels_values_tuple:
            karatel_ids_lst.append(karatel_value[0])

        cursor_karatel.execute("""
            SELECT 
            id_user,
            COUNT(*)
            FROM outcheck
            WHERE complete=1
            AND datetime_create BETWEEN %s AND %s
            GROUP BY id_user
        """, (datetime_start_text, datetime_end_text))
        karatel_outcheck_carskol_tuple = cursor_karatel.fetchall()

        cursor_karatel.execute("""
            SELECT 
            id_user,
            COUNT(*)
            FROM washcheck
            WHERE complete=1
            AND datetime_create BETWEEN %s AND %s
            GROUP BY id_user
        """, (datetime_start_text, datetime_end_text))
        karatel_washcheck_carskol_tuple = cursor_karatel.fetchall()

    #     LOGGER.info('start collecting karatel purity')
    #     cursor_karatel.execute("""
    #         SELECT
    #         001_BotData.ChatId,
    #         ROUND(100 - SUM(IF(040_KaratelData.IdCategory=1,1,0)) / (SELECT COUNT(*) FROM 030_ElementsByCategory WHERE IdCategory=1 AND IdElements>55) * 100, 2) AS Cat1,
    #         ROUND(100 - SUM(IF(040_KaratelData.IdCategory=2,1,0)) / (SELECT COUNT(*) FROM 030_ElementsByCategory WHERE IdCategory=2 AND IdElements>55) * 100, 2) AS Cat2
    #         FROM 040_KaratelData
    #         LEFT JOIN 001_BotData ON (001_BotData.ShiftDate=040_KaratelData.ReportDate AND 001_BotData.CarPlate=040_KaratelData.CarPlate)
    #         WHERE 040_KaratelData.ReportDate BETWEEN %s AND %s
    #         GROUP BY 040_KaratelData.ReportDate, 040_KaratelData.CarPlate
    #         HAVING Cat1<=85 OR Cat2<=80
    #     """, (date_start, date_end))
    #     karatel_purity_percents_tuple = cursor_karatel.fetchall()
    #     LOGGER.info('END collecting karatel purity')

        db_conn.close_connection(connection_karatel)
    except Exception as ex:
        LOGGER.error(ex)

    trainer_phones_lst = []
    trainers_with_students_count = None
    connection_newonebot = db_conn.open_connection_newonebot()
    try:
        cursor_newonebot = connection_newonebot.cursor()
        cursor_newonebot.execute("""
            SELECT 
            REPLACE(teacher_phone, '+', '')
            FROM washes
        """)
        phones_tuple = cursor_newonebot.fetchall()

        for phone_value in phones_tuple:
            trainer_phones_lst.append(phone_value[0])

        cursor_newonebot.execute("""
            SELECT DISTINCT
            REPLACE(washes.teacher_phone, '+', '') AS trainer_phone,
            COUNT(trainings.id_user)
            FROM trainings
            LEFT JOIN washes ON (washes.id=trainings.id_wash)
            WHERE trainings.is_arrived=1
            AND DATE(training_datetime) BETWEEN %s AND %s
            GROUP BY trainer_phone
        """, (date_start, date_end))
        trainers_with_students_count = cursor_newonebot.fetchall()

    finally:
        db_conn.close_connection(connection_newonebot)

    return (common_tuple, novichok_lst, karatel_ids_lst, karatel_outcheck_carskol_tuple, karatel_washcheck_carskol_tuple, trainer_phones_lst, trainers_with_students_count, penalty_progul_tuple, penalty_photo_tuple, msk_leftover_percent_average, msk_kol_brig_cars_divided_pabratski)


def get_workers_payment_registry_report_data_tp(date_start, date_end):
    connection = db_conn.open_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
            users.id,
            CASE WHEN users.phone_opl_service="-" THEN 'Cash' ELSE 'Konsol' END AS opl_type,
            CONCAT(users.fam, ' ', users.im, ' ', users.ot) AS fio,
            users.phone AS phone_bot,
            CASE WHEN users.phone_opl_service IS NOT NULL THEN users.phone_opl_service ELSE 'нет данных' END AS phone_konsol,
            CASE WHEN users.id_role=%s THEN 10*11 ELSE SUM(ROUND(TIME_TO_SEC(TIMEDIFF(smena.datetime_end, smena.datetime_start)) / 60 / 60)) END
            FROM users
            LEFT JOIN smena ON (smena.id_user=users.id)
            LEFT JOIN smena_dates ON (smena_dates.id=smena.id_smena_date)
            WHERE users.id_role IN (%s,%s,%s)
            AND (users.id_role=%s OR (users.id_role!=%s AND smena_dates.date_smena BETWEEN %s AND %s))
            GROUP BY users.id
        """, (ROLES['support_daily'], ROLES['support'], ROLES['support_daily'], ROLES['support_penaltier'], ROLES['support_daily'], ROLES['support_daily'], date_start, date_end))
        common_tuple = cursor.fetchall()

        cursor.execute("""
            SELECT
            penalty.id_user, 
            COUNT(penalty.id)
            FROM penalty
            LEFT JOIN smena_dates ON (smena_dates.id=penalty.id_smena_date)
            WHERE id_penalty_category=%s AND smena_dates.date_smena BETWEEN %s AND %s
            GROUP BY penalty.id_user
        """, (PENALTY_CATEGORIES['progul'], date_start, date_end))
        penalty_progul_tuple = cursor.fetchall()

    finally:
        db_conn.close_connection(connection)

    return (common_tuple, penalty_progul_tuple)


def get_contragents_opl_reestr_report_data():
    connection = db_conn.open_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
            contragent_washes.id,
			contragents_opl_periods.id,
            contragents.ctr_name AS contrag_name,
            n_city.name AS city_name,
            washes.name AS wash_name,
            contragents.ndog AS dog_num,
            CONCAT(DATE_FORMAT(contragents_opl_periods.date_start, "%d.%m"), ' - ', DATE_FORMAT(contragents_opl_periods.date_end, "%d.%m.%Y")) AS period_okaz,
            NULLIF((SELECT COUNT(id) FROM smenaservices WHERE id_auto_class=1 AND smenaservices.id_wash=washes.id AND DATE(smenaservices.date_create) BETWEEN contragents_opl_periods.date_start AND contragents_opl_periods.date_end),0) AS econ_kol,
            NULLIF(contragent_washes.cost_bm_kop,0) AS cost_bm_kop,
            NULLIF((SELECT COUNT(id) FROM smenaservices WHERE id_auto_class=4 AND smenaservices.id_wash=washes.id AND DATE(smenaservices.date_create) BETWEEN contragents_opl_periods.date_start AND contragents_opl_periods.date_end),0) AS furgon_kol,
            NULLIF(contragent_washes.cost_furgon_kop,0) AS cost_furgon_kop,
            NULLIF((SELECT COUNT(id) FROM smenaservices WHERE id_auto_class=5 AND smenaservices.id_wash=washes.id AND DATE(smenaservices.date_create) BETWEEN contragents_opl_periods.date_start AND contragents_opl_periods.date_end),0) AS shuttle_kol,
            NULLIF(contragent_washes.cost_shuttle_kop,0) AS cost_shuttle_kop,
            NULLIF((SELECT COUNT(id) FROM reqs_dopusl WHERE reqs_dopusl.id_dopusl_type=1 AND reqs_dopusl.id_purity=2 AND reqs_dopusl.decision=1 AND reqs_dopusl.id_wash=washes.id AND DATE(reqs_dopusl.date_create) BETWEEN contragents_opl_periods.date_start AND contragents_opl_periods.date_end),0) AS pb_kol,
            NULLIF(contragent_washes.cost_pb_kop,0) AS cost_pb_kop,
            NULLIF((SELECT COUNT(id) FROM reqs_dopusl WHERE reqs_dopusl.id_dopusl_type=2 AND reqs_dopusl.id_purity=2 AND reqs_dopusl.decision=1 AND reqs_dopusl.id_wash=washes.id AND DATE(reqs_dopusl.date_create) BETWEEN contragents_opl_periods.date_start AND contragents_opl_periods.date_end),0) AS ps_kol,
            NULLIF(contragent_washes.cost_ps_kop,0) AS cost_ps_kop,
            NULLIF((SELECT CAST(COALESCE(SUM(kol_elem),0) AS INTEGER) FROM reqs_dopusl WHERE reqs_dopusl.id_dopusl_type=3 AND reqs_dopusl.id_purity=2 AND reqs_dopusl.decision=1 AND reqs_dopusl.id_wash=washes.id AND DATE(reqs_dopusl.date_create) BETWEEN contragents_opl_periods.date_start AND contragents_opl_periods.date_end),0) AS chem_kol,
            NULLIF(contragent_washes.cost_chem_kop,0) AS cost_chem_kop,
            NULL AS zhir_kol,
            NULLIF(contragent_washes.cost_zhir_kop,0) AS cost_zhir_kop,
            NULL AS glue_kol,
            NULLIF(contragent_washes.cost_glue_kop,0) AS cost_glue_kop,
            NULL AS polir_kol,
            NULLIF(contragent_washes.cost_polir_kop,0) AS cost_polir_kop,
            NULL AS chempot_kol,
            NULLIF(contragent_washes.cost_chempot_kop,0) AS cost_chempot_kop,
            NULL AS chern_kol,
            NULLIF(contragent_washes.cost_chern_kop,0) AS cost_chern_kop,
            NULL AS fazwash_kol,
            NULLIF(contragent_washes.cost_fazwash_kop,0) AS cost_fazwash_kop,
            NULL AS podpisk_kol,
            NULLIF(contragent_washes.cost_podpisk_kop,0) AS cost_podpisk_kop,
            NULL AS benzov_kol,
            NULLIF(contragent_washes.cost_benzov_kop,0) AS cost_benzov_kop,
            NULL AS nzmrz_kol,
            NULLIF(contragent_washes.cost_nzmrz_kop,0) AS cost_nzmrz_kop,
            NULL AS itogo_sum,
            NULL AS sver_status,
            NULL AS opl_status,
            NULL AS act_num            
            FROM contragent_washes
            LEFT JOIN contragents ON (contragents.id=contragent_washes.id_contragent)
            LEFT JOIN washes ON (washes.name=contragent_washes.address)
            LEFT JOIN n_city ON (n_city.id=washes.id_city)        
            LEFT JOIN contragents_opl_reestr ON (contragents_opl_reestr.id_contragent_wash=contragent_washes.id)
            LEFT JOIN contragents_opl_periods ON (contragents_opl_periods.id=contragents_opl_reestr.id_period)
            WHERE washes.active=1
            AND contragents_opl_reestr.uploaded_to_sheet=0
            GROUP BY contragents_opl_periods.id, contragent_washes.id
        """)
        values_tuple = cursor.fetchall()
    finally:
        db_conn.close_connection(connection)
    return values_tuple


def mark_opl_reestr_uploaded(opl_reestr_items_list):
    session = Session()
    for item in opl_reestr_items_list:
        id_contragent_wash, id_period = item
        opl_reestr_item = session.query(ContragentOplReestr).get([id_contragent_wash, id_period])
        if opl_reestr_item:
            opl_reestr_item.uploaded_to_sheet = 1
    session.commit()
    session.close()
    return True


def get_report_data_supports_smenas(date_start, date_end):
    connection = db_conn.open_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT 
            DATE_FORMAT(smena_dates.date_smena, '%%d.%%m.%%Y'),
            CONCAT(users.fam, ' ', users.im),
            DATE_FORMAT(smena.datetime_start, '%%d.%%m.%%Y %%H:%%i'),
            DATE_FORMAT(smena.datetime_end, '%%d.%%m.%%Y %%H:%%i')
            FROM smena
            LEFT JOIN smena_dates ON (smena_dates.id=smena.id_smena_date)
            LEFT JOIN users ON (users.id=smena.id_user)
            WHERE users.id_role=%s
            AND smena_dates.date_smena BETWEEN %s AND %s
            ORDER BY users.fam, users.im
        """, (ROLES['support'], date_start, date_end))
        values_tuple = cursor.fetchall()
    finally:
        db_conn.close_connection(connection)
    return values_tuple


def get_report_data_supports_dopusl(datetime_start_text, datetime_end_text):
    connection = db_conn.open_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT 
            CONCAT(users_worker.fam, ' ', users_worker.im),
            reqs_dopusl.gosnomer,
            n_dopusl_types.name,
            n_dopusl_purity.name,
            DATE_FORMAT(reqs_dopusl.date_create, '%%d.%%m.%%Y %%H:%%i') AS date_create,
            CONCAT(users_support.fam, ' ', users_support.im),
            DATE_FORMAT(reqs_dopusl.sent_to_support_datetime, '%%d.%%m.%%Y %%H:%%i') AS sent_to_support_datetime,
            CASE WHEN reqs_dopusl.decision=1 THEN 'Принято' WHEN reqs_dopusl.decision=0 THEN 'Отказ' ELSE NULL END AS decision,
            DATE_FORMAT(reqs_dopusl.processed_by_support_datetime, '%%d.%%m.%%Y %%H:%%i') AS processed_by_support_datetime,
            DATE_FORMAT(reqs_dopusl.response_sent_to_worker_datetime, '%%d.%%m.%%Y %%H:%%i') AS response_sent_to_worker_datetime
            FROM reqs_dopusl
            LEFT JOIN users users_worker ON (users_worker.id=reqs_dopusl.id_user)
            LEFT JOIN users users_support ON (users_support.id=reqs_dopusl.id_support)
            LEFT JOIN n_dopusl_types ON (n_dopusl_types.id=reqs_dopusl.id_dopusl_type)
            LEFT JOIN n_dopusl_purity ON (n_dopusl_purity.id=reqs_dopusl.id_purity)
            WHERE reqs_dopusl.ready=1
            AND reqs_dopusl.date_create BETWEEN %s AND %s
        """, (datetime_start_text, datetime_end_text))
        values_tuple = cursor.fetchall()
    finally:
        db_conn.close_connection(connection)
    return values_tuple


def get_report_data_supports_reqs(datetime_start_text, datetime_end_text):
    connection = db_conn.open_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            (SELECT 
            CONCAT(users_worker.fam, ' ', users_worker.im),
            reqs_kapot.gosnomer,
            "Капот" AS zapros,
            "" AS zapr_type,
            DATE_FORMAT(reqs_kapot.date_create, '%%d.%%m.%%Y %%H:%%i') AS created_at,
            CONCAT(users_support.fam, ' ', users_support.im),
            DATE_FORMAT(reqs_kapot.sent_to_support_datetime, '%%d.%%m.%%Y %%H:%%i') AS sent_to_support_datetime,
            CASE WHEN reqs_kapot.decision=1 THEN 'Принято' WHEN reqs_kapot.decision=0 THEN 'Отказ' ELSE NULL END AS decision,
            DATE_FORMAT(reqs_kapot.processed_by_support_datetime, '%%d.%%m.%%Y %%H:%%i') AS processed_by_support_datetime,
            DATE_FORMAT(reqs_kapot.response_sent_to_worker_datetime, '%%d.%%m.%%Y %%H:%%i') AS response_sent_to_worker_datetime
            FROM reqs_kapot
            LEFT JOIN users users_worker ON (users_worker.id=reqs_kapot.id_user)
            LEFT JOIN users users_support ON (users_support.id=reqs_kapot.id_support)
            WHERE reqs_kapot.ready=1
            AND reqs_kapot.date_create BETWEEN %s AND %s
            )

            UNION ALL

            (SELECT 
            CONCAT(users_worker.fam, ' ', users_worker.im),
            reqs_rpn.gosnomer,
            "РПН",
            "",
            DATE_FORMAT(reqs_rpn.date_create, '%%d.%%m.%%Y %%H:%%i'),
            CONCAT(users_support.fam, ' ', users_support.im),
            DATE_FORMAT(reqs_rpn.sent_to_support_datetime, '%%d.%%m.%%Y %%H:%%i'),
            CASE WHEN reqs_rpn.decision=1 THEN 'Принято' WHEN reqs_rpn.decision=0 THEN 'Отказ' ELSE NULL END,
            DATE_FORMAT(reqs_rpn.processed_by_support_datetime, '%%d.%%m.%%Y %%H:%%i'),
            DATE_FORMAT(reqs_rpn.response_sent_to_worker_datetime, '%%d.%%m.%%Y %%H:%%i')
            FROM reqs_rpn
            LEFT JOIN users users_worker ON (users_worker.id=reqs_rpn.id_user)
            LEFT JOIN users users_support ON (users_support.id=reqs_rpn.id_support)
            WHERE reqs_rpn.ready=1
            AND reqs_rpn.date_create BETWEEN %s AND %s
            )

            UNION ALL

            (SELECT 
            CONCAT(users_worker.fam, ' ', users_worker.im),
            reqs_tphelp.gosnomer,
            "Обращение в ТП",
            n_tphelp_types.name,
            DATE_FORMAT(reqs_tphelp.date_create, '%%d.%%m.%%Y %%H:%%i'),
            CONCAT(users_support.fam, ' ', users_support.im),
            DATE_FORMAT(reqs_tphelp.sent_to_support_datetime, '%%d.%%m.%%Y %%H:%%i'),
            CASE WHEN reqs_tphelp.processed_by_support=1 THEN 'Обработано' ELSE '-' END,
            DATE_FORMAT(reqs_tphelp.processed_by_support_datetime, '%%d.%%m.%%Y %%H:%%i'),
            DATE_FORMAT(reqs_tphelp.response_sent_to_worker_datetime, '%%d.%%m.%%Y %%H:%%i')
            FROM reqs_tphelp
            LEFT JOIN users users_worker ON (users_worker.id=reqs_tphelp.id_user)
            LEFT JOIN users users_support ON (users_support.id=reqs_tphelp.id_support)
            LEFT JOIN n_tphelp_types ON (n_tphelp_types.id=reqs_tphelp.id_tphelp_type)
            WHERE reqs_tphelp.ready=1
            AND reqs_tphelp.date_create BETWEEN %s AND %s
            )

            ORDER BY created_at
        """, (datetime_start_text, datetime_end_text, datetime_start_text, datetime_end_text, datetime_start_text, datetime_end_text))
        values_tuple = cursor.fetchall()
    finally:
        db_conn.close_connection(connection)
    return values_tuple


def get_report_data_supports_penalty(date_start, date_end):
    connection = db_conn.open_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
            DATE_FORMAT(penalty.date_nazn, '%%d.%%m.%%Y %%H:%%i') AS date_nazn,
            CONCAT(users_support.fam, ' ', users_support.im) AS fio_support,
            penalty_category.name,
            penalty_type.name,
            CONCAT(users_worker.fam, ' ', users_worker.im) AS fio_worker
            FROM penalty
            LEFT JOIN users users_worker ON (users_worker.id=penalty.id_user)
            LEFT JOIN users users_support ON (users_support.id=penalty.id_author)
            LEFT JOIN penalty_category ON (penalty_category.id=penalty.id_penalty_category)
            LEFT JOIN penalty_type ON (penalty_type.id=penalty.id_penalty_type)
            WHERE penalty.id_penalty_category<50
            AND DATE(penalty.date_nazn) BETWEEN %s AND %s
        """, (date_start, date_end))
        values_tuple = cursor.fetchall()
    finally:
        db_conn.close_connection(connection)
    return values_tuple


def get_report_data_auto_avg_kol(date_start: datetime.date, weekdays_dict: dict):
    date_day_before_start = date_start - datetime.timedelta(days=1)
    connection = db_conn.open_connection()
    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
            users.district,
            CONCAT(users.fam, ' ', users.im), 
            ROUND(COUNT(smenaservices.id) / (SELECT COUNT(*) FROM smena WHERE id_user=smenaservices.id_user 
                        AND DATE(smena.datetime_start) >= %s)) DIV 1,
            (SELECT COUNT(*) FROM smena WHERE id_user=smenaservices.id_user 
                        AND DATE(smena.datetime_start) >= %s) DIV 1
            FROM smenaservices
            LEFT JOIN users ON (users.id=smenaservices.id_user)
            WHERE users.id_role IN (20,30) AND users.id_city=1
            AND users.active=1 AND users.reg=1
            AND smenaservices.id_smena IS NOT NULL
            AND DATE(smenaservices.date_create) >= %s
            GROUP BY smenaservices.id_user
            ORDER BY users.fam, users.im
        """, (date_day_before_start, date_day_before_start, date_start))
        workers_tuple = cursor.fetchall()

        cursor.execute("""
            SELECT 
            washes.district,
            washes.name,

            FLOOR((SELECT 
                COUNT(id)
                FROM smenaservices
                WHERE id_wash=washes.id
                AND DATE(smenaservices.date_create) >= %s
                AND WEEKDAY(smenaservices.date_create) = 0
            ) / %s) DIV 1 AS mon, 

            FLOOR((SELECT 
                COUNT(id)
                FROM smenaservices
                WHERE id_wash=washes.id
                AND DATE(smenaservices.date_create) >= %s
                AND WEEKDAY(smenaservices.date_create) = 1
            ) / %s) DIV 1 AS tue, 

            FLOOR((SELECT 
                COUNT(id)
                FROM smenaservices
                WHERE id_wash=washes.id
                AND DATE(smenaservices.date_create) >= %s
                AND WEEKDAY(smenaservices.date_create) = 2
            ) / %s) DIV 1 AS wed, 

            FLOOR((SELECT 
                COUNT(id)
                FROM smenaservices
                WHERE id_wash=washes.id
                AND DATE(smenaservices.date_create) >= %s
                AND WEEKDAY(smenaservices.date_create) = 3
            ) / %s) DIV 1 AS thu, 

            FLOOR((SELECT 
                COUNT(id)
                FROM smenaservices
                WHERE id_wash=washes.id
                AND DATE(smenaservices.date_create) >= %s
                AND WEEKDAY(smenaservices.date_create) = 4
            ) / %s) DIV 1 AS fri, 

            FLOOR((SELECT 
                COUNT(id)
                FROM smenaservices
                WHERE id_wash=washes.id
                AND DATE(smenaservices.date_create) >= %s
                AND WEEKDAY(smenaservices.date_create) = 5
            ) / %s) DIV 1 AS sat, 

            FLOOR((SELECT 
                COUNT(id)
                FROM smenaservices
                WHERE id_wash=washes.id
                AND DATE(smenaservices.date_create) >= %s
                AND WEEKDAY(smenaservices.date_create) = 6
            ) / %s) DIV 1 AS sun

            FROM washes
            WHERE washes.active=1 AND washes.id_city=1
            ORDER BY washes.district, washes.name
        """, (date_start, weekdays_dict[0],
              date_start, weekdays_dict[1],
              date_start, weekdays_dict[2],
              date_start, weekdays_dict[3],
              date_start, weekdays_dict[4],
              date_start, weekdays_dict[5],
              date_start, weekdays_dict[6]
              ))
        washes_tuple = cursor.fetchall()
    finally:
        db_conn.close_connection(connection)
    return (workers_tuple, washes_tuple)
