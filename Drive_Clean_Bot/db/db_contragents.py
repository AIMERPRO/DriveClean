"""Контрагенты"""
from models.model_contragents import (Contragent, ContragentOplPeriod,
                                      ContragentWash)
from sqlalchemy import desc

from db.connection import Session

from . import connection_raw as db_conn

# TODO выяснить, какое поле будет лучше всего для первичного ключа у контрагентов


def get_contragent_by_ndog(ndog: int) -> Contragent:
    session = Session()
    value = session.query(Contragent).filter(Contragent.ndog == ndog).first()
    session.close()
    return value


def create_contragent(ctr_name, ndog, id_city, docs_hyperlink, phone, fio, email):
    session = Session()
    new_contragent = Contragent(
        ctr_name=ctr_name,
        ndog=ndog,
        id_city=id_city,
        docs_hyperlink=docs_hyperlink,
        phone=phone,
        fio=fio,
        email=email
    )
    session.add(new_contragent)
    session.commit()
    session.close()
    return True


def get_contragent_wash_by_address(address: str) -> ContragentWash:
    session = Session()
    value = session.query(ContragentWash).filter(ContragentWash.address == address).first()
    session.close()
    return value


def create_contragent_wash(id_contragent, address, cost_bm_kop, cost_furgon_kop, cost_shuttle_kop, cost_pb_kop, cost_ps_kop, cost_chem_kop, cost_zhir_kop, cost_glue_kop, cost_polir_kop, cost_chempot_kop, cost_chern_kop, cost_fazwash_kop, cost_podpisk_kop, cost_benzov_kop, cost_nzmrz_kop):
    session = Session()
    new_contragent_wash = ContragentWash(
        id_contragent=id_contragent,
        address=address,
        cost_bm_kop=cost_bm_kop,
        cost_furgon_kop=cost_furgon_kop,
        cost_shuttle_kop=cost_shuttle_kop,
        cost_pb_kop=cost_pb_kop,
        cost_ps_kop=cost_ps_kop,
        cost_chem_kop=cost_chem_kop,
        cost_zhir_kop=cost_zhir_kop,
        cost_glue_kop=cost_glue_kop,
        cost_polir_kop=cost_polir_kop,
        cost_chempot_kop=cost_chempot_kop,
        cost_chern_kop=cost_chern_kop,
        cost_fazwash_kop=cost_fazwash_kop,
        cost_podpisk_kop=cost_podpisk_kop,
        cost_benzov_kop=cost_benzov_kop,
        cost_nzmrz_kop=cost_nzmrz_kop
    )
    session.add(new_contragent_wash)
    session.commit()
    session.close()
    return True


def get_last_contragents_opl_period() -> ContragentOplPeriod:
    session = Session()
    value = session.query(ContragentOplPeriod).order_by(desc(ContragentOplPeriod.id)).first()
    session.close()
    return value


def set_last_contragents_opl_period(date_start, date_end):
    session = Session()
    new_period = ContragentOplPeriod(
        date_start=date_start,
        date_end=date_end
    )
    session.add(new_period)
    session.commit()
    session.close()
    return True


def get_last_3_contragents_opl_periods():
    # TODO пока просто будем брать 3 последних периода, и высчитывать невыгруженные в реестр мойки по ним.
    # потом как то помечать, какие периоды мы уже просчитали
    session = Session()
    values_tuple = session.query(ContragentOplPeriod).order_by(desc(ContragentOplPeriod.id)).limit(3).all()
    session.close()
    return values_tuple


def check_and_create_opl_reestr_items(id_period):
    connection = db_conn.open_connection()
    try:
        cursor = connection.cursor()

        # TODO здесь берутся даже те мойки, которые не участвовали в текущем периоде, засоряя реестр выплат -
        # они всё равно не будут выгружены в spreadsheet, но будут висеть в таблице contragents_opl_reestr
        # с uploaded_to_sheet=0, типа как будто не выгруженные
        cursor.execute("""
            SELECT
            contragent_washes.id_contragent,
            contragent_washes.id
            FROM contragent_washes
            WHERE contragent_washes.active=1
            AND contragent_washes.id NOT IN (SELECT id_contragent_wash FROM contragents_opl_reestr WHERE id_period=%s)
        """, (id_period,))
        values_tuple = cursor.fetchall()

        if values_tuple:
            for value in values_tuple:
                id_contragent, id_contragent_wash = value
                cursor.execute("""
                    INSERT INTO contragents_opl_reestr
                    (id_contragent, id_contragent_wash, id_period, uploaded_to_sheet, date_create)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (id_contragent, id_contragent_wash, id_period, 0))
            connection.commit()

    finally:
        db_conn.close_connection(connection)
    return values_tuple
