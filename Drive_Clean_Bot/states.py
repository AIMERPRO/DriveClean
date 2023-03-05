"""Состояние пользователей в меню"""
import logging
from enum import Enum

import db

LOGGER = logging.getLogger('applog')


def get_cur_state(id_user):
    """Возвращает текущую стадию
    Args:
        id_user (int): id пользователя;
    Returns:
        str: текущая стадия
    """
    state = db.db_states.get_cur_state(id_user)
    if not state:
        state = States.S_START.value
    return state


def set_state(id_user, state):
    """Сохраняет стадию на которую переходит пользователь
    Args:
        id_user (int): id пользователя;
        state (str): стадия (значение по ключу из класса States);
    """
    db.db_states.set_state(id_user, state)
    LOGGER.info("user %s come to %s (%s)", id_user, States(state).name, state)


class States(Enum):
    """
        Стадии меню юзеров.
        Стадии регистрации начинаются на "0"
        Стадия главного меню всегда "1"
        Стадии после главного меню обозначаются как:
            1 цифра - всегда "1"
            2 цифра - роль юзера
            3 цифра - тематический подраздел
            4 цифра - шаг в этом подразделе
            цифры далее - пункты добавленные позднее
    """
    S_START = '0'

    S_REG = '0.1'
    S_REG_ASK_CITY = '0.2'
    S_REG_ASK_FAM = '0.3'
    S_REG_ASK_IM = '0.4'
    S_REG_ASK_OT = '0.5'
    S_REG_ASK_DATAR = '0.6'
    S_REG_ASK_PHONE = '0.7'
    S_REG_PENDING = '0.99'

    S_MAINMENU = '1'

    S_MENU_ADMIN_USERSMANAGE = '1.10.1.1'

    S_MENU_ADMIN_USERSMANAGE_FIRE_FAM_ASK = '1.10.1.2.1'
    S_MENU_ADMIN_USERSMANAGE_FIRE_ACCEPT_ASK = '1.10.1.2.2'

    S_MENU_SUPPORT_MARK_PENALTY_CITY_ASK = '1.12.1.1'
    S_MENU_SUPPORT_MARK_PENALTY_GOSNOMER_ASK = '1.12.1.2'
    S_MENU_SUPPORT_MARK_PENALTY_SMENASERVICE_CHECK = '1.12.1.3'
    S_MENU_SUPPORT_MARK_PENALTY_USER_CHECK = '1.12.1.4'
    S_MENU_SUPPORT_MARK_PENALTY_CATEGORY_ASK = '1.12.1.5'
    S_MENU_SUPPORT_MARK_PENALTY_TYPE_ASK = '1.12.1.6'

    S_MENU_SUPPORT_CHECK_TPHELP_ID_REQ = '1.12.2.1'
    S_MENU_SUPPORT_CHECK_TPHELP_COMMENTARY_ASK = '1.12.2.2'

    S_MENU_SUPPORT_CHECK_RPN_ID_REQ = '1.12.3.1'
    S_MENU_SUPPORT_CHECK_RPN_DECISION = '1.12.3.2'
    S_MENU_SUPPORT_CHECK_RPN_REFUSE_REASON_ASK = '1.12.3.3'
    S_MENU_SUPPORT_CHECK_RPN_COMMENTARY_ASK = '1.12.3.4'

    S_MENU_SUPPORT_CHECK_KAPOT_ID_REQ = '1.12.4.1'
    S_MENU_SUPPORT_CHECK_KAPOT_DECISION = '1.12.4.2'
    S_MENU_SUPPORT_CHECK_KAPOT_REFUSE_REASON_ASK = '1.12.4.3'
    S_MENU_SUPPORT_CHECK_KAPOT_COMMENTARY_ASK = '1.12.4.4'

    S_MENU_SUPPORT_CHECK_DOPUSL_ID_REQ = '1.12.5.1'
    S_MENU_SUPPORT_CHECK_DOPUSL_DECISION = '1.12.5.2'
    S_MENU_SUPPORT_CHECK_DOPUSL_REFUSE_REASON_ASK = '1.12.5.3'
    S_MENU_SUPPORT_CHECK_DOPUSL_COMMENTARY_ASK = '1.12.5.4'

    S_MENU_SUPPORT_SMENAEND_CONFIRM_ASK = '1.12.6.1'

    S_MENU_BRIGADIR_CAR_LEFTOVER_KOL_ASK = '1.20.1.1'

    S_MENU_WORKER_DAILY = '1.30.1.1'

    S_MENU_WORKER_SMENASERVICE_DISTRICT_ASK = '1.30.2.1'
    S_MENU_WORKER_SMENASERVICE_WASH_ASK = '1.30.2.2'
    S_MENU_WORKER_SMENASERVICE_CARSHARING_ASK = '1.30.2.3'
    S_MENU_WORKER_SMENASERVICE_GOSNOMER_ASK = '1.30.2.4'
    S_MENU_WORKER_SMENASERVICE_DISPATCH_PHOTOSTATUS_ASK = '1.30.2.5'
    S_MENU_WORKER_SMENASERVICE_AUTOCLASS_ASK = '1.30.2.6'
    S_MENU_WORKER_SMENASERVICE_AUTOSR_ASK = '1.30.2.7'
    S_MENU_WORKER_SMENASERVICE_WASHUSL_TYPE_ASK = '1.30.2.8'
    S_MENU_WORKER_SMENASERVICE_OMYV_ASK = '1.30.2.9'
    S_MENU_WORKER_SMENASERVICE_OMYV_KOL_ASK = '1.30.2.10'
    S_MENU_WORKER_SMENASERVICE_KAPOT_VIDEO_ASK = '1.30.2.11'
    S_MENU_WORKER_SMENASERVICE_ACCEPT_ASK = '1.30.2.12'
    S_MENU_WORKER_SMENASERVICE_DIRTY_PHOTO_ASK = '1.30.2.13'
    S_MENU_WORKER_SMENASERVICE_CLEAN_PHOTO_ASK = '1.30.2.14'

    S_MENU_WORKER_SMENAEND_EARLY_ASK = '1.30.3.1'
    S_MENU_WORKER_SMENAEND_EARLY_CUSTOM = '1.30.3.2'
    S_MENU_WORKER_SMENAEND_EARLY_FEWCARS_PHOTO_ASK = '1.30.3.3'
    S_MENU_WORKER_SMENAEND_CARLIST_APPROOVE_ASK = '1.30.3.4'
    S_MENU_WORKER_SMENAEND_LAST_PARKED_CAR_PHOTO_ASK = '1.30.3.5'
    S_MENU_WORKER_SMENAEND_LEFTOVERS_PHOTO_ASK = '1.30.3.6'
    S_MENU_WORKER_SMENAEND_LEFTOVERS_KOL_ASK = '1.30.3.7'
    S_MENU_WORKER_SMENAEND_SCREENSHOT_EXAMPLE_PHOTO_ASK = '1.30.3.8'

    S_MENU_WORKER_SCHED = '1.30.4.1'

    S_MENU_WORKER_TPHELP_TYPE_ASK = '1.30.5.1'
    S_MENU_WORKER_TPHELP_REQ_CHECK = '1.30.5.1.1'

    S_MENU_WORKER_TPHELP_FORGOTTENSTUFF_PHOTO_ASK = '1.30.5.2.1'
    S_MENU_WORKER_TPHELP_FORGOTTENSTUFF_PLACE_ASK = '1.30.5.2.2'
    S_MENU_WORKER_TPHELP_FORGOTTENSTUFF_GOSNOMER_ASK = '1.30.5.2.3'

    S_MENU_WORKER_TPHELP_CARSTATUS_PHOTO_ASK = '1.30.5.3.1'
    S_MENU_WORKER_TPHELP_CARSTATUS_GOSNOMER_ASK = '1.30.5.3.2'
    S_MENU_WORKER_TPHELP_CARSTATUS_COMMENTARY_ASK = '1.30.5.3.3'
    S_MENU_WORKER_TPHELP_CARSTATUS_WHEEL_ASK = '1.30.5.3.4'

    S_MENU_WORKER_TPHELP_APPHELP_PHOTO_ASK = '1.30.5.4.1'
    S_MENU_WORKER_TPHELP_APPHELP_GOSNOMER_ASK = '1.30.5.4.2'
    S_MENU_WORKER_TPHELP_APPHELP_COMMENTARY_ASK = '1.30.5.4.3'

    S_MENU_WORKER_TPHELP_RESTRICTEDAREA_PHOTO_ASK = '1.30.5.5.1'
    S_MENU_WORKER_TPHELP_RESTRICTEDAREA_GOSNOMER_ASK = '1.30.5.5.2'

    S_MENU_WORKER_RPN_DISTRICT_ASK = '1.30.6.1'
    S_MENU_WORKER_RPN_WASH_ASK = '1.30.6.2'
    S_MENU_WORKER_RPN_REQ_ID = '1.30.6.3'
    S_MENU_WORKER_RPN_TEMPERATURELIST_PHOTO_ASK = '1.30.6.4'
    S_MENU_WORKER_RPN_GOSNOMER_ASK = '1.30.6.5'
    S_MENU_WORKER_RPN_WORKPROCESS_PHOTO_ASK = '1.30.6.6'

    S_MENU_WORKER_REQ_KAPOT_DISTRICT_ASK = '1.30.7.1'
    S_MENU_WORKER_REQ_KAPOT_WASH_ASK = '1.30.7.2'
    S_MENU_WORKER_REQ_KAPOT_GOSNOMER_ASK = '1.30.7.3'
    S_MENU_WORKER_REQ_KAPOT_CREATE = '1.30.7.4'
    S_MENU_WORKER_REQ_KAPOT_VIDEO_ASK = '1.30.7.5'

    S_MENU_WORKER_DOPSMENA_SMENADATE_ASK = '1.30.8.1'

    S_MENU_WORKER_OTGUL_SMENADATE_ASK = '1.30.9.1'
    S_MENU_WORKER_OTGUL_DESCRIPTION_ASK = '1.30.9.2'

    S_MENU_WORKER_REQ_DOPUSL_DISTRICT_ASK = '1.30.10.1'
    S_MENU_WORKER_REQ_DOPUSL_WASH_ASK = '1.30.10.2'
    S_MENU_WORKER_REQ_DOPUSL_GOSNOMER_ASK = '1.30.10.3'
    S_MENU_WORKER_REQ_DOPUSL_TYPE_ASK = '1.30.10.4'
    S_MENU_WORKER_REQ_DOPUSL_ELEMKOL_ASK = '1.30.10.5'
    S_MENU_WORKER_REQ_DOPUSL_CREATE_DIRTY = '1.30.10.6'
    S_MENU_WORKER_REQ_DOPUSL_DIRTY_SERVICEAPP_PHOTO_ASK = '1.30.10.65'
    S_MENU_WORKER_REQ_DOPUSL_DIRTY_PHOTO_ASK = '1.30.10.7'
    S_MENU_WORKER_REQ_DOPUSL_CREATE_CLEAN = '1.30.10.8'
    S_MENU_WORKER_REQ_DOPUSL_CLEAN_PHOTO_ASK = '1.30.10.9'

    S_MENU_ACTUALIZE_PERSONAL_DATA_PHONE_OPL_SERVICE_ASK = '1.30.11.1'
    S_MENU_ACTUALIZE_PERSONAL_DATA_EMAIL_ASK = '1.30.11.2'

    S_MENU_WORKER_ASSIGNSMENA_NEXTDAY_ASK = '1.30.12.1'
    S_MENU_WORKER_ASSIGNSMENA_NEXTDAY_CUSTOM_ASK = '1.30.12.2'
