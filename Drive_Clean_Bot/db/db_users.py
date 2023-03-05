"""Регистрация юзеров"""
import datetime
import random

from models.model_service import State
from models.model_users import REG_RESULTS, ROLES, District, Role, User
from models.model_workprocess import BrigadirOnDistrict, Schedule
from sqlalchemy import desc

from db.connection import Session

from . import connection_raw as db_conn


def get_user(id_user: int) -> User:
    """Объект юзера в БД"""
    session = Session()
    user = session.query(User).get(id_user)
    session.close()
    return user


def add_new_user(id_user: int, id_city: int, fam: str, im: str, ot: str, nick: str, datar: datetime.date, phone: str) -> bool:
    """Добавление нового юзера"""
    session = Session()

    user = session.query(User).get(id_user)
    if user:
        user.id_city = id_city
        user.id_role = ROLES['pending']
        user.fam = fam
        user.im = im
        user.ot = ot
        user.nick = nick
        user.datar = datar
        user.phone = phone
        user.reg = 0
        user.date_uvol = None
        user.active = 1
    else:
        user = User(
            id=id_user,
            id_city=id_city,
            id_role=ROLES['pending'],
            fam=fam,
            im=im,
            ot=ot,
            nick=nick,
            datar=datar,
            phone=phone
        )

    session.add(user)
    session.commit()
    session.close()
    return True


def update_phone_opl_service(id_user: int, phone_opl_service: str) -> bool:
    """Добавление нового юзера"""
    session = Session()

    user = session.query(User).get(id_user)
    if user:
        user.phone_opl_service = phone_opl_service
        session.add(user)
        session.commit()
    session.close()
    return True


def update_email(id_user: int, email: str) -> bool:
    """Обновление email у юзера"""
    session = Session()

    user = session.query(User).get(id_user)
    if user:
        user.email = email
        session.add(user)
        session.commit()
    session.close()
    return True


def get_admins():
    """Все админы"""
    session = Session()
    values_tuple = session.query(User).filter(User.id_role == ROLES['admin'], User.active == 1).all()
    session.close()
    return values_tuple


def get_unapprooved_users():
    """Юзеры, ожидающие подтверждения регистрации"""
    session = Session()
    values_tuple = session.query(User).filter(User.reg == 0).limit(18).all()
    session.close()
    return values_tuple


def get_users_without_district():
    """Юзеры, которым ещё не проставили район"""
    session = Session()
    values_tuple = session.query(User).filter(User.district == None, User.id_role.in_(
        [ROLES['worker'], ROLES['brigadir']]), User.active == 1).limit(18).all()  # TODO magic number (ограничение сообщений в секунду - 20)
    session.close()
    return values_tuple


def get_reg_roles():
    """Роли разрешённые к регистрации"""
    session = Session()
    values_tuple = session.query(Role).filter(Role.id > ROLES['pending']).order_by(desc(Role.id)).all()
    session.close()
    return values_tuple


def set_reg(id_user, id_role):
    """Одобрение или отклонение (id_role=0) регистрации"""
    session = Session()
    user = session.query(User).get(id_user)
    cur_role = session.query(Role).get(user.id_role)
    if cur_role.id > ROLES['pending']:
        return REG_RESULTS['already_reg']

    if id_role == 0:
        user.active = 0
    else:
        user.id_role = id_role
    user.reg = 1
    session.add(user)
    session.commit()
    session.close()

    return REG_RESULTS['success']


def get_districts_by_city(id_city):
    """Районы города"""
    session = Session()
    values_tuple = session.query(District).filter(District.id_city == id_city).all()
    session.close()
    return values_tuple


def set_district(id_user, district):
    """Установка района юзеру"""
    session = Session()
    user = session.query(User).get(id_user)
    if user:
        user.district = district
        session.add(user)
        session.commit()
    session.close()
    return True


def get_brigadirs_ids_without_schedules_table():
    """Бригадиры, у которых ещё нет персональной таблицы графиков"""
    connection = db_conn.open_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT users.id
            FROM users
            LEFT JOIN spreadsheets ON (spreadsheets.id_user=users.id)
            WHERE users.id_role=%s AND users.active=1 AND spreadsheets.id IS NULL 
        """, (ROLES['brigadir'],))
        values_tuple = cursor.fetchall()
    finally:
        db_conn.close_connection(connection)
    return values_tuple


def get_city_brigadirs(id_city: int):
    """Бригадиры города"""
    session = Session()
    values_tuple = session.query(User).filter(
        User.id_role == ROLES['brigadir'], User.id_city == id_city, User.active == 1).all()
    session.close()
    return values_tuple


def get_district_brigadirs(id_city, district):
    """Бригадиры района"""
    session = Session()
    values_tuple = session.query(User).join(BrigadirOnDistrict, BrigadirOnDistrict.id_brigadir == User.id).filter(
        BrigadirOnDistrict.id_city == id_city, BrigadirOnDistrict.district == district, BrigadirOnDistrict.active == 1, User.active == 1).all()
    session.close()
    return values_tuple


def append_brigadir_to_district(id_brigadir, id_city, district):
    """Добавление бригадира на район"""
    session = Session()
    brig_on_district_item = session.query(BrigadirOnDistrict).get([id_brigadir, id_city, district])
    if brig_on_district_item:
        brig_on_district_item.active = 1
        brig_on_district_item.date_change = datetime.datetime.now()
    else:
        brig_on_district_item = BrigadirOnDistrict(
            id_brigadir=id_brigadir,
            id_city=id_city,
            district=district
        )
    session.add(brig_on_district_item)
    session.commit()
    session.close()
    return True


def delete_brigadir_from_district(id_brigadir, id_city, district):
    """Снятие бригадира с района"""
    session = Session()
    brig_on_district_item = session.query(BrigadirOnDistrict).get([id_brigadir, id_city, district])
    if brig_on_district_item:
        brig_on_district_item.active = 0
        brig_on_district_item.date_change = datetime.datetime.now()
        session.add(brig_on_district_item)
        session.commit()
    session.close()
    return True


def get_my_responsible_districts(id_brigadir):
    """Кортеж районов, за которые ответственен этот бригадир"""
    session = Session()
    values_tuple = session.query(BrigadirOnDistrict).filter(
        BrigadirOnDistrict.id_brigadir == id_brigadir, BrigadirOnDistrict.active == 1).all()
    session.close()
    return values_tuple


def get_my_random_brigadir(user_item):
    session = Session()
    values_tuple = session.query(User).join(BrigadirOnDistrict, BrigadirOnDistrict.id_brigadir == User.id).filter(
        BrigadirOnDistrict.id_city == user_item.id_city, BrigadirOnDistrict.district == user_item.district, BrigadirOnDistrict.active == 1).all()
    if not values_tuple:  # не нашлось по району, тогда выберем любого бригадира города
        values_tuple = session.query(User).join(BrigadirOnDistrict, BrigadirOnDistrict.id_user == User.id).filter(
            BrigadirOnDistrict.id_city == user_item.id_city, BrigadirOnDistrict.active == 1).all()
    session.close()
    if values_tuple:
        return random.choice(values_tuple)
    return None


def search_users_by_fio_part(fam, id_user_me):
    session = Session()
    values_tuple = session.query(User).filter(User.fam.like(
        f'%{fam}%'), User.id != id_user_me, User.id_role != ROLES['admin'], User.active == 1).limit(48).all()
    session.close()
    return values_tuple


def fire_user(id_user):
    session = Session()

    user_item = session.query(User).get(id_user)
    if user_item:
        user_item.active = 0
        user_item.date_uvol = datetime.datetime.now()

    brig_district_item = session.query(BrigadirOnDistrict).filter(
        BrigadirOnDistrict.id_brigadir == id_user, BrigadirOnDistrict.active == 1).first()
    if brig_district_item:
        brig_district_item.active = 0
        brig_district_item.date_change = datetime.datetime.now()

    schedule_item = session.query(Schedule).filter(Schedule.id_user == id_user, Schedule.active == 1).first()
    if schedule_item:
        schedule_item.active = 0
        schedule_item.date_end = datetime.datetime.now()

    state_item = session.query(State).get(id_user)
    if state_item:
        session.delete(state_item)

    session.commit()
    session.close()
    return True


def is_user_exists_as_karatel(id_user: int) -> bool:
    """Существует ли юзер в базе карателей как активный работник"""
    connection_karatelbot = db_conn.open_connection_karatelbot()
    try:
        cursor_karatelbot = connection_karatelbot.cursor()
        cursor_karatelbot.execute("""
            SELECT 
            id 
            FROM users
            WHERE id=%s
            AND id_role=40
            AND active=1 AND reg=1
        """, (id_user,))
        value = cursor_karatelbot.fetchone()
    finally:
        db_conn.close_connection(connection_karatelbot)
    return value


def is_user_exists_as_teacher(phone: str) -> bool:
    """Существует ли юзер в базе бота новичков как учитель на мойке"""
    connection_newonebot = db_conn.open_connection_newonebot()
    try:
        cursor_newonebot = connection_newonebot.cursor()
        cursor_newonebot.execute("""
            SELECT 
            id 
            FROM washes
            WHERE teacher_phone = CONCAT("+", %s)
            AND active=1
        """, (phone,))
        value = cursor_newonebot.fetchone()
    finally:
        db_conn.close_connection(connection_newonebot)
    return value
