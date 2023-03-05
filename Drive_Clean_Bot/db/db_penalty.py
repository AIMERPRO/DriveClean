"""Штрафы"""
from models.model_workprocess import PENALTY_CATEGORIES, Penalty, PenaltyType

from db.connection import Session

from . import connection_raw as db_conn


def get_penalty_types_by_category(id_penalty_category):
    session = Session()
    values_tuple = session.query(PenaltyType).filter(PenaltyType.id_penalty_category == id_penalty_category).all()
    session.close()
    return values_tuple


def get_penalty_type_by_name(id_penalty_category, penalty_type_name):
    session = Session()
    value = session.query(PenaltyType).filter(PenaltyType.id_penalty_category ==
                                              id_penalty_category, PenaltyType.name == penalty_type_name).first()
    session.close()
    return value


def add_new_penalty(id_user, id_smenaservice, id_penalty_category, id_penalty_type, id_author):
    session = Session()
    new_penalty = Penalty(
        id_user=id_user,
        id_smenaservice=id_smenaservice,
        id_penalty_category=id_penalty_category,
        id_penalty_type=id_penalty_type,
        id_author=id_author,
    )

    session.add(new_penalty)
    session.commit()
    session.close()
    return True


def put_progul_penalties(id_smena_date: int):
    connection = db_conn.open_connection()
    users_ids_list = []
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT 
            id_user
            FROM smena_notify
            WHERE response=0
            AND id_smena_date = %s
            AND id_user NOT IN (SELECT id_user FROM penalty WHERE id_smena_date=%s AND id_penalty_category=%s)
        """, (id_smena_date, id_smena_date, PENALTY_CATEGORIES['progul']))
        values_tuple = cursor.fetchall()
        for value in values_tuple:
            users_ids_list.append(value[0])

        if users_ids_list:
            cursor.execute("""
                INSERT INTO penalty
                (id_user, id_smena_date, id_penalty_category, date_nazn)
                SELECT 
                id_user,
                id_smena_date,
                %s,
                NOW()
                FROM smena_notify
                WHERE response=0
                AND id_smena_date=%s
                AND id_user NOT IN (SELECT id_user FROM penalty WHERE id_smena_date=%s AND id_penalty_category=%s)
            """, (PENALTY_CATEGORIES['progul'], id_smena_date, id_smena_date, PENALTY_CATEGORIES['progul']))
            connection.commit()
    finally:
        db_conn.close_connection(connection)

    return users_ids_list
