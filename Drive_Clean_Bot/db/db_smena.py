"""Смены"""
import datetime

from sqlalchemy import desc, func

from db.connection import Session
from models.model_smena import (DopSmena, Smena, SmenaDate, SmenaNotify,
                                SmenaService, Wash, WorkersCount)
from models.model_users import ROLES, District, User
from models.model_workprocess import CarLeftover, Otmazki, Schedule


def get_scheds_stuff(smenadate: SmenaDate):  # TODO везде как тут - добавить типы переменных
    session = Session()
    sheds_tuple = session.query(Schedule).join(User, User.id == Schedule.id_user).filter(User.id_role.in_(
        [ROLES['worker'], ROLES['brigadir'], ROLES['support']]), User.active == 1, Schedule.active == 1).all()
    users_tuple = session.query(User).filter(User.id_role.in_(
        [ROLES['worker'], ROLES['brigadir'], ROLES['support']]), User.active == 1).all()
    dopsmena_tuple = session.query(DopSmena).filter(
        DopSmena.date_smena == smenadate.date_smena, DopSmena.approoved == 1).all()
    otgul_tuple = session.query(Otmazki).filter(
        Otmazki.date_smena == smenadate.date_smena, Otmazki.approoved == 1).all()
    session.close()
    return sheds_tuple, users_tuple, dopsmena_tuple, otgul_tuple


def get_last_smenadate() -> SmenaDate:
    session = Session()
    value = session.query(SmenaDate).order_by(desc(SmenaDate.id)).first()
    session.close()
    return value


def set_last_smenadate(last_smena_date):
    session = Session()
    new_smena_date = SmenaDate(
        date_smena=last_smena_date
    )
    session.add(new_smena_date)
    session.commit()
    session.close()
    return True


def finish_smenadate():
    session = Session()
    smenadate = session.query(SmenaDate).filter(SmenaDate.finished == 0).first()
    if smenadate:
        smenadate.finished = 1
        session.add(smenadate)
        session.commit()
    session.close()
    return True


def close_abandoned_smenas():
    session = Session()
    abandoned_smenas_list = []
    users_ids_list = []
    values_tuple = session.query(Smena).filter(Smena.finished == 0).all()
    if values_tuple:
        for smena in values_tuple:
            smena.datetime_end = datetime.datetime.now()
            smena.abandoned = 1
            smena.finished = 1
            abandoned_smenas_list.append(smena)
            users_ids_list.append(smena.id_user)
        session.add_all(abandoned_smenas_list)
        session.commit()
    session.close()
    return users_ids_list


def get_user_cur_opened_smena_by_date(id_user, smenadate):
    session = Session()
    value = session.query(Smena).filter(Smena.id_user == id_user, Smena.id_smena_date == smenadate.id).first()
    session.close()
    return value


def get_user_unfinished_smena(id_user):
    session = Session()
    value = session.query(Smena).filter(Smena.id_user == id_user, Smena.finished == 0).first()
    session.close()
    return value


def close_smena(id_smena, id_early_smena_end_reason, custom_early_smena_end_reason, id_leftover_cars_kol):
    session = Session()
    smena = session.query(Smena).filter(Smena.id == id_smena, Smena.finished == 0).first()
    if smena:
        smena.datetime_end = datetime.datetime.now()
        smena.id_early_smena_end_reason = id_early_smena_end_reason
        smena.custom_early_smena_end_reason = custom_early_smena_end_reason
        smena.id_leftover_cars_kol = id_leftover_cars_kol
        smena.finished = 1
        session.commit()
    session.close()
    return True


def close_nostrict_smena(id_smena):
    """Закрытие смены у тех кто не перегонщик (у саппортов)"""
    session = Session()
    smena = session.query(Smena).filter(Smena.id == id_smena, Smena.finished == 0).first()
    if smena:
        smena.datetime_end = datetime.datetime.now()
        smena.nostrict = 1
        smena.finished = 1
        session.commit()
    session.close()
    return True


def is_user_on_smena(id_user):
    session = Session()
    value = session.query(Smena).filter(Smena.id_user == id_user, Smena.finished == 0).first()
    session.close()
    return value


def open_smena(id_user, smenadate):
    session = Session()
    new_smena = Smena(
        id_smena_date=smenadate.id,
        id_user=id_user
    )
    smena_notify_item = session.query(SmenaNotify).get([smenadate.id, id_user])
    if smena_notify_item:
        smena_notify_item.response = 1
    else:
        smena_notify_item = SmenaNotify(
            id_smena_date=smenadate.id,
            id_user=id_user,
            response=1
        )
    session.add(smena_notify_item)
    session.add(new_smena)
    session.commit()
    session.close()
    return True


def set_smena_notify_users(smenadate_item, users_lst):
    session = Session()
    for user in users_lst:
        smena_notify_item = session.query(SmenaNotify).get([smenadate_item.id, user.id])
        if not smena_notify_item:
            smena_notify_item = SmenaNotify(
                id_smena_date=smenadate_item.id,
                id_user=user.id
            )
            session.add(smena_notify_item)
    session.commit()
    return True


def get_districts_by_city(id_city):
    session = Session()
    values_tuple = session.query(District).filter(District.id_city == id_city).order_by(District.district).all()
    session.close()
    return values_tuple


def is_district_exists(id_city, district):
    session = Session()
    value = session.query(District).filter(District.id_city == id_city, District.district == district).first()
    session.close()
    return value


def get_washes_by_district(id_city, district):
    session = Session()
    values_tuple = session.query(Wash).filter(Wash.id_city == id_city,
                                              Wash.district == district, Wash.active == 1).all()
    session.close()
    return values_tuple


def get_wash_by_name(id_city, district, name):
    session = Session()
    value = session.query(Wash).filter(Wash.id_city == id_city, Wash.district ==
                                       district, Wash.name == name, Wash.active == 1).first()
    session.close()
    return value


def add_new_smenaservice(id_user, daily, id_smena, id_wash, id_carsharing, dispatch_photostatus, gosnomer, id_auto_class, id_auto_sr_type, id_wash_usl_type, omyv_percent):
    session = Session()
    smenaservice = SmenaService(
        id_user=id_user,
        daily=daily,
        id_smena=id_smena,
        id_wash=id_wash,
        gosnomer=gosnomer,
        id_carsharing=id_carsharing,
        dispatch_photostatus=dispatch_photostatus,
        id_auto_class=id_auto_class,
        id_auto_sr_type=id_auto_sr_type,
        id_wash_usl_type=id_wash_usl_type,
        omyv_percent=omyv_percent
    )

    session.add(smenaservice)
    session.commit()
    session.close()
    return True


def get_smenaservices_by_smena(id_smena):
    session = Session()
    values_tuple = session.query(SmenaService).filter(SmenaService.id_smena == id_smena).all()
    session.close()
    return values_tuple


def get_smenaservice_by_gosnomer(gosnomer: str, id_city: int) -> SmenaService:
    session = Session()
    value = session.query(SmenaService).join(User, User.id == SmenaService.id_user).filter(
        SmenaService.gosnomer == gosnomer, User.id_city == id_city).order_by(desc(SmenaService.id)).first()
    session.close()
    return value


def get_last_user_wash(id_user):
    """Мойка, на которой в ТЕКУЩЕЙ смене последний раз работал этот юзер"""
    session = Session()

    wash = None
    cur_smena = session.query(Smena).filter(Smena.id_user == id_user, Smena.finished == 0).first()
    if cur_smena:
        last_smenaservice = session.query(SmenaService).filter(
            SmenaService.id_smena == cur_smena.id).order_by(desc(SmenaService.id)).first()
        if last_smenaservice:
            wash = session.query(Wash).get(last_smenaservice.id_wash)
    session.close()
    return wash


def create_otgul(id_user, date_smena, reason_description):
    session = Session()
    otmazka_item = session.query(Otmazki).get([id_user, date_smena])
    if otmazka_item:  # TODO показывать юзеру, что запрос уже существует
        otmazka_item.reason_description = reason_description,
        otmazka_item.approoved = None
    else:
        otmazka_item = Otmazki(
            id_user=id_user,
            date_smena=date_smena,
            reason_description=reason_description
        )
    session.add(otmazka_item)
    session.commit()
    session.close()
    return True


def set_otgul_approove(id_user, date_smena, approoved):
    session = Session()
    otmazka_item = session.query(Otmazki).get([id_user, date_smena])
    if otmazka_item:
        otmazka_item.approoved = approoved
        session.commit()
    session.close()
    return True


def create_dopsmena(id_user: int, date_smena: datetime.date, auto_assigned: bool = False) -> bool:
    session = Session()
    dopsmena_item = session.query(DopSmena).get([id_user, date_smena])
    if dopsmena_item:  # TODO показывать юзеру, что запрос уже существует
        dopsmena_item.approoved = None
    else:
        dopsmena_item = DopSmena(
            id_user=id_user,
            date_smena=date_smena,
            auto_assigned=auto_assigned,
        )
    session.add(dopsmena_item)
    session.commit()
    session.close()
    return True


def set_dopsmena_approove(id_user, date_smena, approoved):
    session = Session()
    dopsmena_item = session.query(DopSmena).get([id_user, date_smena])
    if dopsmena_item:
        dopsmena_item.approoved = approoved
        session.commit()
    session.close()
    return True


def get_dopsmena(id_user: int, date_smena: datetime.date) -> DopSmena:
    """Объект допсмены в БД"""
    session = Session()
    dopsmena_item = session.query(DopSmena).get([id_user, date_smena])
    session.close()
    return dopsmena_item


# TODO не забыть что допсмены и отгулы просто создаются, но пока никак не влияют на график


def get_unapprooved_dopsmenas(id_city):
    session = Session()
    values_tuple = session.query(DopSmena).join(User, User.id == DopSmena.id_user).filter(
        User.id_city == id_city, DopSmena.approoved == None).limit(18).all()  # TODO magic number
    session.close()
    return values_tuple


def get_unapprooved_otguls(id_city):
    session = Session()
    values_tuple = session.query(Otmazki).join(User, User.id == Otmazki.id_user).filter(
        User.id_city == id_city, Otmazki.approoved == None).limit(18).all()  # TODO magic number
    session.close()
    return values_tuple


def get_otgul(id_user: int, date_smena: datetime.date) -> Otmazki:
    """Объект отгула в БД"""
    session = Session()
    otgul_item = session.query(Otmazki).get([id_user, date_smena])
    session.close()
    return otgul_item


def get_car_leftover(id_city: int, id_smena_date: int) -> CarLeftover:
    session = Session()
    value = session.query(CarLeftover).get([id_city, id_smena_date])
    session.close()
    return value


def create_car_leftover(id_city: int, id_smena_date: int, kol_leftover: int, id_brigadir: int) -> bool:
    session = Session()
    car_leftover_item = session.query(CarLeftover).get([id_city, id_smena_date])
    if car_leftover_item:
        session.delete(car_leftover_item)
    car_leftover_item = CarLeftover(
        id_city=id_city,
        id_smena_date=id_smena_date,
        kol_leftover=kol_leftover,
        id_brigadir=id_brigadir
    )
    session.add(car_leftover_item)
    session.commit()
    session.close()
    return True


def check_gosnomer_duplicate(id_user: int, gosnomer: str) -> bool:
    session = Session()
    smena_item = session.query(Smena).filter(Smena.id_user == id_user, Smena.finished == 0).first()
    if smena_item:
        smenaservice_item = session.query(SmenaService).filter(
            SmenaService.id_smena == smena_item.id, SmenaService.gosnomer == gosnomer).first()
    else:
        smenaservice_item = session.query(SmenaService).filter(SmenaService.id_user == id_user, func.DATE(
            SmenaService.date_create) == datetime.date.today(), SmenaService.gosnomer == gosnomer).first()
    session.close()
    if smenaservice_item:
        return True
    return False


def insert_workers_count(workers_count_dict: dict, id_city: int) -> bool:
    session = Session()

    for date_smena, kol in workers_count_dict.items():
        workers_count_item = session.query(WorkersCount).get([date_smena, id_city])
        if workers_count_item:
            workers_count_item.kol = kol
            workers_count_item.date_update = datetime.datetime.now()
        else:
            workers_count_item = WorkersCount(
                date_smena=date_smena,
                id_city=id_city,
                kol=kol
            )
        session.add(workers_count_item)
    session.commit()
    session.close()
    return True


def get_workers_count(date_smena: datetime.date, id_city: int) -> WorkersCount:
    session = Session()
    value = session.query(WorkersCount).get([date_smena, id_city])
    session.close()
    return value
