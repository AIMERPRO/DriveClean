"""Состояние пользователей в меню"""
import logging
from enum import Enum

import db

LOGGER = logging.getLogger('applog')


def get_cur_state(id_user: int) -> str:
    """Возвращает текущую стадию"""
    state = db.states.get_cur_state(id_user)
    if not state:
        state = States.S_START.value
    return state


def set_state(id_user: int, state: str) -> bool:
    """Сохраняет стадию, на которую переходит пользователь"""
    db.states.set_state(id_user, state)
    LOGGER.info("user %s come to %s (%s)", id_user, States(state).name, state)
    return True


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
    S_REG_PENDING = '0.99'

    S_MAINMENU = '1'

    S_MENU_KARATEL_WASHCHECK_WASH_ASK = '1.40.2.1'
    S_MENU_KARATEL_WASHCHECK_GOSNOMER_ASK = '1.40.2.2'
    S_MENU_KARATEL_WASHCHECK_ELEMENTS_ASK = '1.40.2.3'

    S_MENU_KARATEL_OUTCHECK_GOSNOMER_ASK = '1.40.3.1'
    S_MENU_KARATEL_OUTCHECK_ELEMENTS_ASK = '1.40.3.2'
    S_MENU_KARATEL_OUTCHECK_PHOTOELEMENTS_ASK = '1.40.3.3'
