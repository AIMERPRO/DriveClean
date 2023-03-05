"""Всё что связано с отправкой запросов саппортам"""
import datetime
import logging
import random

from models.model_reqs import (REQS_DOPUSL_PURITY, DopuslTypes, ReqDopusl,
                               ReqKapot, ReqRpn, ReqTpHelp)
from models.model_service import MEDIA_TYPES, Media
from models.model_smena import Smena, Wash
from models.model_users import ROLES, City, User

from db.connection import Session

LOGGER = logging.getLogger('applog')

SUPPORT_RESEND_TIME_MINUTES = 15  # время, через которое запрос будет отправлен другому саппорту в случае неответа


def get_supports_on_smena():
    session = Session()
    values_tuple = session.query(User).join(Smena, Smena.id_user == User.id).filter(
        Smena.finished == 0, User.id_role == ROLES['support'], User.active == 1).all()
    session.close()
    return values_tuple


def get_random_support_on_smena(id_support_preferred: int = None, id_user_exclude: int = None) -> User:
    """
        id_support_preferred: если указано, то он будет возвращаться (при наличии на смене)
    """
    session = Session()
    values_tuple = session.query(User).join(Smena, Smena.id_user == User.id).filter(
        Smena.finished == 0, User.id_role == ROLES['support'], User.active == 1, User.id != id_user_exclude).all()
    session.close()

    users_on_smena_ids = []
    for user_item in values_tuple:
        users_on_smena_ids.append(user_item.id)

    LOGGER.info(f'Lets choose support. preferred {id_support_preferred} exclude {id_user_exclude}')
    if id_support_preferred and id_support_preferred in users_on_smena_ids:
        session = Session()
        user_support_preferred_item = session.query(User).get(id_support_preferred)
        session.close()
        LOGGER.info(f'Preferred support on smena and chosen - {user_support_preferred_item.id}')
        return user_support_preferred_item

    if values_tuple:
        LOGGER.info(f'Support will be chosen from common tuple')
        return random.choice(values_tuple)

    return None


def get_random_support_daily() -> User:
    session = Session()
    values_tuple = session.query(User).filter(User.id_role == ROLES['support_daily'], User.active == 1).all()
    session.close()
    if values_tuple:
        return random.choice(values_tuple)
    return None


def create_empty_tphelp_request(id_user, id_tphelp_type):
    session = Session()
    new_req_tphelp = ReqTpHelp(
        id_user=id_user,
        id_tphelp_type=id_tphelp_type
    )
    session.add(new_req_tphelp)
    session.commit()
    new_id = new_req_tphelp.id
    session.close()
    return new_id


def update_tphelp_request_for_ready(id_req_tphelp, gosnomer, commentary):
    session = Session()
    req_tphelp = session.query(ReqTpHelp).filter(ReqTpHelp.id == id_req_tphelp).first()
    if req_tphelp:
        req_tphelp.gosnomer = gosnomer
        req_tphelp.commentary = commentary
        req_tphelp.ready = 1
        session.commit()
    session.close()
    return True


def get_tphelp_request(id_req_tphelp) -> ReqTpHelp:
    session = Session()
    value = session.query(ReqTpHelp).get(id_req_tphelp)
    session.close()
    return value


def update_tphelp_noreaction_reqs_for_repeat() -> bool:
    session = Session()
    reqs_without_reaction_tuple = session.query(ReqTpHelp).filter(
        ReqTpHelp.sent_to_support == 1,
        ReqTpHelp.processed_by_support == 0,
        ReqTpHelp.sent_to_support_datetime < datetime.datetime.now()-datetime.timedelta(minutes=SUPPORT_RESEND_TIME_MINUTES),
        ReqTpHelp.sent_to_support_datetime > datetime.datetime.now()-datetime.timedelta(days=2)
    ).all()
    for req_tphelp_without_reaction_item in reqs_without_reaction_tuple:
        req_tphelp_without_reaction_item.sent_to_support = 0
        session.add(req_tphelp_without_reaction_item)
        session.commit()
    session.close()
    return True


def get_tphelp_requests_for_support():
    session = Session()
    result_list = []

    expired_sent_reqs_tuple = session.query(ReqTpHelp).filter(
        ReqTpHelp.processed_by_support == 0, ReqTpHelp.date_create < datetime.datetime.now()-datetime.timedelta(hours=12)).all()
    if expired_sent_reqs_tuple:
        for req_item in expired_sent_reqs_tuple:
            req_item.expired = 1
        session.commit()

    reqs_tphelp_tuple = session.query(ReqTpHelp).filter(
        ReqTpHelp.ready == 1, ReqTpHelp.sent_to_support == 0, ReqTpHelp.expired == 0).all()
    for req_tphelp in reqs_tphelp_tuple:
        id_req_tphelp = req_tphelp.id
        id_user = req_tphelp.id_user
        gosnomer = req_tphelp.gosnomer
        commentary = req_tphelp.commentary
        media_tuple = session.query(Media).filter(Media.id_req_tphelp == id_req_tphelp).all()

        user = session.query(User).get(id_user)
        fio = f'{user.fam} {user.im}'

        city = session.query(City).get(user.id_city)
        city_name = city.name

        result_list.append((req_tphelp, fio, city_name, gosnomer, commentary, media_tuple))

    session.close()
    return result_list


def mark_req_tphelp_sent_to_support(id_req_tphelp, id_support):
    """Отметить - запрос отправлен саппорту"""
    session = Session()
    tphelp_item = session.query(ReqTpHelp).get(id_req_tphelp)
    if tphelp_item:
        tphelp_item.sent_to_support = 1
        tphelp_item.sent_to_support_datetime = datetime.datetime.now()
        tphelp_item.id_support = id_support
        session.add(tphelp_item)
        session.commit()
    session.close()
    return True


def set_req_tphelp_response(id_req_tphelp, commentary):
    """Сохранить ответ на запрос от саппорта"""
    session = Session()
    tphelp_item = session.query(ReqTpHelp).get(id_req_tphelp)
    if tphelp_item:
        tphelp_item.sent_to_support = 1
        tphelp_item.processed_by_support = 1
        tphelp_item.processed_by_support_datetime = datetime.datetime.now()
        tphelp_item.commentary_from_support = commentary
        session.add(tphelp_item)
        session.commit()
    session.close()
    return True


def get_req_tphelp_responses_for_workers():
    session = Session()
    values_tuple = session.query(ReqTpHelp).filter(ReqTpHelp.processed_by_support ==
                                                   1, ReqTpHelp.response_sent_to_worker == 0).all()
    session.close()
    return values_tuple


def mark_req_tphelp_response_sent_to_worker(id_req_tphelp):
    """Отметить - ответ отправлен перегонщику"""
    session = Session()
    tphelp_item = session.query(ReqTpHelp).get(id_req_tphelp)
    if tphelp_item:
        tphelp_item.response_sent_to_worker = 1
        tphelp_item.response_sent_to_worker_datetime = datetime.datetime.now()
        session.add(tphelp_item)
        session.commit()
    session.close()
    return True


def create_empty_rpn_request(id_user: int, id_wash: int) -> int:
    session = Session()
    new_req_rpn = ReqRpn(
        id_user=id_user,
        id_wash=id_wash
    )
    session.add(new_req_rpn)
    session.commit()
    new_id = new_req_rpn.id
    session.close()
    return new_id


def update_rpn_request_for_ready(id_req_rpn, gosnomer):
    session = Session()
    req_rpn = session.query(ReqRpn).get(id_req_rpn)
    if req_rpn:
        req_rpn.gosnomer = gosnomer
        req_rpn.ready = 1
        session.commit()
    session.close()
    return True


def get_rpn_request(id_req_rpn) -> ReqRpn:
    session = Session()
    value = session.query(ReqRpn).get(id_req_rpn)
    session.close()
    return value


def get_rpn_requests_for_support():
    session = Session()
    result_list = []

    expired_sent_reqs_tuple = session.query(ReqRpn).filter(
        ReqRpn.processed_by_support == 0, ReqRpn.date_create < datetime.datetime.now()-datetime.timedelta(hours=12)).all()
    if expired_sent_reqs_tuple:
        for req_item in expired_sent_reqs_tuple:
            req_item.expired = 1
        session.commit()

    reqs_rpn_tuple = session.query(ReqRpn).filter(
        ReqRpn.ready == 1, ReqRpn.sent_to_support == 0, ReqRpn.expired == 0).all()
    for req_rpn in reqs_rpn_tuple:
        id_req_rpn = req_rpn.id
        id_user = req_rpn.id_user
        gosnomer = req_rpn.gosnomer
        media_tuple_temperlist = session.query(Media).filter(
            Media.id_req_rpn == id_req_rpn, Media.id_media_type == MEDIA_TYPES['rpn_temperature_list']).all()
        media_tuple_workprocess = session.query(Media).filter(
            Media.id_req_rpn == id_req_rpn, Media.id_media_type == MEDIA_TYPES['rpn_work_process']).all()

        user = session.query(User).get(id_user)
        fio = f'{user.fam} {user.im}'

        wash = session.query(Wash).get(req_rpn.id_wash)
        wash_name = wash.name

        result_list.append((id_req_rpn, fio, wash_name, gosnomer, media_tuple_temperlist, media_tuple_workprocess))

    session.close()
    return result_list


def mark_req_rpn_sent_to_support(id_req_rpn, id_support):
    session = Session()
    rpn_item = session.query(ReqRpn).get(id_req_rpn)
    if rpn_item:
        rpn_item.sent_to_support = 1
        rpn_item.sent_to_support_datetime = datetime.datetime.now()
        rpn_item.id_support = id_support
        session.add(rpn_item)
        session.commit()
    session.close()
    return True


def set_req_rpn_response(id_req_rpn, decision, id_refuse_reason, custom_refuse_reason):
    session = Session()
    rpn_item = session.query(ReqRpn).get(id_req_rpn)
    if rpn_item:
        rpn_item.sent_to_support = 1
        rpn_item.processed_by_support = 1
        rpn_item.processed_by_support_datetime = datetime.datetime.now()
        rpn_item.decision = decision
        rpn_item.id_refuse_reason = id_refuse_reason
        rpn_item.custom_refuse_reason = custom_refuse_reason
        session.add(rpn_item)
        session.commit()
    session.close()
    return True


def get_req_rpn_responses_for_workers():
    session = Session()
    values_tuple = session.query(ReqRpn).filter(ReqRpn.processed_by_support ==
                                                1, ReqRpn.response_sent_to_worker == 0).all()
    session.close()
    return values_tuple


def mark_req_rpn_response_sent_to_worker(id_req_rpn):
    session = Session()
    rpn_item = session.query(ReqRpn).get(id_req_rpn)
    if rpn_item:
        rpn_item.response_sent_to_worker = 1
        rpn_item.response_sent_to_worker_datetime = datetime.datetime.now()
        session.add(rpn_item)
        session.commit()
    session.close()
    return True


def create_empty_kapot_request(id_user, id_wash, gosnomer):
    session = Session()
    new_req_kapot = ReqKapot(
        id_user=id_user,
        id_wash=id_wash,
        gosnomer=gosnomer
    )
    session.add(new_req_kapot)
    session.commit()
    new_id = new_req_kapot.id
    session.close()
    return new_id


def update_kapot_request_for_ready(id_req_kapot):
    session = Session()
    req_kapot = session.query(ReqKapot).get(id_req_kapot)
    if req_kapot:
        req_kapot.ready = 1
        session.commit()
    session.close()
    return True


def get_kapot_request(id_req_kapot) -> ReqKapot:
    session = Session()
    value = session.query(ReqKapot).get(id_req_kapot)
    session.close()
    return value


def update_kapot_noreaction_reqs_for_repeat() -> bool:
    session = Session()
    reqs_without_reaction_tuple = session.query(ReqKapot).filter(
        ReqKapot.sent_to_support == 1,
        ReqKapot.processed_by_support == 0,
        ReqKapot.sent_to_support_datetime < datetime.datetime.now()-datetime.timedelta(minutes=SUPPORT_RESEND_TIME_MINUTES),
        ReqKapot.sent_to_support_datetime > datetime.datetime.now()-datetime.timedelta(days=2)
    ).all()
    for req_kapot_without_reaction_item in reqs_without_reaction_tuple:
        req_kapot_without_reaction_item.sent_to_support = 0
        session.add(req_kapot_without_reaction_item)
        session.commit()
    session.close()
    return True


def get_kapot_requests_for_support():
    session = Session()
    result_list = []

    expired_sent_reqs_tuple = session.query(ReqKapot).filter(
        ReqKapot.processed_by_support == 0, ReqKapot.date_create < datetime.datetime.now()-datetime.timedelta(hours=12)).all()
    if expired_sent_reqs_tuple:
        for req_item in expired_sent_reqs_tuple:
            req_item.expired = 1
        session.commit()

    reqs_kapot_tuple = session.query(ReqKapot).filter(
        ReqKapot.ready == 1, ReqKapot.sent_to_support == 0, ReqKapot.expired == 0).all()
    for req_kapot in reqs_kapot_tuple:
        id_req_kapot = req_kapot.id
        id_user = req_kapot.id_user
        gosnomer = req_kapot.gosnomer
        media_tuple = session.query(Media).filter(Media.id_req_kapot == id_req_kapot).all()

        user = session.query(User).get(id_user)
        fio = f'{user.fam} {user.im}'

        wash = session.query(Wash).get(req_kapot.id_wash)
        wash_name = wash.name

        result_list.append((req_kapot, fio, wash_name, gosnomer, media_tuple))

    session.close()
    return result_list


def mark_req_kapot_sent_to_support(id_req_kapot, id_support):
    session = Session()
    kapot_item = session.query(ReqKapot).get(id_req_kapot)
    if kapot_item:
        kapot_item.sent_to_support = 1
        kapot_item.sent_to_support_datetime = datetime.datetime.now()
        kapot_item.id_support = id_support
        session.add(kapot_item)
        session.commit()
    session.close()
    return True


def set_req_kapot_response(id_req_kapot, decision, id_refuse_reason, custom_refuse_reason):
    session = Session()
    kapot_item = session.query(ReqKapot).get(id_req_kapot)
    if kapot_item:
        kapot_item.sent_to_support = 1
        kapot_item.processed_by_support = 1
        kapot_item.processed_by_support_datetime = datetime.datetime.now()
        kapot_item.decision = decision
        kapot_item.id_refuse_reason = id_refuse_reason
        kapot_item.custom_refuse_reason = custom_refuse_reason
        session.add(kapot_item)
        session.commit()
    session.close()
    return True


def get_req_kapot_responses_for_workers():
    session = Session()
    values_tuple = session.query(ReqKapot).filter(ReqKapot.processed_by_support ==
                                                  1, ReqKapot.response_sent_to_worker == 0).all()
    session.close()
    return values_tuple


def mark_req_kapot_response_sent_to_worker(id_req_kapot):
    session = Session()
    kapot_item = session.query(ReqKapot).get(id_req_kapot)
    if kapot_item:
        kapot_item.response_sent_to_worker = 1
        kapot_item.response_sent_to_worker_datetime = datetime.datetime.now()
        session.add(kapot_item)
        session.commit()
    session.close()
    return True


def create_empty_dopusl_request(id_user, id_req_dirty, id_purity, id_wash, gosnomer, id_dopusl_type, kol_elem):
    session = Session()
    new_req_dopusl = ReqDopusl(
        id_user=id_user,
        id_req_dirty=id_req_dirty,
        id_purity=id_purity,
        id_wash=id_wash,
        gosnomer=gosnomer,
        id_dopusl_type=id_dopusl_type,
        kol_elem=kol_elem
    )
    session.add(new_req_dopusl)
    session.commit()
    new_id = new_req_dopusl.id
    session.close()
    return new_id


def update_dopusl_request_for_ready(id_req_dopusl):
    session = Session()
    req_dopusl = session.query(ReqDopusl).get(id_req_dopusl)
    if req_dopusl:
        req_dopusl.ready = 1
        session.commit()
    session.close()
    return True


def get_dopusl_request(id_req_dopusl) -> ReqDopusl:
    session = Session()
    value = session.query(ReqDopusl).get(id_req_dopusl)
    session.close()
    return value


def update_dopusl_noreaction_reqs_for_repeat() -> bool:
    session = Session()
    reqs_without_reaction_tuple = session.query(ReqDopusl).filter(
        ReqDopusl.sent_to_support == 1,
        ReqDopusl.processed_by_support == 0,
        ReqDopusl.sent_to_support_datetime < datetime.datetime.now()-datetime.timedelta(minutes=SUPPORT_RESEND_TIME_MINUTES),
        ReqDopusl.sent_to_support_datetime > datetime.datetime.now()-datetime.timedelta(days=2)
    ).all()
    for req_dopusl_without_reaction_item in reqs_without_reaction_tuple:
        req_dopusl_without_reaction_item.sent_to_support = 0
        session.add(req_dopusl_without_reaction_item)
        session.commit()
    session.close()
    return True


def get_dopusl_requests_for_support():
    session = Session()
    result_list = []

    expired_sent_reqs_tuple = session.query(ReqDopusl).filter(
        ReqDopusl.processed_by_support == 0, ReqDopusl.date_create < datetime.datetime.now()-datetime.timedelta(hours=12)).all()
    if expired_sent_reqs_tuple:
        for req_item in expired_sent_reqs_tuple:
            req_item.expired = 1
        session.commit()

    reqs_dopusl_tuple = session.query(ReqDopusl).filter(
        ReqDopusl.ready == 1, ReqDopusl.sent_to_support == 0, ReqDopusl.expired == 0).all()
    for req_dopusl in reqs_dopusl_tuple:
        req_dopusl_dirty = None
        id_req_dopusl = req_dopusl.id
        id_user = req_dopusl.id_user
        media_tuple = session.query(Media).filter(Media.id_req_dopusl == id_req_dopusl).all()
        media_tuple_additional_dirty = session.query(Media).filter(
            Media.id_req_dopusl == req_dopusl.id_req_dirty).all() if req_dopusl.id_purity == REQS_DOPUSL_PURITY['clean'] else None

        user = session.query(User).get(id_user)
        fio = f'{user.fam} {user.im}'

        city = session.query(City).get(user.id_city)
        city_name = city.name

        wash = session.query(Wash).get(req_dopusl.id_wash)
        wash_name = wash.name

        dopusl_type_item = session.query(DopuslTypes).get(req_dopusl.id_dopusl_type)
        dopusl_type_name = dopusl_type_item.name

        if req_dopusl.id_purity == REQS_DOPUSL_PURITY['clean']:
            req_dopusl_dirty = session.query(ReqDopusl).get(req_dopusl.id_req_dirty)

        result_list.append((req_dopusl, req_dopusl_dirty, fio, city_name, wash_name, dopusl_type_name,
                           media_tuple, media_tuple_additional_dirty))

    session.close()
    return result_list


def mark_req_dopusl_sent_to_support(id_req_dopusl, id_support):
    session = Session()
    dopusl_item = session.query(ReqDopusl).get(id_req_dopusl)
    if dopusl_item:
        dopusl_item.sent_to_support = 1
        dopusl_item.sent_to_support_datetime = datetime.datetime.now()
        dopusl_item.id_support = id_support
        session.add(dopusl_item)
        session.commit()
    session.close()
    return True


def set_req_dopusl_response(id_req_dopusl, decision, id_refuse_reason, custom_refuse_reason):
    session = Session()
    dopusl_item = session.query(ReqDopusl).get(id_req_dopusl)
    if dopusl_item:
        # sent_to_support = 1 это нужно на случай, если услуга уже помечена как "без реакции", но первоначальный саппорт внезапно ответил на неё
        dopusl_item.sent_to_support = 1
        dopusl_item.processed_by_support = 1
        dopusl_item.processed_by_support_datetime = datetime.datetime.now()
        dopusl_item.decision = decision
        dopusl_item.id_refuse_reason = id_refuse_reason
        dopusl_item.custom_refuse_reason = custom_refuse_reason
        session.add(dopusl_item)
        session.commit()
    session.close()
    return True


def get_req_dopusl_responses_for_workers():
    session = Session()
    values_tuple = session.query(ReqDopusl).filter(ReqDopusl.processed_by_support ==
                                                   1, ReqDopusl.response_sent_to_worker == 0).all()
    session.close()
    return values_tuple


def mark_req_dopusl_response_sent_to_worker(id_req_dopusl):
    session = Session()
    dopusl_item = session.query(ReqDopusl).get(id_req_dopusl)
    if dopusl_item:
        dopusl_item.response_sent_to_worker = 1
        dopusl_item.response_sent_to_worker_datetime = datetime.datetime.now()
        session.add(dopusl_item)
        session.commit()
    session.close()
    return True
