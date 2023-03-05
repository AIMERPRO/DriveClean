#!venv/bin/python

"""Main module"""

import calendar
import datetime
import logging
import logging.handlers as loghandlers
import os
import re
import sys
import threading
import time

import telebot
from dateutil.relativedelta import relativedelta
from telebot import types, util
from telebot.types import Message, InputMediaPhoto

import config
import db
import spreadsheets
import states
from Drive_Clean_Bot.db.db_karatel import get_karatel_not_sent_washcheck, \
    get_karatel_washchecks_checklist_by_id_washcheck, get_karatel_balls_from_element_by_id, \
    get_karatel_not_sent_outcheck, get_karatel_outcheck_checklist_by_id_outcheck, \
    get_karatel_outcheck_get_photos_by_id_outcheck, set_karatel_outcheck_sent, set_karatel_washcheck_sent
from models.model_reqs import (REQS_DOPUSL_PURITY, REQS_DOPUSL_REFUSE_REASONS,
                               REQS_DOPUSL_TYPES, REQS_KAPOT_REFUSE_REASONS,
                               REQS_RPN_REFUSE_REASONS, TP_HELP_TYPES,
                               DopuslRefuseReason, DopuslTypes,
                               ReqKapotRefuseReason, ReqRpnRefuseReason,
                               TpHelpTypes)
from models.model_service import MEDIA_TYPES, WEEKDAYS_NUMBERS, WEEKDAYS_WHEN
from models.model_smena import (AUTO_CLASSES, AUTO_SR_TYPES, CARSHARINGS,
                                EARLY_SMENA_END_REASONS, WASH_USL_TYPES,
                                AutoClass, AutoSrType, Carsharing,
                                EarlySmenaEndReason, WashUslType)
from models.model_spreadsheets import SPREADSHEET_TYPES
from models.model_users import CITIES, REG_RESULTS, ROLES, City, Role, User
from models.model_workprocess import LeftoverCarsKol, PenaltyCategory
from states import States as st

BOT = telebot.TeleBot(config.TOKEN)

NIGHT_SMENA_START = (21, 0)
NIGHT_SMENA_END = (9, 59)

# в этот период запросы на услуги будут отсылаться ночным саппортам (в остальное время - дневным)
# немного отличается от обычного периода ночной смены
NIGHT_SMENA_SUPPORTCHECK_START = (21, 30)
NIGHT_SMENA_SUPPORTCHECK_END = (9, 29)

if not os.path.exists('tmp'):
    os.makedirs('tmp')
if not os.path.exists('logs'):
    os.makedirs('logs')
LOGGER = logging.getLogger('applog')
LOGGER.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s  %(filename)s  %(funcName)s  %(lineno)d  %(name)s  %(levelname)s: %(message)s')
log_handler = loghandlers.RotatingFileHandler(
    './logs/botlog.log',
    maxBytes=1000000,
    encoding='utf-8',
    backupCount=50
)
log_handler.setLevel(logging.INFO)
log_handler.setFormatter(formatter)
LOGGER.addHandler(log_handler)
telebot.logger.setLevel(logging.INFO)
telebot.logger.addHandler(LOGGER)


@BOT.message_handler(func=lambda message: message.text == 'Отмена')
def cancel_to_mainmenu(message):
    """При команде Отмена из любого места (кроме запрещённых для отмены) возвращает в главное меню"""
    states_with_forbid_cancel_lst = [
        st.S_MENU_WORKER_ASSIGNSMENA_NEXTDAY_ASK.value,
        st.S_MENU_WORKER_ASSIGNSMENA_NEXTDAY_CUSTOM_ASK.value,
    ]
    if states.get_cur_state(message.chat.id) in states_with_forbid_cancel_lst:
        return
    cmd_start(message)


@BOT.message_handler(commands=['cmd_smenastart_f4gh375'])
def cmd_smenastart_f4gh375(message):
    send_smena_start_notify()


@BOT.message_handler(commands=['cmd_major_smenaresults_c4d08cd'])
def cmd_major_smenaresults_c4d08cd(message):
    show_chatreport_major_smenaresults()


@BOT.message_handler(commands=['cmd_major_today_workers_kol_26b022c'])
def cmd_major_today_workers_kol_26b022c(message):
    show_chatreport_major_today_workers_kol()


# TODO временно
@BOT.message_handler(commands=['cmd_refresh_contrag_parse_rif48g8'])
def cmd_refresh_contrag_data_rif48g8(message):
    spreadsheets.parse_contragents_list_sheet()


# TODO временно


@BOT.message_handler(commands=['cmd_refresh_contrag_sheet_rif48g8'])
def cmd_refresh_contrag_sheet_rif48g8(message):
    spreadsheets.update_contragents_opl_reestr_sheet()


@BOT.message_handler(commands=['cmd_tst_updshedsheets_rif48g8'])
def cmd_tst_updshedsheets_rif48g8(message):
    db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['schedules'], 1)
    db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['schedules'], 2)
    db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['brig_schedules'], None)


@BOT.callback_query_handler(func=lambda call: True)
def inline_buttons_router(call):
    """Роутер для инлайновых кнопок"""
    if call.message:
        key = call.data.split(';')[0]
        is_del_inline_keyb = True

        if key == 'menu_admin_usersmanage_approove_user':
            menu_admin_usersmanage_approove_user(call.message, call.data)
        elif key == 'menu_admin_usersmanage_user_district':
            menu_admin_usersmanage_user_district(call.message, call.data)
        elif key == 'menu_admin_usersmanage_brigdistricts_append':
            menu_admin_usersmanage_brigdistricts_append(call.message, call.data)
        elif key == 'menu_admin_usersmanage_fire_confirm_ask':
            menu_admin_usersmanage_fire_confirm_ask(call.message, call.data)
        elif call.data.split(";")[0] == 'weekschedule_asking':
            weekschedule_asking(call.message, call.data)
        elif call.data.split(";")[0] == 'smena_start':
            smena_start(call.message, call.data)
        elif call.data.split(";")[0] == 'menu_support_check_tphelp':
            menu_support_check_tphelp(call.message, call.data)
        elif call.data.split(";")[0] == 'menu_support_check_rpn':
            menu_support_check_rpn(call.message, call.data)
        elif call.data.split(";")[0] == 'menu_support_check_kapot':
            menu_support_check_kapot(call.message, call.data)
        elif call.data.split(";")[0] == 'menu_support_check_dopusl':
            menu_support_check_dopusl(call.message, call.data)
        elif call.data.split(";")[0] == 'menu_worker_dopusl_clean_photo_ask':
            menu_worker_dopusl_clean_photo_ask(call.message, call.data)
        elif call.data.split(";")[0] == 'menu_brigadir_dopsmena_approove':
            menu_brigadir_workers_requests_dopsmena_approove(call.message, call.data)
        elif call.data.split(";")[0] == 'menu_brigadir_otgul_approove':
            menu_brigadir_workers_requests_otgul_approove(call.message, call.data)
        elif call.data.split(";")[0] == 'menu_brigadir_newsched_approove':
            menu_brigadir_workers_requests_newched_approove(call.message, call.data)
        elif call.data.split(";")[0] == 'menu_lk_actualize_email':
            lk_actualize_email_ask(call.message, call.data)

        if is_del_inline_keyb:
            BOT.edit_message_reply_markup(chat_id=call.message.chat.id,
                                          message_id=call.message.id, reply_markup=types.InlineKeyboardMarkup())


@BOT.message_handler(content_types=['photo'])
def photo_router(message):
    """Роутер для сообщений с фото"""
    if states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENAEND_EARLY_FEWCARS_PHOTO_ASK.value:
        menu_worker_smena_close_early_fewcars_photo_save(message)
    elif states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENAEND_LAST_PARKED_CAR_PHOTO_ASK.value:
        menu_worker_smena_close_last_parked_car_photo_save(message)
    elif states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENAEND_LEFTOVERS_PHOTO_ASK.value:
        menu_worker_smena_close_leftovers_photo_save(message)
    elif states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENAEND_SCREENSHOT_EXAMPLE_PHOTO_ASK.value:
        menu_worker_smena_close_screenshot_example_photo_save(message)
    elif states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_TPHELP_FORGOTTENSTUFF_PHOTO_ASK.value:
        menu_worker_tphelp_forgottenstuff_photo_save(message)
    elif states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_TPHELP_CARSTATUS_PHOTO_ASK.value:
        menu_worker_tphelp_carstatus_photo_save(message)
    elif states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_TPHELP_APPHELP_PHOTO_ASK.value:
        menu_worker_tphelp_apphelp_photo_save(message)
    elif states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_TPHELP_RESTRICTEDAREA_PHOTO_ASK.value:
        menu_worker_tphelp_restricted_area_photo_save(message)
    elif states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_RPN_TEMPERATURELIST_PHOTO_ASK.value:
        menu_worker_rpn_temperaturelist_photo_save(message)
    elif states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_RPN_WORKPROCESS_PHOTO_ASK.value:
        menu_worker_rpn_workprocess_photo_save(message)
    elif states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_REQ_DOPUSL_DIRTY_SERVICEAPP_PHOTO_ASK.value:
        menu_worker_dopusl_dirty_serviceapp_photo_save(message)
    elif states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_REQ_DOPUSL_DIRTY_PHOTO_ASK.value:
        menu_worker_dopusl_dirty_photo_save(message)
    elif states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_REQ_DOPUSL_CLEAN_PHOTO_ASK.value:
        menu_worker_dopusl_clean_photo_save(message)
    elif states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENASERVICE_DIRTY_PHOTO_ASK.value:
        menu_worker_dirty_photo_save(message)
    elif states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENASERVICE_CLEAN_PHOTO_ASK.value:
        menu_worker_clean_photo_save(message)


@BOT.message_handler(content_types=['video'])
def video_router(message):
    """Роутер для сообщений с видео"""
    if states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_REQ_KAPOT_VIDEO_ASK.value:
        menu_worker_kapot_video_save(message)
    elif states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENASERVICE_KAPOT_VIDEO_ASK.value:
        menu_worker_smenaservice_kapot_video_save(message)


@BOT.message_handler(commands=['start'])
def cmd_start(message):
    """Старт диалога с ботом"""
    if message.chat.id < 0:  # если вдруг диалог начат из стороннего чата
        return
    user = db.db_users.get_user(message.chat.id)
    if user:  # как то фигурирует в БД
        if not user.reg and user.active:  # прошёл регистрацию, но ещё не подтверждён
            menu_reg_pending(message)
        elif user.reg and not user.active:  # уволен (или отменена админом регистрация), может пройти регистрацию заново
            menu_reg(message)
        elif user.reg and user.active:  # зарегистрирован, подтверждён
            mainmenu(message)
    else:  # вообще нету в БД
        menu_reg(message)


def menu_reg(message):
    """Начало регистрации"""
    db.db_tempvals.clear_user_tempvals(message.chat.id)
    BOT.send_message(message.chat.id, 'Добро пожаловать в бот! Приступим к регистрации.')
    menu_reg_city_ask(message)


def menu_reg_city_ask(message):
    keyboard = make_keyboard(row_width=2, fill_with_classifier=City)
    mes = 'Выберите ваш город'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_REG_ASK_CITY.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_REG_ASK_CITY.value)
def menu_reg_city_save(message):
    choice = message.text
    city = db.db_classifiers.find_classifier_object(City, name=choice)
    if not city:
        BOT.send_message(message.chat.id, 'Нет такого города')
        return
    db.db_tempvals.set_tmpval(message.chat.id, st.S_REG_ASK_CITY.name, intval=city.id)
    menu_reg_fam_ask(message)


def menu_reg_fam_ask(message):
    keyboard = make_keyboard()
    mes = 'Напишите вашу фамилию?'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_REG_ASK_FAM.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_REG_ASK_FAM.value)
def menu_reg_fam_save(message):
    fam = message.text
    if len(fam) > 100:
        BOT.send_message(message.chat.id, 'Слишком длинная фамилия')
        return
    if not fam.replace(' ', '').isalpha():
        BOT.send_message(message.chat.id, 'Недопустимые символы в фамилии')
        return
    db.db_tempvals.set_tmpval(message.chat.id, st.S_REG_ASK_FAM.name, textval=fam)
    menu_reg_im_ask(message)


def menu_reg_im_ask(message):
    keyboard = make_keyboard()
    mes = 'Напишите ваше имя'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_REG_ASK_IM.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_REG_ASK_IM.value)
def menu_reg_im_save(message):
    im = message.text
    if len(im) > 100:
        BOT.send_message(message.chat.id, 'Слишком длинное имя')
        return
    if not im.replace(' ', '').isalpha():
        BOT.send_message(message.chat.id, 'Недопустимые символы в имени')
        return
    db.db_tempvals.set_tmpval(message.chat.id, st.S_REG_ASK_IM.name, textval=im)
    menu_reg_ot_ask(message)


def menu_reg_ot_ask(message):
    keyboard = make_keyboard()
    mes = 'Напишите ваше отчество'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_REG_ASK_OT.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_REG_ASK_OT.value)
def menu_reg_ot_save(message):
    ot = message.text
    if len(ot) > 100:
        BOT.send_message(message.chat.id, 'Слишком длинное отчество')
        return
    if not ot.replace(' ', '').isalpha():
        BOT.send_message(message.chat.id, 'Недопустимые символы в отчестве')
        return
    db.db_tempvals.set_tmpval(message.chat.id, st.S_REG_ASK_OT.name, textval=ot)
    menu_reg_datar_ask(message)


def menu_reg_datar_ask(message):
    keyboard = make_keyboard()
    mes = 'Укажите вашу дату рождения в виде 15.01.1990'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_REG_ASK_DATAR.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_REG_ASK_DATAR.value)
def menu_reg_datar_save(message):
    try:
        date_r = datetime.datetime.strptime(message.text, '%d.%m.%Y')
        cur_date = datetime.datetime.now()
        if date_r > cur_date:
            raise ValueError
    except ValueError:
        BOT.send_message(message.chat.id, 'Неправильно указана дата!')
        return
    datar = message.text
    db.db_tempvals.set_tmpval(message.chat.id, st.S_REG_ASK_DATAR.name, textval=datar)
    menu_reg_phone_ask(message)


def menu_reg_phone_ask(message):
    keyboard = make_keyboard()
    mes = 'Укажите ваш номер телефона в виде +79991232233'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_REG_ASK_PHONE.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_REG_ASK_PHONE.value)
def menu_reg_phone_save(message):
    phone = message.text.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '')
    if len(phone) > 20:
        BOT.send_message(message.chat.id, 'Слишком длинный номер')
        return
    if not str.isdigit(phone):
        BOT.send_message(message.chat.id, 'Неправильно указан номер телефона')
        return

    phone_str_lst = list(phone)
    if phone_str_lst[0] == '8':
        phone_str_lst[0] = '7'
    phone = "".join(phone_str_lst)

    db.db_tempvals.set_tmpval(message.chat.id, st.S_REG_ASK_PHONE.name, textval=phone)
    menu_reg_save(message)


# TODO запрос email


def menu_reg_save(message):
    """Сохранение регистрации"""
    id_user = message.chat.id
    id_city = db.db_tempvals.get_tmpval(id_user, st.S_REG_ASK_CITY.name).intval
    fam = db.db_tempvals.get_tmpval(id_user, st.S_REG_ASK_FAM.name).textval
    im = db.db_tempvals.get_tmpval(id_user, st.S_REG_ASK_IM.name).textval
    ot = db.db_tempvals.get_tmpval(id_user, st.S_REG_ASK_OT.name).textval
    nick = message.chat.username
    phone = db.db_tempvals.get_tmpval(id_user, st.S_REG_ASK_PHONE.name).textval
    datar = db.db_tempvals.get_tmpval(id_user, st.S_REG_ASK_DATAR.name).textval
    datar = datetime.datetime.strptime(datar, '%d.%m.%Y').date()

    city = db.db_classifiers.find_classifier_object(City, id=id_city)

    if db.db_users.add_new_user(id_user, id_city, fam, im, ot, nick, datar, phone):
        BOT.send_message(message.chat.id, 'Регистрация прошла успешно')

        admins_tuple = db.db_users.get_admins()
        for admin in admins_tuple:
            try:
                BOT.send_message(admin.id, f'{fam} {im} ({city.name}) желает зарегистрироваться')
            except Exception as ex_blk:
                LOGGER.error(ex_blk)

        states.set_state(message.chat.id, st.S_REG_PENDING.value)
        menu_reg_pending(message)
    else:
        BOT.send_message(message.chat.id, 'Ошибка регистрации')


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_REG_PENDING.value)
def menu_reg_pending(message):
    user = db.db_users.get_user(message.chat.id)
    if user and user.id_role != ROLES['pending']:
        cmd_start(message)
    else:
        keyb_items = ['Обновить']
        keyboard = make_keyboard(items=keyb_items, is_with_cancel=False)
        mes = 'Ожидайте подтверждения регистрации. Обычно она занимает 15 минут.\nДля проверки статуса нажмите кнопку Обновить'
        BOT.send_message(message.chat.id, mes, reply_markup=keyboard)


def is_head_sup(sup_id: int) -> bool:
    """Является ли юзер главным саппортом"""
    head_sup_id = db.db_prefs.get_pref('id_head_support').intval
    return sup_id == head_sup_id


def mainmenu(message):
    """Главное меню"""
    db.db_tempvals.clear_user_tempvals(message.chat.id)
    user = db.db_users.get_user(message.chat.id)
    keyb_items = []
    row_width = 1

    if not user.phone_opl_service:
        actualize_personal_data(message)
        return

    if user.id_role == ROLES['admin']:
        if is_head_sup(user.id):
            keyb_items.append('Утвердить графики ТП')
        keyb_items.append('Управление пользователями')
        keyb_items.append('Отчёты')
        row_width = 2

    elif user.id_role == ROLES['support']:
        if db.db_smena.is_user_on_smena(user.id):
            keyb_items.append('Отметить ошибку')
            keyb_items.append('Завершить смену')
        else:
            keyb_items.append('Отметить ошибку')
            keyb_items.append('Мой график')
            # keyb_items.append('Доп.смена')
            # keyb_items.append('Отгул')
        row_width = 2

    elif user.id_role == ROLES['support_daily'] or user.id_role == ROLES['support_penaltier']:
        keyb_items.append('Отметить ошибку')

    elif user.id_role == ROLES['brigadir']:
        if db.db_smena.is_user_on_smena(user.id):
            keyb_items.append('Выполнил услугу')
            keyb_items.append('Согласование доп. услуги')
            # TODO не забыть, что пункты меню, связанные с запросами саппорту, дублируются в обработчике дневных смен menu_worker_daily()
            keyb_items.append('Отчёт Rapid капот')
            if user.id_city == CITIES['moscow']:
                keyb_items.append('Отчёт РПН')
            keyb_items.append('Обращение в Support')
            keyb_items.append('Отчётность работников')
            keyb_items.append('Моя отчётность')
            keyb_items.append('График выходов')
            keyb_items.append('Запросы от работников')
            keyb_items.append('Ввести остатки авто')
            keyb_items.append('Завершить смену')
        else:
            keyb_items.append('Дневной перегон')
            keyb_items.append('Мой график')
            keyb_items.append('Отчётность работников')
            keyb_items.append('Моя отчётность')
            keyb_items.append('График выходов')
            keyb_items.append('Запросы от работников')
            keyb_items.append('Ввести остатки авто')
            keyb_items.append('Доп.смена')
            keyb_items.append('Отгул')
        keyb_items.append('Личный кабинет')
        row_width = 2

    elif user.id_role == ROLES['karatel']:
        keyb_items.append('Личный кабинет')

    elif user.id_role == ROLES['teacher']:
        keyb_items.append('Личный кабинет')

    elif user.id_role == ROLES['worker']:
        if db.db_smena.is_user_on_smena(user.id):
            keyb_items.append('Выполнил услугу')
            keyb_items.append('Согласование доп. услуги')
            keyb_items.append('Отчёт Rapid капот')
            if user.id_city == CITIES['moscow']:
                keyb_items.append('Отчёт РПН')
            keyb_items.append('Обращение в Support')
            keyb_items.append('Моя отчётность')
            keyb_items.append('Завершить смену')
        else:
            keyb_items.append('Дневной перегон')
            keyb_items.append('Доп.смена')
            keyb_items.append('Мой график')
            keyb_items.append('Моя отчётность')
            keyb_items.append('Отгул')
        keyb_items.append('Личный кабинет')
        row_width = 2

    elif user.id_role == ROLES['specprojects']:
        keyb_items.append('Личный кабинет')

    keyboard = make_keyboard(items=keyb_items, row_width=row_width, is_with_cancel=False)
    mes = 'Вы в главном меню'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MAINMENU.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_MAINMENU.value)
def mainmenu_choice(message):
    """Обработка нажатия в главном меню"""
    choice = message.text
    user = db.db_users.get_user(message.chat.id)

    if user.id_role == ROLES['admin']:
        if choice == 'Утвердить графики ТП' and is_head_sup(user.id):
            menu_brigadir_workers_requests_newched(message)
        if choice == 'Управление пользователями':
            menu_admin_usersmanage(message)
        elif choice == 'Отчёты':
            menu_admin_showlinks_reports(message)
        elif choice == '/cmd_fda77e8e323a_update_resources':
            cmd_update_resources(message)
        else:
            mainmenu(message)

    elif user.id_role == ROLES['support']:
        if db.db_smena.is_user_on_smena(user.id):
            if choice == 'Отметить ошибку':
                menu_support_mark_penalty(message)
            elif choice == 'Завершить смену':
                menu_support_smena_close(message)
            else:
                mainmenu(message)
        else:
            if choice == 'Отметить ошибку':
                menu_support_mark_penalty(message)
            elif choice == 'Мой график':
                menu_worker_myschedule_ask(message)
            else:
                mainmenu(message)

    elif user.id_role == ROLES['support_daily'] or user.id_role == ROLES['support_penaltier']:
        if choice == 'Отметить ошибку':
            menu_support_mark_penalty(message)
        else:
            mainmenu(message)

    elif user.id_role == ROLES['brigadir']:
        if db.db_smena.is_user_on_smena(user.id):
            if choice == 'Выполнил услугу':
                menu_worker_smenaservice_new(message)
            elif choice == 'Согласование доп. услуги':
                menu_worker_dopusl_new(message)
            elif choice == 'Отчёт Rapid капот':
                menu_worker_kapot_new(message)
            elif choice == 'Отчёт РПН' and user.id_city == CITIES['moscow']:
                menu_worker_rpn_new(message)
            elif choice == 'Обращение в Support':
                menu_worker_tphelp_new(message)
            elif choice == 'Отчётность работников':
                menu_brigadir_chatreports_workers(message)
            elif choice == 'График выходов':
                menu_brigadir_show_sched_table(message)
            elif choice == 'Моя отчётность':
                menu_worker_chatreports_mine(message)
            elif choice == 'Запросы от работников':
                menu_brigadir_workers_requests(message)
            elif choice == 'Ввести остатки авто':
                menu_brigadir_car_leftovers_new(message)
            elif choice == 'Завершить смену':
                menu_worker_smena_close(message)
            elif choice == 'Личный кабинет':
                menu_lk(message)
            else:
                mainmenu(message)
        else:
            if choice == 'Дневной перегон':
                menu_worker_daily(message)
            elif choice == 'Мой график':
                menu_worker_myschedule_ask(message)
            elif choice == 'Доп.смена':
                menu_worker_dopsmena_new(message)
            elif choice == 'Отгул':
                menu_worker_otgul_new(message)
            elif choice == 'График перегонщиков':
                BOT.send_message(message.chat.id, 'В разработке...')  # TODO В разработке
            elif choice == 'Отчётность работников':
                menu_brigadir_chatreports_workers(message)
            elif choice == 'График выходов':
                menu_brigadir_show_sched_table(message)
            elif choice == 'Моя отчётность':
                menu_worker_chatreports_mine(message)
            elif choice == 'Запросы от работников':
                menu_brigadir_workers_requests(message)
            elif choice == 'Ввести остатки авто':
                menu_brigadir_car_leftovers_new(message)
            elif choice == 'Личный кабинет':
                menu_lk(message)
            else:
                mainmenu(message)

    elif user.id_role == ROLES['karatel']:
        if choice == 'Личный кабинет':
            menu_lk(message)
        else:
            mainmenu(message)

    elif user.id_role == ROLES['teacher']:
        if choice == 'Личный кабинет':
            menu_lk(message)
        else:
            mainmenu(message)

    elif user.id_role == ROLES['worker']:
        if db.db_smena.is_user_on_smena(user.id):
            if choice == 'Выполнил услугу':
                menu_worker_smenaservice_new(message)
            elif choice == 'Согласование доп. услуги':
                menu_worker_dopusl_new(message)
            elif choice == 'Отчёт Rapid капот':
                menu_worker_kapot_new(message)
            elif choice == 'Отчёт РПН' and user.id_city == CITIES['moscow']:
                menu_worker_rpn_new(message)
            elif choice == 'Обращение в Support':
                menu_worker_tphelp_new(message)
            elif choice == 'Моя отчётность':
                menu_worker_chatreports_mine(message)
            elif choice == 'Завершить смену':
                menu_worker_smena_close(message)
            elif choice == 'Личный кабинет':
                menu_lk(message)
            else:
                mainmenu(message)
        else:
            if choice == 'Дневной перегон':
                menu_worker_daily(message)
            elif choice == 'Мой график':
                menu_worker_myschedule_ask(message)
            elif choice == 'Доп.смена':
                menu_worker_dopsmena_new(message)
            elif choice == 'Отгул':
                menu_worker_otgul_new(message)
            elif choice == 'Моя отчётность':
                menu_worker_chatreports_mine(message)
            elif choice == 'Личный кабинет':
                menu_lk(message)
            else:
                mainmenu(message)

    elif user.id_role == ROLES['specprojects']:
        if choice == 'Личный кабинет':
            menu_lk(message)
        else:
            mainmenu(message)


def actualize_personal_data(message):
    BOT.send_message(message.chat.id, 'Необходима актуализация персональных данных')
    actualize_personal_data_phone_opl_service_ask(message)


def actualize_personal_data_phone_opl_service_ask(message):
    keyboard = make_keyboard(is_with_cancel=False)
    mes = 'Укажите ваш номер телефона в сервисе для получения выплаты Konsol, в виде +79991232233'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_ACTUALIZE_PERSONAL_DATA_PHONE_OPL_SERVICE_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(
    message.chat.id) == st.S_MENU_ACTUALIZE_PERSONAL_DATA_PHONE_OPL_SERVICE_ASK.value)
def actualize_personal_data_phone_opl_service_save(message):
    phone_opl_service = message.text.replace(' ', '').replace(
        '-', '').replace('(', '').replace(')', '').replace('+', '')
    if len(phone_opl_service) > 20:
        BOT.send_message(message.chat.id, 'Слишком длинный номер')
        return
    if not str.isdigit(phone_opl_service):
        BOT.send_message(message.chat.id, 'Неправильно указан номер телефона')
        return

    phone_str_lst = list(phone_opl_service)
    if phone_str_lst[0] == '8':
        phone_str_lst[0] = '7'
    phone_opl_service = "".join(phone_str_lst)

    if db.db_users.update_phone_opl_service(message.chat.id, phone_opl_service):
        BOT.send_message(message.chat.id, 'Данные обновлены')
    else:
        BOT.send_message(message.chat.id, 'Ошибка записи в базу')
    mainmenu(message)


def menu_admin_usersmanage(message):
    keyb_items = []
    row_width = 2

    keyb_items.append('Запросы на регистрацию')
    keyb_items.append('Уволить работника')
    keyb_items.append('Районы бригадиров')

    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    mes = 'Выберите действие'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_ADMIN_USERSMANAGE.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_ADMIN_USERSMANAGE.value)
def menu_admin_usersmanage_choice(message):
    choice = message.text
    if choice == 'Запросы на регистрацию':
        menu_admin_usersmanage_approove(message)
    elif choice == 'Уволить работника':
        menu_admin_usersmanage_fire(message)
    elif choice == 'Районы бригадиров':
        menu_admin_usersmanage_brigdistricts(message)


def menu_admin_usersmanage_approove(message):
    unapprooved_users_tuple = db.db_users.get_unapprooved_users()
    users_without_district_tuple = db.db_users.get_users_without_district()
    if not unapprooved_users_tuple and not users_without_district_tuple:
        BOT.send_message(message.chat.id, 'Нет незарегистрированных пользователей')

    for user in unapprooved_users_tuple:
        keyboard_inline = types.InlineKeyboardMarkup()
        keyboard_list = []
        city = db.db_classifiers.find_classifier_object(City, id=user.id_city)
        roles = db.db_users.get_reg_roles()
        for role in roles:
            keyboard_list.append(types.InlineKeyboardButton(
                text=role.name, callback_data=f'menu_admin_usersmanage_approove_user;{user.id};{role.id}'))
        keyboard_list.append(types.InlineKeyboardButton(text='Удалить регистрацию',
                                                        callback_data=f'menu_admin_usersmanage_approove_user;{user.id};0'))

        keyboard_inline.add(*keyboard_list, row_width=2)
        BOT.send_message(
            message.chat.id, f'{user.fam} {user.im} ({city.name}) - какую роль назначить?',
            reply_markup=keyboard_inline)

    # TODO как то здесь проверять, вдруг кто два раза себе запросит кнопки, и сначала нажмёт одно, а в другом сообщении другое

    for user in users_without_district_tuple:
        keyboard_inline = types.InlineKeyboardMarkup()
        keyboard_list = []
        districts_tuple = db.db_users.get_districts_by_city(user.id_city)
        city = db.db_classifiers.find_classifier_object(City, id=user.id_city)
        for district_item in districts_tuple:
            keyboard_list.append(types.InlineKeyboardButton(
                text=district_item.district,
                callback_data=f'menu_admin_usersmanage_user_district;{user.id};{district_item.district}'))
        keyboard_inline.add(*keyboard_list, row_width=4)
        BOT.send_message(
            message.chat.id, f'Какой район назначить работнику {user.fam} {user.im} ({city.name})?',
            reply_markup=keyboard_inline)

    mainmenu(message)


def menu_admin_usersmanage_approove_user(message, data):
    """Простановка роли юзеру"""
    params = data.split(';')
    id_user_new = int(params[1])
    id_role_new = int(params[2])

    reg_result = db.db_users.set_reg(id_user_new, id_role_new)

    if reg_result:
        new_user = db.db_users.get_user(id_user_new)
        new_role = db.db_classifiers.find_classifier_object(Role, id=new_user.id_role)
        if reg_result == REG_RESULTS['already_reg']:
            BOT.send_message(
                message.chat.id,
                f'Другой администратор уже проставил роль пользователю {new_user.fam} {new_user.im} ({new_role.name})')
        elif reg_result == REG_RESULTS['success']:
            if id_role_new == 0:
                BOT.send_message(message.chat.id, f'Отменена регистрация у пользователя {new_user.fam} {new_user.im}')
                try:
                    BOT.send_message(id_user_new, 'Ваша регистрация была отменена')
                except Exception as ex_blk:
                    LOGGER.error(ex_blk)
            else:

                BOT.send_message(
                    message.chat.id,
                    f'Роль для пользователя {new_user.fam} {new_user.im} проставлена ({new_role.name})')
                if new_role.id not in (ROLES['admin'], ROLES['specprojects'], ROLES['support'],
                                       ROLES['support_daily'], ['support_penaltier']):
                    districts_tuple = db.db_users.get_districts_by_city(new_user.id_city)
                    if len(districts_tuple) == 1:
                        db.db_users.set_district(id_user_new, districts_tuple[0].district)
                        BOT.send_message(
                            message.chat.id,
                            f'Пользователю {new_user.fam} {new_user.im} назначен район {districts_tuple[0].district}')
                    else:
                        keyboard_inline = types.InlineKeyboardMarkup()
                        keyboard_list = []
                        city = db.db_classifiers.find_classifier_object(City, id=new_user.id_city)
                        for district_item in districts_tuple:
                            keyboard_list.append(types.InlineKeyboardButton(
                                text=district_item.district,
                                callback_data=f'menu_admin_usersmanage_user_district;{new_user.id};{district_item.district}'))
                        keyboard_inline.add(*keyboard_list, row_width=4)
                        BOT.send_message(
                            message.chat.id,
                            f'Какой район назначить работнику {new_user.fam} {new_user.im} ({city.name})?',
                            reply_markup=keyboard_inline)

                try:
                    BOT.send_message(
                        new_user.id,
                        f'Регистрация подтверждена, ваша роль - {new_role.name}. Нажмите кнопку Обновить для перехода в главное меню')
                    if id_role_new in (ROLES['worker'], ROLES['brigadir'], ROLES['support']):
                        BOT.send_message(
                            id_user_new, '\n\nНапоминаем о необходимости выбрать себе рабочий график в меню бота')
                    db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['schedules'], new_user.id_city)
                    db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['brig_schedules'], None)
                except Exception as ex_blk:
                    LOGGER.error(ex_blk)
    else:
        BOT.send_message(message.chat.id, 'Ошибка простановки роли')


def menu_admin_usersmanage_user_district(message, data):
    """Простановка района юзеру"""
    params = data.split(';')
    id_user_new = int(params[1])
    district_new = int(params[2])

    new_user = db.db_users.get_user(id_user_new)
    if db.db_users.set_district(id_user_new, district_new):
        BOT.send_message(message.chat.id, f'Пользователю {new_user.fam} {new_user.im} назначен район {district_new}')
        new_user = db.db_users.get_user(id_user_new)
        mes_user = f'Вы назначены на район {new_user.district}\n\n'
        brigadirs_tuple = db.db_users.get_district_brigadirs(new_user.id_city, new_user.district)
        if brigadirs_tuple:
            mes_brig = f'На ваш район ({new_user.district}) назначен работник:\n{new_user.fam} {new_user.im} {new_user.ot}, +{new_user.phone}'
            for brigadir_item in brigadirs_tuple:
                try:
                    BOT.send_message(brigadir_item.id, mes_brig)
                except Exception as ex_blk:
                    LOGGER.error(ex_blk)

            mes_user += 'Бригадир: ' if len(brigadirs_tuple) == 1 else 'Бригадиры:\n'
            for brigadir_item in brigadirs_tuple:
                mes_user += f'{brigadir_item.fam} {brigadir_item.im} {brigadir_item.ot}, +{brigadir_item.phone}\n'

        try:
            BOT.send_message(new_user.id, mes_user)
        except Exception as ex_blk:
            LOGGER.error(ex_blk)

    else:
        BOT.send_message(message.chat.id, 'Ошибка записи района в базу')


def menu_admin_usersmanage_fire(message):
    menu_admin_usersmanage_fire_fam_ask(message)


def menu_admin_usersmanage_fire_fam_ask(message):
    keyboard = make_keyboard()

    BOT.send_message(message.chat.id, 'Введите для поиска фамилию исполнителя, которого нужно удалить',
                     reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_ADMIN_USERSMANAGE_FIRE_FAM_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_ADMIN_USERSMANAGE_FIRE_FAM_ASK.value)
def menu_admin_usersmanage_fire_fam_search(message):
    fam = message.text
    if len(fam) > 100:
        BOT.send_message(message.chat.id, 'Слишком длинная фамилия')
        return
    if len(fam) < 3:
        BOT.send_message(message.chat.id, 'Слишком короткая фамилия')
        return
    if not fam.replace(' ', '').isalpha():
        BOT.send_message(message.chat.id, 'Недопустимые символы в фамилии')
        return

    users_tuple = db.db_users.search_users_by_fio_part(fam, message.chat.id)
    if users_tuple:
        keyboard_inline = types.InlineKeyboardMarkup()
        keyboard_list = []
        for user in users_tuple:
            keyboard_list.append(types.InlineKeyboardButton(
                text=f'{user.fam} {user.im} ({user.phone})',
                callback_data=f'menu_admin_usersmanage_fire_confirm_ask;{user.id}'))
        keyboard_inline.add(*keyboard_list, row_width=1)
        BOT.send_message(message.chat.id, 'Выберите работника из найденных', reply_markup=keyboard_inline)
    else:
        BOT.send_message(message.chat.id, 'Не найден работник с похожей фамилией')


def menu_admin_usersmanage_fire_confirm_ask(message, data):
    params = data.split(';')
    id_user_fire = int(params[1])
    user = db.db_users.get_user(id_user_fire)
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_ADMIN_USERSMANAGE_FIRE_FAM_ASK.name, intval=id_user_fire)

    keyb_items = []
    keyb_items.append('Да')
    keyb_items.append('Да (без уведомления)')
    keyboard = make_keyboard(items=keyb_items, row_width=2)
    mes = f'Уволить работника {user.fam} {user.im} ({user.phone})?'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_ADMIN_USERSMANAGE_FIRE_ACCEPT_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_ADMIN_USERSMANAGE_FIRE_ACCEPT_ASK.value)
def menu_admin_usersmanage_fire_confirm_save(message):
    choice = message.text
    if choice in ('Да', 'Да (без уведомления)'):
        id_user_fire = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_ADMIN_USERSMANAGE_FIRE_FAM_ASK.name).intval
        user = db.db_users.get_user(id_user_fire)
        if db.db_users.fire_user(id_user_fire):
            BOT.send_message(message.chat.id, 'Работник уволен')
            if choice == 'Да':
                try:
                    BOT.send_message(id_user_fire, 'Вы уволены. Регистрация отменена')
                except Exception as ex_blk:
                    LOGGER.error(ex_blk)
            db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['schedules'], user.id_city)
            db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['brig_schedules'], None)
            mainmenu(message)
        else:
            BOT.send_message(message.chat.id, 'Ошибка увольнения работника')


def menu_admin_usersmanage_brigdistricts(message):
    city_items = db.db_classifiers.get_classifier_items(City)
    for city in city_items:
        city_brigs_tuple = db.db_users.get_city_brigadirs(city.id)
        if not city_brigs_tuple:
            BOT.send_message(message.chat.id, f'В городе {city.name} нету бригадиров!')
        else:
            districts_tuple = db.db_users.get_districts_by_city(city.id)
            for district_item in districts_tuple:
                district_brigadirs_tuple = db.db_users.get_district_brigadirs(city.id, district_item.district)
                if not district_brigadirs_tuple:
                    keyboard_inline = types.InlineKeyboardMarkup()
                    keyboard_list = []
                    for brigadir_item in city_brigs_tuple:
                        keyboard_list.append(types.InlineKeyboardButton(
                            text=f'{brigadir_item.fam} {brigadir_item.im}',
                            callback_data=f'menu_admin_usersmanage_brigdistricts_append;{brigadir_item.id};{city.id};{district_item.district}'))
                    keyboard_inline.add(*keyboard_list, row_width=1)
                    BOT.send_message(
                        message.chat.id,
                        f'В городе {city.name} у района {district_item.district} не назначен бригадир.\nКого назначить на этот район?',
                        reply_markup=keyboard_inline)  # TODO тут можно выйти за лимиты кол-ва сообщений в секунду (20)

    mainmenu(message)


def menu_admin_usersmanage_brigdistricts_append(message, data):
    """Простановка бригадира на район"""
    params = data.split(';')
    id_brigadir = int(params[1])
    id_city = int(params[2])
    district = int(params[3])

    user = db.db_users.get_user(id_brigadir)
    city = db.db_classifiers.find_classifier_object(City, id=id_city)

    if db.db_users.append_brigadir_to_district(id_brigadir, id_city, district):
        BOT.send_message(message.chat.id, f'Бригадир {user.fam} {user.im} поставлен на район {district} ({city.name})')
    else:
        BOT.send_message(message.chat.id, 'Ошибка назначения бригадира')


def menu_admin_showlinks_reports(message):
    city_items = db.db_classifiers.get_classifier_items(City)
    mes = ''
    for city in city_items:
        mes += f'{city.icon} <b>{city.name}</b>\n'

        sh_item_sched = db.db_spreadsheets.get_spreadsheet(city.id, SPREADSHEET_TYPES['schedules'])
        if not sh_item_sched:
            continue
        hyperlink = f'https://docs.google.com/spreadsheets/d/{sh_item_sched.id_drive}/edit#gid=1'
        mes += f'график выходов: {hyperlink}\n'
        mes += '\n'

        brigs_city_tuple = db.db_users.get_city_brigadirs(city.id)
        for brig_item in brigs_city_tuple:
            sh_brig_sched = db.db_spreadsheets.get_spreadsheet(
                None, SPREADSHEET_TYPES['brig_schedules'], id_user=brig_item.id)
            if sh_brig_sched:
                hyperlink = f'https://docs.google.com/spreadsheets/d/{sh_brig_sched.id_drive}/edit#gid=1'
                mes += f'график выходов (бригадир {brig_item.fam} {brig_item.im}): {hyperlink}\n'
                mes += '\n'

        sh_item_smena_results = db.db_spreadsheets.get_spreadsheet(city.id, SPREADSHEET_TYPES['smena_results'])
        if not sh_item_smena_results:
            continue
        hyperlink = f'https://docs.google.com/spreadsheets/d/{sh_item_smena_results.id_drive}/edit#gid=1'
        mes += f'отчёт по сменам: {hyperlink}\n'  # TODO имена из SPREADSHEET_TYPES_CAPTIONS
        mes += '\n'

    sh_item_auto_avg = db.db_spreadsheets.get_spreadsheet(None, SPREADSHEET_TYPES['auto_avg_kol_by_category'])
    if sh_item_auto_avg:
        mes += '\n'
        mes += '<b>Работники и мойки</b>\n'
        hyperlink = f'https://docs.google.com/spreadsheets/d/{sh_item_auto_avg.id_drive}/edit#gid=1'
        mes += f'среднее кол-во авто: {hyperlink}\n'
        mes += '\n'

    sh_item_support = db.db_spreadsheets.get_spreadsheet(None, SPREADSHEET_TYPES['supports'])
    if sh_item_support:
        mes += '\n'
        mes += '<b>Саппорты</b>\n'
        hyperlink = f'https://docs.google.com/spreadsheets/d/{sh_item_support.id_drive}/edit#gid=1'
        mes += f'отчёт по саппортам: {hyperlink}\n'
        mes += '\n'

    mes += '\n'
    mes += '<b>Реестр выплат - самозанятые</b>\n'
    prev_month_str, curr_month_str = get_prev_and_curr_month_dates()
    workers_reestr_prev_month_sheet_item = db.db_spreadsheets.get_spreadsheet(id_city=None,
                                                                              id_type=SPREADSHEET_TYPES[
                                                                                  'payment_registry'],
                                                                              period=prev_month_str)
    workers_reestr_curr_month_sheet_item = db.db_spreadsheets.get_spreadsheet(id_city=None,
                                                                              id_type=SPREADSHEET_TYPES[
                                                                                  'payment_registry'],
                                                                              period=curr_month_str)
    if workers_reestr_prev_month_sheet_item:
        hyperlink = f'https://docs.google.com/spreadsheets/d/{workers_reestr_prev_month_sheet_item.id_drive}/edit#gid=1'
        mes += f'{prev_month_str}: {hyperlink}\n'
    if workers_reestr_curr_month_sheet_item:
        hyperlink = f'https://docs.google.com/spreadsheets/d/{workers_reestr_curr_month_sheet_item.id_drive}/edit#gid=1'
        mes += f'{curr_month_str}: {hyperlink}\n'
    mes += '\n'

    service_chats_tuple = db.db_reports.get_all_service_chats()
    if service_chats_tuple:
        mes += '\n'
        mes += '<b>Группы и каналы</b>\n'
        for service_chat_item in service_chats_tuple:
            if service_chat_item.hyperlink:
                if service_chat_item.name == 'major':
                    mes += f'Major Group: {service_chat_item.hyperlink}\n'
                # TODO автоматом чтоли заполнять, или правильнее вручную контролировать, какие группы показывать

    BOT.send_message(message.chat.id, mes, parse_mode='html', disable_web_page_preview=True)


def menu_brigadir_chatreports_workers(message):
    my_districts_tuple = db.db_users.get_my_responsible_districts(message.chat.id)
    if not my_districts_tuple:
        BOT.send_message(message.chat.id, 'Вы не назначены на район')
        return

    show_chatreport_workers_myworkers(message.chat.id)
    for brig_on_district_item in my_districts_tuple:  # TODO нужно ли каждый район в отдельном сообщении
        id_city = brig_on_district_item.id_city
        district = brig_on_district_item.district
        show_chatreport_workers_whohowmuch(message.chat.id, id_city, district)
        show_chatreport_workers_appearance(message.chat.id, id_city, district)


def show_chatreport_workers_myworkers(id_brigadir):
    mes = f'<b>Отчёт \"Мои подчинённые\"</b>\n\n'
    report_items = db.db_reports.get_myworkerslist_chatreport(id_brigadir)
    if report_items:
        row_number = 1
        for report_item in report_items:
            fio, phone, week_template = report_item
            mes += f'{row_number}. {fio} +{phone}\n'
            if week_template:
                mes += f'рабочие дни: {sched_week_template_to_words(week_template)}'
            else:
                mes += 'нет графика'
            mes += '\n'
            row_number += 1
    else:
        mes += 'нет подчинённых'

    splitted_mes = util.smart_split(mes, chars_per_string=4096)
    for mes_part in splitted_mes:
        BOT.send_message(id_brigadir, mes_part, parse_mode='html')


def show_chatreport_workers_whohowmuch(id_brigadir, id_city, district):
    """Кто сколько"""
    last_smenadate_item = db.db_smena.get_last_smenadate()
    mes = f'<b>Отчёт \"Кто сколько\" по смене {last_smenadate_item.date_smena.strftime("%d.%m.%Y")} (район {district})</b>\n\n'
    report_items = db.db_reports.get_whohowmuch_chatreport(id_city, district, last_smenadate_item.id)
    if report_items:
        for report_item in report_items:
            fio = report_item[0]
            kol = report_item[1]
            mes += f'{fio}: {kol}\n'
    report_items_without_district = db.db_reports.get_whohowmuch_chatreport(id_city, 0, last_smenadate_item.id)
    if report_items_without_district:
        mes += '\n'
        mes += 'По работникам с неназначенным районом:\n'
        for report_item in report_items_without_district:
            fio = report_item[0]
            kol = report_item[1]
            mes += f'{fio}: {kol}\n'
    if not report_items and not report_items_without_district:
        mes += 'Нет выполненных автомобилей на этом районе'

    splitted_mes = util.smart_split(mes, chars_per_string=4096)
    for mes_part in splitted_mes:
        BOT.send_message(id_brigadir, mes_part, parse_mode='html')


def show_chatreport_workers_appearance(id_brigadir, id_city, district):
    """Кто вышел/не вышел на смену"""
    last_smenadate_item = db.db_smena.get_last_smenadate()
    mes = f'<b>Отчёт \"Выходы на смену\" по смене {last_smenadate_item.date_smena.strftime("%d.%m.%Y")} (район {district})</b>\n\n'
    report_items = db.db_reports.get_appearance_chatreport(id_city, district, last_smenadate_item.id)
    if report_items:
        for report_item in report_items:
            fio = report_item[0]
            icon = '✅' if int(report_item[1]) == 1 else '❌'
            response_text = report_item[2]
            mes += f'{icon} {fio}: {response_text}\n'
    report_items_without_district = db.db_reports.get_appearance_chatreport(id_city, 0, last_smenadate_item.id)
    if report_items_without_district:
        mes += '\n'
        mes += 'По работникам с неназначенным районом:\n'
        for report_item in report_items_without_district:
            fio = report_item[0]
            icon = '✅' if int(report_item[1]) == 1 else '❌'
            response_text = report_item[2]
            mes += f'{icon} {fio}: {response_text}\n'
    if not report_items and not report_items_without_district:
        mes += 'Нет выполненных автомобилей на этом районе'

    splitted_mes = util.smart_split(mes, chars_per_string=4096)
    for mes_part in splitted_mes:
        BOT.send_message(id_brigadir, mes_part, parse_mode='html')


def menu_brigadir_show_sched_table(message):
    user = db.db_users.get_user(message.chat.id)
    sh_brig_sched = db.db_spreadsheets.get_spreadsheet(
        None, SPREADSHEET_TYPES['brig_schedules'], id_user=message.chat.id)
    if sh_brig_sched:
        hyperlink = f'https://docs.google.com/spreadsheets/d/{sh_brig_sched.id_drive}/edit#gid=1'
        mes = f'График выходов подчинённых (бригадир {user.fam} {user.im}): {hyperlink}\n'
    else:
        mes = 'Отчётная таблица ещё не создана'

    BOT.send_message(message.chat.id, mes, parse_mode='html', disable_web_page_preview=True)


def menu_worker_chatreports_mine(message: types.Message):
    show_chatreport_mine_periods_results(message.chat.id)
    show_chatreport_mine_last_smena_results(message.chat.id)
    show_chatreport_mine_brigadirs(message.chat.id)


def show_chatreport_mine_periods_results(id_user: int):
    date_start, date_end = get_period_dates()

    # TODO максимально тупо и непродуктивно, но этот код я пишу в 00:05 ночи
    # нам нужно взять прошлый период, но если тупо отминусовать 11 дней (среднюю длину периода), то в конце февраля будет не очень
    # поэтому тупо отнимаем от "текущей" даты по одному дню, пока метод не выдаст даты, отличные от дат текущего периода (то есть, это будут даты прошлого периода)
    tmp_date = datetime.date.today()
    prev_date_start = date_start
    prev_date_end = date_end
    for _ in range(12):  # чтобы не использовать опасный while, 11 шагов уж точно хватит для перескока на прошлый период
        prev_date_start, prev_date_end = get_period_dates(tmp_date)
        if prev_date_start != date_start:
            break
        tmp_date = tmp_date - datetime.timedelta(days=1)

    mes_prev_period = f'<b>Мои результаты за прошлый период ({prev_date_start.strftime("%d.%m.%Y")}-{prev_date_end.strftime("%d.%m.%Y")})</b>\n\n'
    report_items = db.db_reports.get_chatreport_mine_period_results(id_user, prev_date_start, prev_date_end)
    kol_night, kol_day = report_items
    mes_prev_period += f'Дневных авто: {kol_day}\n'
    mes_prev_period += f'Ночных авто: {kol_night}'

    date_start, date_end = get_period_dates()
    mes_cur_period = f'<b>Мои результаты за текущий период ({date_start.strftime("%d.%m.%Y")}-{date_end.strftime("%d.%m.%Y")})</b>\n\n'
    report_items = db.db_reports.get_chatreport_mine_period_results(id_user, date_start, date_end)
    kol_night, kol_day = report_items
    mes_cur_period += f'Дневных авто: {kol_day}\n'
    mes_cur_period += f'Ночных авто: {kol_night}'

    BOT.send_message(id_user, mes_prev_period, parse_mode='html')
    BOT.send_message(id_user, mes_cur_period, parse_mode='html')


def show_chatreport_mine_last_smena_results(id_user: int):
    last_smenadate_item = db.db_smena.get_last_smenadate()
    mes = f'<b>Мои результаты за последнюю смену ({last_smenadate_item.date_smena.strftime("%d.%m.%Y")})</b>\n\n'
    report_items = db.db_reports.get_chatreport_mine_last_smena_results(id_user, last_smenadate_item.date_smena)
    kol_night, kol_day = report_items
    mes += f'Дневных авто: {kol_day}\n'
    mes += f'Ночных авто: {kol_night}'
    BOT.send_message(id_user, mes, parse_mode='html')


def show_chatreport_mine_brigadirs(id_user: int):
    user = db.db_users.get_user(id_user)
    brigadirs_tuple = db.db_users.get_district_brigadirs(user.id_city, user.district)
    if brigadirs_tuple:
        mes = f'Район: {user.district}\n'
        mes += 'Бригадир: ' if len(brigadirs_tuple) == 1 else 'Бригадиры:\n'
        for brigadir_item in brigadirs_tuple:
            mes += f'{brigadir_item.fam} {brigadir_item.im} {brigadir_item.ot}, +{brigadir_item.phone}\n'
        BOT.send_message(id_user, mes)


def menu_brigadir_workers_requests(message):
    menu_brigadir_workers_requests_dopsmena(message)
    menu_brigadir_workers_requests_otgul(message)
    menu_brigadir_workers_requests_newched(message)


def menu_brigadir_workers_requests_dopsmena(message):
    user_me = db.db_users.get_user(message.chat.id)
    dopsmena_requests_tuple = db.db_smena.get_unapprooved_dopsmenas(user_me.id_city)
    if dopsmena_requests_tuple:
        for dopsmena in dopsmena_requests_tuple:
            date_smena_text = dopsmena.date_smena.strftime("%d.%m.%Y")
            req_user = db.db_users.get_user(dopsmena.id_user)
            keyboard_inline = types.InlineKeyboardMarkup()
            keyboard_list = []
            keyboard_list.append(types.InlineKeyboardButton(
                text='Отказать', callback_data=f"menu_brigadir_dopsmena_approove;{req_user.id};{date_smena_text};0"))
            keyboard_list.append(types.InlineKeyboardButton(text='Подтвердить',
                                                            callback_data=f"menu_brigadir_dopsmena_approove;{req_user.id};{date_smena_text};1"))
            keyboard_inline.add(*keyboard_list, row_width=2)
            BOT.send_message(
                message.chat.id, f'{req_user.fam} {req_user.im} желает взять доп.смену на {date_smena_text}',
                reply_markup=keyboard_inline)
    else:
        BOT.send_message(message.chat.id, 'Нет запросов на доп.смены')


def menu_brigadir_workers_requests_dopsmena_approove(message, data):
    params = data.split(';')
    id_req_user = int(params[1])
    date_smena_text = params[2]
    date_smena = datetime.datetime.strptime(date_smena_text, '%d.%m.%Y').date()
    approove = int(params[3])
    req_user = db.db_users.get_user(id_req_user)

    db.db_smena.set_dopsmena_approove(id_req_user, date_smena, approove)

    if approove == 0:
        BOT.send_message(
            message.chat.id, f'Отказано в допсмене работнику {req_user.fam} {req_user.im} на дату {date_smena_text}')
        try:
            BOT.send_message(id_req_user, f'Вам отказано в доп.смене на дату {date_smena_text}')
        except Exception as ex_blk:
            LOGGER.error(ex_blk)
    elif approove == 1:
        # TODO как то сделать обработку если допсмену прошляпили и подтвердили сильно позже
        BOT.send_message(
            message.chat.id,
            f'Подтверждена допсмена у работника {req_user.fam} {req_user.im} на дату {date_smena_text}')
        user = db.db_users.get_user(id_req_user)
        db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['schedules'], user.id_city)
        db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['brig_schedules'], None)
        try:
            BOT.send_message(id_req_user, f'Доп.смена на дату {date_smena_text} подтверждена')
        except Exception as ex_blk:
            LOGGER.error(ex_blk)

        # TODO приглашение тут же пройти на смену, вынести в отдельный метод, и вообще это копия кода из send_smena_start_notify()
        cur_date = datetime.date.today()
        if is_smena_evening_now() and cur_date == date_smena:
            smenadate_item = db.db_smena.get_last_smenadate()
            smenadate_button_text = smenadate_item.date_smena.strftime('%Y-%m-%d')
            keyboard_inline = types.InlineKeyboardMarkup()
            keyboard_list = []
            keyboard_list.append(types.InlineKeyboardButton(text='Начать работу',
                                                            callback_data=f'smena_start;{smenadate_button_text}'))
            keyboard_inline.add(*keyboard_list, row_width=1)

            if user.id_role in (ROLES['worker'], ROLES['brigadir']):
                mes = 'Напоминаем, что сегодня по графику твоя смена. Нажми "Начать работу", как будешь готов приступить к перегону.'
            else:
                mes = 'Напоминаем, что сегодня по графику твоя смена. Нажми "Начать работу", как будешь готов приступить к работе.'
            try:
                BOT.send_message(id_req_user, mes, reply_markup=keyboard_inline)
            except Exception as ex_blk:
                LOGGER.error(ex_blk)
            db.db_smena.set_smena_notify_users(smenadate_item, [user])


def menu_brigadir_workers_requests_otgul(message):
    user_me = db.db_users.get_user(message.chat.id)
    otgul_requests_tuple = db.db_smena.get_unapprooved_otguls(user_me.id_city)
    if otgul_requests_tuple:
        for otgul in otgul_requests_tuple:
            date_smena_text = otgul.date_smena.strftime("%d.%m.%Y")
            req_user = db.db_users.get_user(otgul.id_user)
            keyboard_inline = types.InlineKeyboardMarkup()
            keyboard_list = []
            keyboard_list.append(types.InlineKeyboardButton(
                text='Отказать', callback_data=f"menu_brigadir_otgul_approove;{req_user.id};{date_smena_text};0"))
            keyboard_list.append(types.InlineKeyboardButton(text='Подтвердить',
                                                            callback_data=f"menu_brigadir_otgul_approove;{req_user.id};{date_smena_text};1"))
            keyboard_inline.add(*keyboard_list, row_width=2)
            BOT.send_message(
                message.chat.id,
                f'{req_user.fam} {req_user.im} желает взять отгул на {date_smena_text} по причине {otgul.reason_description}',
                reply_markup=keyboard_inline)
    else:
        BOT.send_message(message.chat.id, 'Нет запросов на отгулы')


def menu_brigadir_workers_requests_otgul_approove(message, data):
    params = data.split(';')
    id_req_user = int(params[1])
    date_smena_text = params[2]
    date_smena = datetime.datetime.strptime(date_smena_text, '%d.%m.%Y').date()
    approove = int(params[3])
    req_user = db.db_users.get_user(id_req_user)

    db.db_smena.set_otgul_approove(id_req_user, date_smena, approove)

    if approove == 0:
        BOT.send_message(
            message.chat.id, f'Отказано в отгуле работнику {req_user.fam} {req_user.im} на дату {date_smena_text}')
        try:
            BOT.send_message(id_req_user, f'Вам отказано в отгуле на дату {date_smena_text}')
        except Exception as ex_blk:
            LOGGER.error(ex_blk)
    elif approove == 1:
        BOT.send_message(
            message.chat.id, f'Подтвержден отгул у работника {req_user.fam} {req_user.im} на дату {date_smena_text}')
        user = db.db_users.get_user(id_req_user)
        db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['schedules'], user.id_city)
        db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['brig_schedules'], None)
        try:
            BOT.send_message(id_req_user, f'Отгул на дату {date_smena_text} подтвержден')
        except Exception as ex_blk:
            LOGGER.error(ex_blk)


def menu_brigadir_workers_requests_newched(message: Message):
    user_me = db.db_users.get_user(message.chat.id)
    if user_me.id_role == ROLES['admin'] and is_head_sup(message.chat.id):
        newsched_requests_tuple = db.db_schedule.get_support_scheds()
    else:
        newsched_requests_tuple = db.db_schedule.get_unapprooved_scheds(user_me.id_city)
    if newsched_requests_tuple:
        for newsched in newsched_requests_tuple:
            req_user = db.db_users.get_user(newsched.id_user)
            keyboard_inline = types.InlineKeyboardMarkup()
            keyboard_list = []
            keyboard_list.append(types.InlineKeyboardButton(
                text='Отказать', callback_data=f"menu_brigadir_newsched_approove;{req_user.id};{newsched.id};0"))
            keyboard_list.append(types.InlineKeyboardButton(text='Подтвердить',
                                                            callback_data=f"menu_brigadir_newsched_approove;{req_user.id};{newsched.id};1"))
            keyboard_inline.add(*keyboard_list, row_width=2)
            BOT.send_message(
                message.chat.id,
                f'{req_user.fam} {req_user.im} желает взять новый график с рабочими днями: {sched_week_template_to_words(newsched.week_template)}',
                reply_markup=keyboard_inline)
    else:
        BOT.send_message(message.chat.id, 'Нет запросов на смену графика')


def menu_brigadir_workers_requests_newched_approove(message, data):
    params = data.split(';')
    id_req_user = int(params[1])
    sched_id = int(params[2])
    approove = int(params[3])
    req_user = db.db_users.get_user(id_req_user)
    is_sup_brig = is_head_sup(message.chat.id)

    if approove == 0:
        db.db_schedule.reject_user_schedule(sched_id)
        BOT.send_message(message.chat.id, f'Отказано в новом графике работнику {req_user.fam} {req_user.im}')
        try:
            BOT.send_message(id_req_user, f'Вам отказано в новом рабочем графике')
        except Exception as ex_blk:
            LOGGER.error(ex_blk)
    elif approove == 1:
        db.db_schedule.confirm_user_schedule(sched_id)
        user = db.db_users.get_user(id_req_user)
        by_acceptor = '' if is_sup_brig else 'бригадиром'
        if not is_sup_brig:
            db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['schedules'], user.id_city)
            db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['brig_schedules'], None)
        BOT.send_message(message.chat.id, f'Подтвержден новый график у работника {req_user.fam} {req_user.im}')
        try:
            BOT.send_message(id_req_user, f'Новый рабочий график подтвержден {by_acceptor}')
        except Exception as ex_blk:
            LOGGER.error(ex_blk)


def menu_brigadir_car_leftovers_new(message):
    if datetime.datetime.strptime('06:55',
                                  '%H:%M').time() <= datetime.datetime.now().time() <= datetime.datetime.strptime(
            '09:59', '%H:%M').time():
        user_item = db.db_users.get_user(message.chat.id)
        last_smenadate_item = db.db_smena.get_last_smenadate()
        car_leftover_item = db.db_smena.get_car_leftover(user_item.id_city, last_smenadate_item.id)
        if car_leftover_item:
            BOT.send_message(message.chat.id, 'Остатки за прошедшую смену уже введены')
        else:
            keyboard = make_keyboard()
            mes = 'Введите остаток доступных авто по городу'
            BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
            states.set_state(message.chat.id, st.S_MENU_BRIGADIR_CAR_LEFTOVER_KOL_ASK.value)
    else:
        BOT.send_message(message.chat.id, 'Ввести остатки можно только с 06:55 до 10:00')


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_BRIGADIR_CAR_LEFTOVER_KOL_ASK.value)
def menu_brigadir_car_leftovers_save(message):
    choice = message.text
    try:
        kol_leftover = int(choice)
    except ValueError:
        BOT.send_message(message.chat.id, 'Введите остаток числом')
        return

    user_item = db.db_users.get_user(message.chat.id)
    last_smenadate_item = db.db_smena.get_last_smenadate()
    if db.db_smena.create_car_leftover(user_item.id_city, last_smenadate_item.id, kol_leftover, message.chat.id):
        BOT.send_message(
            message.chat.id,
            f'Показания остатков на смену {last_smenadate_item.date_smena.strftime("%d.%m.%Y")} приняты')
    else:
        BOT.send_message(message.chat.id, 'Ошибка записи остатков')
    mainmenu(message)


def menu_support_mark_penalty(message):
    menu_support_mark_penalty_city_ask(message)


def menu_support_mark_penalty_city_ask(message):
    keyboard = make_keyboard(row_width=2, fill_with_classifier=City)
    mes = 'Выберите город'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_SUPPORT_MARK_PENALTY_CITY_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_SUPPORT_MARK_PENALTY_CITY_ASK.value)
def menu_support_mark_penalty_city_save(message):
    choice = message.text
    city = db.db_classifiers.find_classifier_object(City, name=choice)
    if not city:
        BOT.send_message(message.chat.id, 'Нет такого города')
        return
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_SUPPORT_MARK_PENALTY_CITY_ASK.name, intval=city.id)
    menu_support_mark_penalty_gosnomer_ask(message)


def menu_support_mark_penalty_gosnomer_ask(message):
    keyboard = make_keyboard()
    mes = 'Введите госномер автомобиля русскими буквами по примеру А777АА799'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_SUPPORT_MARK_PENALTY_GOSNOMER_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_SUPPORT_MARK_PENALTY_GOSNOMER_ASK.value)
def menu_support_mark_penalty_gosnomer_save(message):
    gosnomer = message.text.upper()
    if len(gosnomer) != 9:
        BOT.send_message(message.chat.id, 'Госномер должен содержать 9 символов')
        return
    if bool(re.search('[a-zA-Z]', gosnomer)):
        BOT.send_message(message.chat.id, 'Госномер должен быть написан русскими буквами')
        return

    id_city = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_SUPPORT_MARK_PENALTY_CITY_ASK.name, is_delete_after_read=False).intval
    smenaservice = db.db_smena.get_smenaservice_by_gosnomer(gosnomer, id_city)
    if not smenaservice:
        BOT.send_message(message.chat.id, 'Госномер не найден среди ближайших выполненных услуг')
        return

    user = db.db_users.get_user(smenaservice.id_user)
    BOT.send_message(
        message.chat.id,
        f'Авто с госномером {gosnomer} выполнено работником {user.fam} {user.im} {user.ot} {smenaservice.date_create.strftime("%d.%m.%Y %H:%M")}')

    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_SUPPORT_MARK_PENALTY_GOSNOMER_ASK.name, textval=gosnomer)
    db.db_tempvals.set_tmpval(
        message.chat.id, st.S_MENU_SUPPORT_MARK_PENALTY_SMENASERVICE_CHECK.name, intval=smenaservice.id)
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_SUPPORT_MARK_PENALTY_USER_CHECK.name,
                              intval=smenaservice.id_user)
    menu_support_mark_penalty_category_ask(message)


def menu_support_mark_penalty_category_ask(message):
    keyboard = make_keyboard(row_width=2, fill_with_classifier=PenaltyCategory)
    mes = 'Выберите вид нарушения'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_SUPPORT_MARK_PENALTY_CATEGORY_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_SUPPORT_MARK_PENALTY_CATEGORY_ASK.value)
def menu_support_mark_penalty_category_save(message):
    choice = message.text
    penalty_category = db.db_classifiers.find_classifier_object(PenaltyCategory, name=choice)
    if not penalty_category:
        BOT.send_message(message.chat.id, 'Нет такой категории')
        return
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_SUPPORT_MARK_PENALTY_CATEGORY_ASK.name,
                              intval=penalty_category.id, textval=choice)
    menu_support_mark_penalty_type_ask(message)


def menu_support_mark_penalty_type_ask(message):
    keyb_items = []
    id_penalty_category = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_SUPPORT_MARK_PENALTY_CATEGORY_ASK.name, is_delete_after_read=False).intval
    penalty_types_tuple = db.db_penalty.get_penalty_types_by_category(id_penalty_category)
    if not penalty_types_tuple:
        menu_support_mark_penalty_type_end(message)
    else:
        for penalty_type in penalty_types_tuple:
            keyb_items.append(str(penalty_type.name))

        keyboard = make_keyboard(items=keyb_items, row_width=2)
        mes = 'Выберите описание нарушения'

        BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
        states.set_state(message.chat.id, st.S_MENU_SUPPORT_MARK_PENALTY_TYPE_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_SUPPORT_MARK_PENALTY_TYPE_ASK.value)
def menu_support_mark_penalty_category_save(message):
    choice = message.text
    id_penalty_category = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_SUPPORT_MARK_PENALTY_CATEGORY_ASK.name, is_delete_after_read=False).intval
    penalty_type = db.db_penalty.get_penalty_type_by_name(id_penalty_category, choice)
    if not penalty_type:
        BOT.send_message(message.chat.id, 'Нет такого пункта')
        return
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_SUPPORT_MARK_PENALTY_TYPE_ASK.name,
                              intval=penalty_type.id, textval=choice)
    menu_support_mark_penalty_type_end(message)


def menu_support_mark_penalty_type_end(message):
    menu_support_mark_penalty_save(message)


def menu_support_mark_penalty_save(message):
    id_user = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_SUPPORT_MARK_PENALTY_USER_CHECK.name).intval
    id_smenaservice = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_SUPPORT_MARK_PENALTY_SMENASERVICE_CHECK.name).intval

    penalty_category = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_SUPPORT_MARK_PENALTY_CATEGORY_ASK.name)
    id_penalty_category = penalty_category.intval
    penalty_category_name = penalty_category.textval

    penalty_type = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_SUPPORT_MARK_PENALTY_TYPE_ASK.name)
    id_penalty_type = penalty_type.intval if penalty_type else None
    penalty_type_name = penalty_type.textval if penalty_type else None
    penalty_type_text = f' ({penalty_type_name})' if penalty_type_name else ''

    gosnomer = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_SUPPORT_MARK_PENALTY_GOSNOMER_ASK.name).textval

    id_author = message.chat.id
    author_item = db.db_users.get_user(id_author)
    about_nick_text = f'Если у вас возникли вопросы или возражения, то обратитесь к @{author_item.nick}' if author_item.nick else ''

    mes_for_worker = f'Вам выставлен штраф за \"{penalty_category_name}{penalty_type_text}\" по автомобилю {gosnomer}.\n\n{about_nick_text}'
    if db.db_penalty.add_new_penalty(id_user, id_smenaservice, id_penalty_category, id_penalty_type, id_author):
        try:
            BOT.send_message(id_user, mes_for_worker)
        except Exception as ex_blk:
            LOGGER.error(ex_blk)
        BOT.send_message(message.chat.id, 'Нарушение зафиксировано')
        mainmenu(message)
    else:
        BOT.send_message(message.chat.id, 'Ошибка записи в базу')


def menu_support_smena_close(message):
    menu_support_smena_close_confirm_ask(message)


def menu_support_smena_close_confirm_ask(message):
    keyb_items = []
    keyb_items.append('Да')
    row_width = 2

    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    mes = 'Завершить смену?'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_SUPPORT_SMENAEND_CONFIRM_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_SUPPORT_SMENAEND_CONFIRM_ASK.value)
def menu_support_smena_close_confirm_save(message):
    choice = message.text
    if choice != 'Да':
        return

    smena = db.db_smena.get_user_unfinished_smena(message.chat.id)
    id_smena = smena.id if smena else None

    if db.db_smena.close_nostrict_smena(id_smena):
        BOT.send_message(message.chat.id, 'Смена закрыта')
        db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['supports'], None)
        mainmenu(message)
    else:
        BOT.send_message(message.chat.id, 'Ошибка записи в базу')


def menu_worker_smenaservice_new(message):
    db.db_tempvals.set_tmpval(message.chat.id, 'smenaservice_daily', intval=0)
    menu_worker_smenaservice_district_ask(message)


def menu_worker_smenaservice_district_ask(message):
    user = db.db_users.get_user(message.chat.id)
    keyb_items = []
    districts_tuple = db.db_smena.get_districts_by_city(user.id_city)
    for district_item in districts_tuple:
        keyb_items.append(str(district_item.district))

    keyboard = make_keyboard(items=keyb_items, row_width=2)
    mes = 'Выберите район мойки'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_DISTRICT_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENASERVICE_DISTRICT_ASK.value)
def menu_worker_smenaservice_district_save(message):
    choice = message.text
    user = db.db_users.get_user(message.chat.id)

    if not choice.isdigit() or not db.db_smena.is_district_exists(user.id_city, int(choice)):
        BOT.send_message(message.chat.id, 'Нет такого района')
        return
    district = int(choice)

    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_DISTRICT_ASK.name, intval=district)
    menu_worker_smenaservice_wash_ask(message)


def menu_worker_smenaservice_wash_ask(message):
    user = db.db_users.get_user(message.chat.id)
    district = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_SMENASERVICE_DISTRICT_ASK.name, is_delete_after_read=False).intval
    keyb_items = []
    washes_tuple = db.db_smena.get_washes_by_district(user.id_city, district)
    if not washes_tuple:
        BOT.send_message(message.chat.id, 'Нет моек в этом районе')
        return
    for washes_item in washes_tuple:
        keyb_items.append(washes_item.name)

    keyboard = make_keyboard(items=keyb_items, row_width=2)
    mes = 'Выберите мойку, на которой был выполнен этот автомобиль'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_WASH_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENASERVICE_WASH_ASK.value)
def menu_worker_smenaservice_wash_save(message):
    choice = message.text
    user = db.db_users.get_user(message.chat.id)
    district = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_SMENASERVICE_DISTRICT_ASK.name, is_delete_after_read=False).intval

    wash = db.db_smena.get_wash_by_name(user.id_city, district, choice)

    if not wash:
        BOT.send_message(message.chat.id, 'Нет такой мойки')
        return

    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_WASH_ASK.name,
                              intval=wash.id, textval=choice)
    menu_worker_smenaservice_carsharing_ask(message)


def menu_worker_smenaservice_carsharing_ask(message):
    keyboard = make_keyboard(row_width=2, fill_with_classifier=Carsharing)
    mes = 'Какой каршеринг?\n\n'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_CARSHARING_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENASERVICE_CARSHARING_ASK.value)
def menu_worker_smenaservice_carsharing_save(message):
    choice = message.text
    carsharing = db.db_classifiers.find_classifier_object(Carsharing, name=choice)
    if not carsharing:
        BOT.send_message(message.chat.id, 'Нет такого каршеринга')
        return
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_CARSHARING_ASK.name,
                              intval=carsharing.id, textval=choice)
    menu_worker_smenaservice_dispatch_photostatus_check(message)


def menu_worker_smenaservice_dispatch_photostatus_check(message):
    id_carsharing = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_SMENASERVICE_CARSHARING_ASK.name, is_delete_after_read=False).intval
    if id_carsharing == CARSHARINGS['citydrive']:
        menu_worker_smenaservice_dispatch_photostatus_ask(message)
    else:
        menu_worker_smenaservice_dispatch_photostatus_end(message)


def menu_worker_smenaservice_dispatch_photostatus_ask(message):
    keyb_items = []
    keyb_items.append('Да')
    keyb_items.append('Нет')
    row_width = 2

    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    mes = 'В диспетчерскую загрузились все фотографии подтверждающие состояние автомобиля?'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_DISPATCH_PHOTOSTATUS_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(
    message.chat.id) == st.S_MENU_WORKER_SMENASERVICE_DISPATCH_PHOTOSTATUS_ASK.value)
def menu_worker_smenaservice_dispatch_photostatus_save(message):
    choice = message.text
    if choice == 'Да':
        is_dispatch_photostatus = 1
    elif choice == 'Нет':
        is_dispatch_photostatus = 0
    else:
        BOT.send_message(message.chat.id, 'Неправильный выбор')
        return

    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_DISPATCH_PHOTOSTATUS_ASK.name,
                              intval=is_dispatch_photostatus, textval=choice)
    menu_worker_smenaservice_dispatch_photostatus_end(message)


def menu_worker_smenaservice_dispatch_photostatus_end(message):
    menu_worker_smenaservice_gosnomer_ask(message)


def menu_worker_smenaservice_gosnomer_ask(message):
    keyboard = make_keyboard()
    mes = 'Введите госномер автомобиля русскими буквами по примеру А777АА799'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_GOSNOMER_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENASERVICE_GOSNOMER_ASK.value)
def menu_workersmenaservice_gosnomer_save(message):
    gosnomer = message.text.upper()
    if len(gosnomer) != 9:
        BOT.send_message(message.chat.id, 'Госномер должен содержать 9 символов')
        return
    if bool(re.search('[a-zA-Z]', gosnomer)):
        BOT.send_message(message.chat.id, 'Госномер должен быть написан русскими буквами')
        return
    if db.db_smena.check_gosnomer_duplicate(message.chat.id, gosnomer):
        BOT.send_message(message.chat.id, 'Авто с этим госномером уже было введено вами в текущей смене')
        return

    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_GOSNOMER_ASK.name, textval=gosnomer)
    menu_worker_smenaservice_autoclass_ask(message)


def menu_worker_smenaservice_autoclass_ask(message):
    id_carsharing = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_SMENASERVICE_CARSHARING_ASK.name, is_delete_after_read=False).intval
    if id_carsharing == CARSHARINGS['citydrive']:
        db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_AUTOCLASS_ASK.name,
                                  intval=AUTO_CLASSES['econom'], textval='Эконом')
        menu_worker_smenaservice_autoclass_end(message)
    else:
        keyboard = make_keyboard(row_width=2, fill_with_classifier=AutoClass)
        mes = 'Какой класс автомобиля?\n\n'
        mes += 'Эконом: kaptur, G70, X1 и другие\n'
        mes += 'Бизнес: BMW 520, Mercedes E200 и другие\n'
        mes += 'Премиум: Porsche 911, Porsche Panamera, Range Rover и другие\n'
        mes += 'Фургон: Jumpy, Kombi, Transporter и другие'

        BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
        states.set_state(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_AUTOCLASS_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENASERVICE_AUTOCLASS_ASK.value)
def menu_worker_smenaservice_autoclass_save(message):
    choice = message.text
    autoclass = db.db_classifiers.find_classifier_object(AutoClass, name=choice)
    if not autoclass:
        BOT.send_message(message.chat.id, 'Нет такого класса')
        return
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_AUTOCLASS_ASK.name,
                              intval=autoclass.id, textval=choice)
    menu_worker_smenaservice_autoclass_end(message)


def menu_worker_smenaservice_autoclass_end(message):
    menu_worker_smenaservice_autosr_ask(message)


def menu_worker_smenaservice_autosr_ask(message):
    is_daily = bool(db.db_tempvals.get_tmpval(message.chat.id, 'smenaservice_daily', is_delete_after_read=False).intval)
    if is_daily:
        db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_AUTOSR_ASK.name,
                                  intval=AUTO_SR_TYPES['sroch'])
        menu_worker_smenaservice_autosr_end(message)
    else:
        id_carsharing = db.db_tempvals.get_tmpval(
            message.chat.id, st.S_MENU_WORKER_SMENASERVICE_CARSHARING_ASK.name, is_delete_after_read=False).intval
        if id_carsharing == CARSHARINGS['citydrive']:
            db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_AUTOSR_ASK.name,
                                      intval=AUTO_SR_TYPES['plan'])
            menu_worker_smenaservice_autosr_end(message)
        else:
            keyboard = make_keyboard(row_width=2, fill_with_classifier=AutoSrType)
            mes = 'Статус авто?'

            BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
            states.set_state(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_AUTOSR_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENASERVICE_AUTOSR_ASK.value)
def menu_worker_smenaservice_autosr_save(message):
    choice = message.text
    autosr = db.db_classifiers.find_classifier_object(AutoSrType, name=choice)
    if not autosr:
        BOT.send_message(message.chat.id, 'Нет такого статуса')
        return
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_AUTOSR_ASK.name,
                              intval=autosr.id, textval=choice)
    menu_worker_smenaservice_autosr_end(message)


def menu_worker_smenaservice_autosr_end(message):
    menu_worker_smenaservice_washusl_type_ask(message)


def menu_worker_smenaservice_washusl_type_ask(message):
    is_daily = bool(db.db_tempvals.get_tmpval(message.chat.id, 'smenaservice_daily', is_delete_after_read=False).intval)
    if is_daily:
        db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_WASHUSL_TYPE_ASK.name,
                                  intval=WASH_USL_TYPES['complex'])
        menu_worker_smenaservice_washusl_type_end(message)
    else:
        id_carsharing = db.db_tempvals.get_tmpval(
            message.chat.id, st.S_MENU_WORKER_SMENASERVICE_CARSHARING_ASK.name, is_delete_after_read=False).intval
        if id_carsharing == CARSHARINGS['citydrive']:
            db.db_tempvals.set_tmpval(
                message.chat.id, st.S_MENU_WORKER_SMENASERVICE_WASHUSL_TYPE_ASK.name, intval=WASH_USL_TYPES['beskont'])
            menu_worker_smenaservice_washusl_type_end(message)
        else:
            keyboard = make_keyboard(row_width=2, fill_with_classifier=WashUslType)
            mes = 'Вид мойки?'

            BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
            states.set_state(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_WASHUSL_TYPE_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENASERVICE_WASHUSL_TYPE_ASK.value)
def menu_worker_smenaservice_washusl_type_save(message):
    choice = message.text
    washusl = db.db_classifiers.find_classifier_object(WashUslType, name=choice)
    if not washusl:
        BOT.send_message(message.chat.id, 'Нет такого статуса')
        return
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_WASHUSL_TYPE_ASK.name,
                              intval=washusl.id, textval=choice)
    menu_worker_smenaservice_washusl_type_end(message)


def menu_worker_smenaservice_washusl_type_end(message):
    menu_worker_smenaservice_omyv_check(message)


def menu_worker_smenaservice_omyv_check(message):
    if db.db_prefs.get_pref("zima_blizko").intval == 1:
        menu_worker_smenaservice_omyv_ask(message)
    else:
        db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_OMYV_KOL_ASK.name, intval=0)
        menu_worker_smenaservice_omyv_end(message)


def menu_worker_smenaservice_omyv_ask(message):
    keyb_items = []
    keyb_items.append('Да')
    keyb_items.append('Нет')
    row_width = 2

    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    mes = 'Был ли долив омывающей жидкости?'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_OMYV_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENASERVICE_OMYV_ASK.value)
def menu_worker_smenaservice_omyv_kol_ask(message):
    choice = message.text
    if choice == 'Да':
        keyb_items = []
        keyb_items.append('25%')
        keyb_items.append('50%')
        keyb_items.append('75%')
        keyb_items.append('100%')
        keyb_items.append('125%')
        row_width = 2

        keyboard = make_keyboard(items=keyb_items, row_width=row_width)
        mes = 'Какое количество канистры было долито?'

        BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
        states.set_state(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_OMYV_KOL_ASK.value)
    elif choice == 'Нет':
        db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_OMYV_KOL_ASK.name, intval=0)
        menu_worker_smenaservice_omyv_end(message)
    else:
        BOT.send_message(message.chat.id, 'Неправильный выбор')
        return


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENASERVICE_OMYV_KOL_ASK.value)
def menu_worker_smenaservice_omyv_kol_save(message):
    choice = message.text
    if choice == '25%':
        kol_omyv = 25
    elif choice == '50%':
        kol_omyv = 50
    elif choice == '75%':
        kol_omyv = 75
    elif choice == '100%':
        kol_omyv = 100
    elif choice == '125%':
        kol_omyv = 125
    else:
        BOT.send_message(message.chat.id, 'Неправильный выбор')
        return

    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_OMYV_KOL_ASK.name, intval=kol_omyv)
    menu_worker_smenaservice_omyv_end(message)


def menu_worker_smenaservice_omyv_end(message):
    menu_worker_smenaservice_is_skoda(message)


def menu_worker_smenaservice_is_skoda(message):
    id_auto_class = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_SMENASERVICE_AUTOCLASS_ASK.name, is_delete_after_read=False).intval
    if id_auto_class == AUTO_CLASSES['skoda_rapid']:
        menu_worker_smenaservice_kapot_video_ask(message)
    else:
        menu_worker_smenaservice_accept_ask(message)


def menu_worker_smenaservice_kapot_video_ask(message):
    id_wash = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_SMENASERVICE_WASH_ASK.name, is_delete_after_read=False).intval
    gosnomer = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_SMENASERVICE_GOSNOMER_ASK.name, is_delete_after_read=False).textval
    id_req_kapot = db.db_reqs.create_empty_kapot_request(message.chat.id, id_wash, gosnomer)
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_REQ_KAPOT_CREATE.name, intval=id_req_kapot)

    keyb_items = []
    row_width = 2
    keyb_items.append('Далее')
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    mes = 'Загрузите короткое видео-подтверждение закрытого капота.\n\nПосле загрузки, нажмите Далее'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_KAPOT_VIDEO_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENASERVICE_KAPOT_VIDEO_ASK.value)
def menu_worker_smenaservice_kapot_video_save(message):
    id_req_kapot = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_REQ_KAPOT_CREATE.name, is_delete_after_read=False).intval
    id_media_type = MEDIA_TYPES['video_kapot_confirmation']
    media_tuple = db.db_media.get_media_tuple(message.chat.id, id_media_type, id_req_kapot=id_req_kapot)

    if message.video:
        if media_tuple and len(media_tuple) > 0:
            BOT.send_message(message.chat.id, 'Достаточно одного видео!')
            return
        file_id = message.video.file_id
        db.db_media.save_media(message.chat.id, id_media_type, file_id, id_req_kapot=id_req_kapot)
        BOT.send_message(message.chat.id, 'Видео загружено')
    else:
        if message.text == 'Далее':
            if not media_tuple or len(media_tuple) == 0:
                BOT.send_message(message.chat.id, 'Вначале загрузи видео!')
                return
            menu_worker_smenaservice_kapot_video_end(message)


def menu_worker_smenaservice_kapot_video_end(message):
    id_req_kapot = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_REQ_KAPOT_CREATE.name, is_delete_after_read=False).intval
    if db.db_reqs.update_kapot_request_for_ready(id_req_kapot):
        BOT.send_message(message.chat.id, 'Видео отправлено на проверку')
    else:
        BOT.send_message(message.chat.id, 'Ошибка записи видео в базу')
    menu_worker_smenaservice_accept_ask(message)


def menu_worker_smenaservice_accept_ask(message):
    name_wash = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_SMENASERVICE_WASH_ASK.name, is_delete_after_read=False).textval
    name_carsharing = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_SMENASERVICE_CARSHARING_ASK.name, is_delete_after_read=False).textval
    gosnomer = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_SMENASERVICE_GOSNOMER_ASK.name, is_delete_after_read=False).textval
    # TODO класс авто нету у ситидрайва, потом отфильтровать, кому показывать
    # auto_class = db.tempvals.get_tmpval(
    #     message.chat.id, st.S_MENU_WORKER_SMENASERVICE_AUTOCLASS_ASK.name, is_delete_after_read=False).textval
    omyv_kol = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_SMENASERVICE_OMYV_KOL_ASK.name, is_delete_after_read=False).intval

    keyb_items = []
    keyb_items.append('Да')
    keyb_items.append('Нет')
    row_width = 2

    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    mes = f'Мойка: {name_wash}\n'
    mes += f'Каршеринг: {name_carsharing}\n'
    mes += f'Госномер: {gosnomer}\n'
    # mes += f'Класс авто: {auto_class}\n'
    if db.db_prefs.get_pref("zima_blizko").intval == 1:
        mes += f'Залито омывайки: {omyv_kol}%\n\n'
    mes += 'Подтвердить авто?'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_ACCEPT_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENASERVICE_ACCEPT_ASK.value)
def menu_worker_smenaservice_save(message):
    choice = message.text
    if choice == 'Да':
        id_user = message.chat.id
        daily = bool(db.db_tempvals.get_tmpval(message.chat.id,
                                               'smenaservice_daily', is_delete_after_read=False).intval)
        smena = db.db_smena.get_user_unfinished_smena(id_user)
        id_smena = smena.id if smena else None
        id_wash = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_WASH_ASK.name).intval
        id_carsharing = db.db_tempvals.get_tmpval(
            message.chat.id, st.S_MENU_WORKER_SMENASERVICE_CARSHARING_ASK.name).intval
        dispatch_photostatus = db.db_tempvals.get_tmpval(
            message.chat.id, st.S_MENU_WORKER_SMENASERVICE_DISPATCH_PHOTOSTATUS_ASK.name)
        dispatch_photostatus = dispatch_photostatus.intval if dispatch_photostatus else None
        gosnomer = db.db_tempvals.get_tmpval(
            message.chat.id, st.S_MENU_WORKER_SMENASERVICE_GOSNOMER_ASK.name, is_delete_after_read=False).textval
        auto_class = db.db_tempvals.get_tmpval(
            message.chat.id, st.S_MENU_WORKER_SMENASERVICE_AUTOCLASS_ASK.name)
        id_auto_class = auto_class.intval if auto_class else None
        id_auto_sr_type = db.db_tempvals.get_tmpval(
            message.chat.id, st.S_MENU_WORKER_SMENASERVICE_AUTOSR_ASK.name).intval
        id_wash_usl_type = db.db_tempvals.get_tmpval(
            message.chat.id, st.S_MENU_WORKER_SMENASERVICE_WASHUSL_TYPE_ASK.name).intval
        omyv_percent = db.db_tempvals.get_tmpval(
            message.chat.id, st.S_MENU_WORKER_SMENASERVICE_OMYV_KOL_ASK.name).intval

        if db.db_smena.add_new_smenaservice(id_user, daily, id_smena, id_wash, id_carsharing, dispatch_photostatus,
                                            gosnomer, id_auto_class, id_auto_sr_type, id_wash_usl_type, omyv_percent):
            BOT.send_message(
                message.chat.id,
                'Данные по авто записаны\n\nНапоминаем о необходимости парковки автомобиля по правилам ПДД')

            if id_carsharing == CARSHARINGS['citydrive']:
                menu_worker_dirty_photo_ask(message)
            else:
                mainmenu(message)
        else:
            BOT.send_message(message.chat.id, 'Ошибка записи в базу')

    elif choice == 'Нет':
        pass
    else:
        BOT.send_message(message.chat.id, 'Неправильный выбор')
        return


def menu_worker_dirty_photo_ask(message):
    keyb_items = []
    row_width = 2
    keyb_items.append('Далее')
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    mes = 'Загрузи фото грязного авто (не более 4 шт.) и нажми Далее'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_DIRTY_PHOTO_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENASERVICE_DIRTY_PHOTO_ASK.value)
def menu_worker_dirty_photo_save(message):
    user = db.db_users.get_user(message.chat.id)
    gosnomer = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_SMENASERVICE_GOSNOMER_ASK.name, is_delete_after_read=False).textval
    smenaservice = db.db_smena.get_smenaservice_by_gosnomer(gosnomer, user.id_city)
    id_media_type = MEDIA_TYPES['smenaservice_dirty']
    media_tuple = db.db_media.get_media_tuple(message.chat.id, id_media_type, id_smenaservice=smenaservice.id)
    if message.photo:
        if media_tuple and len(media_tuple) >= 4:
            BOT.send_message(message.chat.id, 'Уже достаточно фото!')
            return
        file_id = message.photo[-1].file_id
        db.db_media.save_media(message.chat.id, id_media_type, file_id,
                               id_smenaservice=smenaservice.id, sent_to_chat=False)
        BOT.send_message(message.chat.id, 'Фото загружено')
    else:
        if message.text == 'Далее':
            if not media_tuple or len(media_tuple) == 0:
                BOT.send_message(message.chat.id, 'Вначале загрузи фотографии!')
                return
            menu_worker_clean_photo_ask(message)


def menu_worker_clean_photo_ask(message):
    keyb_items = []
    row_width = 2
    keyb_items.append('Далее')
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    mes = 'Загрузи фото чистого авто (не более 7 шт.) и нажми Далее'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_SMENASERVICE_CLEAN_PHOTO_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENASERVICE_CLEAN_PHOTO_ASK.value)
def menu_worker_clean_photo_save(message):
    user = db.db_users.get_user(message.chat.id)
    gosnomer = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_SMENASERVICE_GOSNOMER_ASK.name, is_delete_after_read=False).textval
    smenaservice = db.db_smena.get_smenaservice_by_gosnomer(gosnomer, user.id_city)
    id_media_type = MEDIA_TYPES['smenaservice_clean']
    media_tuple = db.db_media.get_media_tuple(message.chat.id, id_media_type, id_smenaservice=smenaservice.id)
    if message.photo:
        if media_tuple and len(media_tuple) >= 7:
            BOT.send_message(message.chat.id, 'Уже достаточно фото!')
            return
        file_id = message.photo[-1].file_id
        db.db_media.save_media(message.chat.id, id_media_type, file_id,
                               id_smenaservice=smenaservice.id, sent_to_chat=False)
        BOT.send_message(message.chat.id, 'Фото загружено')
    else:
        if message.text == 'Далее':
            if not media_tuple or len(media_tuple) == 0:
                BOT.send_message(message.chat.id, 'Вначале загрузи фотографии!')
                return
            BOT.send_message(message.chat.id, 'Фото приняты')
            mainmenu(message)


def menu_worker_dopusl_new(message):
    last_wash = db.db_smena.get_last_user_wash(message.chat.id)
    if last_wash:
        db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_WASH_ASK.name,
                                  intval=last_wash.id, textval=last_wash.name)
        BOT.send_message(message.chat.id, f'Текущая мойка: {last_wash.name}')
        menu_worker_dopusl_gosnomer_ask(message)
    else:
        menu_worker_dopusl_district_ask(message)


def menu_worker_dopusl_district_ask(message):
    user = db.db_users.get_user(message.chat.id)
    keyb_items = []
    districts_tuple = db.db_smena.get_districts_by_city(user.id_city)
    for district_item in districts_tuple:
        keyb_items.append(str(district_item.district))

    keyboard = make_keyboard(items=keyb_items, row_width=2)
    mes = 'Выберите номер района'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_DISTRICT_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_REQ_DOPUSL_DISTRICT_ASK.value)
def menu_worker_dopusl_district_save(message):
    choice = message.text
    user = db.db_users.get_user(message.chat.id)

    if not choice.isdigit() or not db.db_smena.is_district_exists(user.id_city, int(choice)):
        BOT.send_message(message.chat.id, 'Нет такого района')
        return
    district = int(choice)

    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_DISTRICT_ASK.name, intval=district)
    menu_worker_dopusl_wash_ask(message)


def menu_worker_dopusl_wash_ask(message):
    user = db.db_users.get_user(message.chat.id)
    district = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_DISTRICT_ASK.name, is_delete_after_read=False).intval
    keyb_items = []
    washes_tuple = db.db_smena.get_washes_by_district(user.id_city, district)
    if not washes_tuple:
        BOT.send_message(message.chat.id, 'Нет моек в этом районе')
        return
    for washes_item in washes_tuple:
        keyb_items.append(washes_item.name)

    keyboard = make_keyboard(items=keyb_items, row_width=2)
    mes = 'Выберите адрес мойки'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_WASH_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_REQ_DOPUSL_WASH_ASK.value)
def menu_worker_dopusl_wash_save(message):
    choice = message.text
    user = db.db_users.get_user(message.chat.id)
    district = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_DISTRICT_ASK.name, is_delete_after_read=False).intval

    wash = db.db_smena.get_wash_by_name(user.id_city, district, choice)

    if not wash:
        BOT.send_message(message.chat.id, 'Нет такой мойки')
        return

    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_WASH_ASK.name,
                              intval=wash.id, textval=choice)
    menu_worker_dopusl_gosnomer_ask(message)


def menu_worker_dopusl_gosnomer_ask(message):
    keyboard = make_keyboard()
    mes = 'Введите госномер автомобиля русскими буквами по примеру А777АА799'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_GOSNOMER_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_REQ_DOPUSL_GOSNOMER_ASK.value)
def menu_worker_dopusl_gosnomer_save(message):
    gosnomer = message.text.upper()
    if len(gosnomer) != 9:
        BOT.send_message(message.chat.id, 'Госномер должен содержать 9 символов')
        return  # TODO сколько раз уже этот кусок кода повторяется
    if bool(re.search('[a-zA-Z]', gosnomer)):
        BOT.send_message(message.chat.id, 'Госномер должен быть написан русскими буквами')
        return

    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_GOSNOMER_ASK.name, textval=gosnomer)
    menu_worker_dopusl_type_ask(message)


def menu_worker_dopusl_type_ask(message):
    keyboard = make_keyboard(row_width=2, fill_with_classifier=DopuslTypes)
    gosnomer = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_GOSNOMER_ASK.name, is_delete_after_read=False).textval
    mes = f'Выберите услугу, которую необходимо выполнить по автомобилю {gosnomer}'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_TYPE_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_REQ_DOPUSL_TYPE_ASK.value)
def menu_worker_dopusl_type_save(message):
    choice = message.text
    dopusl_type_item = db.db_classifiers.find_classifier_object(DopuslTypes, name=choice)
    if not dopusl_type_item:
        BOT.send_message(message.chat.id, 'Нет такой услуги')
        return
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_TYPE_ASK.name, intval=dopusl_type_item.id)
    if dopusl_type_item.id == REQS_DOPUSL_TYPES['chem']:
        menu_worker_dopusl_elemkol_ask(message)
    else:
        menu_worker_dopusl_create_empty_dirty(message)


def menu_worker_dopusl_elemkol_ask(message):
    keyb_items = []
    row_width = 3
    for kol_item in range(1, 7):
        keyb_items.append(str(kol_item))
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    mes = 'Укажите количество элементов'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_ELEMKOL_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_REQ_DOPUSL_ELEMKOL_ASK.value)
def menu_worker_dopusl_elemkol_save(message):
    choice = message.text
    try:
        kol_elem = int(choice)
    except ValueError:
        BOT.send_message(message.chat.id, 'Неправильный выбор')
        return
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_ELEMKOL_ASK.name, intval=kol_elem)
    menu_worker_dopusl_create_empty_dirty(message)


def menu_worker_dopusl_create_empty_dirty(message):
    id_purity = REQS_DOPUSL_PURITY['dirty']
    id_wash = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_WASH_ASK.name, is_delete_after_read=False).intval
    gosnomer = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_GOSNOMER_ASK.name, is_delete_after_read=False).textval
    id_dopusl_type = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_TYPE_ASK.name, is_delete_after_read=False).intval
    kol_elem_item = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_ELEMKOL_ASK.name, is_delete_after_read=False)
    kol_elem = kol_elem_item.intval if kol_elem_item else None
    id_req_dirty = None

    id_req_dopusl = db.db_reqs.create_empty_dopusl_request(
        message.chat.id, id_req_dirty, id_purity, id_wash, gosnomer, id_dopusl_type, kol_elem)
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_CREATE_DIRTY.name, intval=id_req_dopusl)

    if is_smena_period_now():
        menu_worker_dopusl_dirty_photo_ask(message)
    else:
        menu_worker_dopusl_dirty_serviceapp_photo_ask(message)


def menu_worker_dopusl_dirty_serviceapp_photo_ask(message):
    keyb_items = []
    row_width = 2
    keyb_items.append('Далее')
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)

    mes = 'Загрузите скриншот из сервисного приложения с комментарием к срочной мойке.\n\nПосле этого нажмите Далее'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_DIRTY_SERVICEAPP_PHOTO_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(
    message.chat.id) == st.S_MENU_WORKER_REQ_DOPUSL_DIRTY_SERVICEAPP_PHOTO_ASK.value)
def menu_worker_dopusl_dirty_serviceapp_photo_save(message):
    smena = db.db_smena.get_user_unfinished_smena(message.chat.id)
    id_smena = smena.id if smena else None
    id_req_dopusl = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_CREATE_DIRTY.name, is_delete_after_read=False).intval
    id_media_type = MEDIA_TYPES['dopusl_serviceapp']
    media_tuple = db.db_media.get_media_tuple(message.chat.id, id_media_type,
                                              id_smena=id_smena, id_req_dopusl=id_req_dopusl)
    if message.photo:
        if media_tuple and len(media_tuple) > 2:
            BOT.send_message(message.chat.id, 'Уже достаточно фото!')
            return
        file_id = message.photo[-1].file_id
        db.db_media.save_media(message.chat.id, id_media_type, file_id, id_smena=id_smena, id_req_dopusl=id_req_dopusl)
        BOT.send_message(message.chat.id, 'Фото загружено')
    else:
        if message.text == 'Далее':
            if not media_tuple or len(media_tuple) == 0:
                BOT.send_message(message.chat.id, 'Вначале загрузи фотографии!')
                return
            menu_worker_dopusl_dirty_photo_ask(message)


def menu_worker_dopusl_dirty_photo_ask(message):
    keyb_items = []
    row_width = 2
    keyb_items.append('Далее')
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)

    mes = 'Загрузите фотографию грязных элементов и нажмите Далее'
    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_DIRTY_PHOTO_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_REQ_DOPUSL_DIRTY_PHOTO_ASK.value)
def menu_worker_dopusl_dirty_photo_save(message):
    smena = db.db_smena.get_user_unfinished_smena(message.chat.id)
    id_smena = smena.id if smena else None
    id_req_dopusl = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_CREATE_DIRTY.name, is_delete_after_read=False).intval
    id_media_type = MEDIA_TYPES['dopusl_dirty']
    media_tuple = db.db_media.get_media_tuple(message.chat.id, id_media_type,
                                              id_smena=id_smena, id_req_dopusl=id_req_dopusl)
    if message.photo:
        if media_tuple and len(media_tuple) > 3:
            BOT.send_message(message.chat.id, 'Уже достаточно фото!')
            return
        file_id = message.photo[-1].file_id
        db.db_media.save_media(message.chat.id, id_media_type, file_id, id_smena=id_smena, id_req_dopusl=id_req_dopusl)
        BOT.send_message(message.chat.id, 'Фото загружено')
    else:
        if message.text == 'Далее':
            if not media_tuple or len(media_tuple) == 0:
                BOT.send_message(message.chat.id, 'Вначале загрузи фотографии!')
                return
            menu_worker_dopusl_dirty_save(message)


def menu_worker_dopusl_dirty_save(message):
    id_req_dopusl = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_CREATE_DIRTY.name, is_delete_after_read=False).intval
    if db.db_reqs.update_dopusl_request_for_ready(id_req_dopusl):
        db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['supports'], None)
        BOT.send_message(message.chat.id, 'Ожидайте ответа от техподдержки. Обычно это занимает 2-3 минуты.')
        mainmenu(message)
    else:
        BOT.send_message(message.chat.id, 'Ошибка записи в базу')


def menu_worker_tphelp_new(message):
    menu_worker_tphelp_type_ask(message)


def menu_worker_tphelp_type_ask(message):
    keyboard = make_keyboard(row_width=1, fill_with_classifier=TpHelpTypes)
    mes = 'Выберите причину обращения в техподдержку'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_TPHELP_TYPE_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_TPHELP_TYPE_ASK.value)
def menu_worker_tphelp_type_save(message):
    choice = message.text
    tphelp_type = db.db_classifiers.find_classifier_object(TpHelpTypes, name=choice)
    if not tphelp_type:
        BOT.send_message(message.chat.id, 'Нет такого варианта')
        return
    if tphelp_type.id == TP_HELP_TYPES['forgotten_stuff']:
        menu_worker_tphelp_forgottenstuff(message)
    elif tphelp_type.id == TP_HELP_TYPES['carstatus']:
        menu_worker_tphelp_carstatus(message)
    elif tphelp_type.id == TP_HELP_TYPES['app_help']:
        menu_worker_tphelp_apphelp(message)
    elif tphelp_type.id == TP_HELP_TYPES['restricted_area']:
        menu_worker_tphelp_restricted_area(message)


def menu_worker_tphelp_forgottenstuff(message):
    id_req_tphelp = db.db_reqs.create_empty_tphelp_request(message.chat.id, TP_HELP_TYPES['forgotten_stuff'])
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_TPHELP_REQ_CHECK.name, intval=id_req_tphelp)
    menu_worker_tphelp_forgottenstuff_photo_ask(message)


def menu_worker_tphelp_carstatus(message):
    id_req_tphelp = db.db_reqs.create_empty_tphelp_request(message.chat.id, TP_HELP_TYPES['carstatus'])
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_TPHELP_REQ_CHECK.name, intval=id_req_tphelp)
    menu_worker_tphelp_carstatus_photo_ask(message)


def menu_worker_tphelp_apphelp(message):
    id_req_tphelp = db.db_reqs.create_empty_tphelp_request(message.chat.id, TP_HELP_TYPES['app_help'])
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_TPHELP_REQ_CHECK.name, intval=id_req_tphelp)
    menu_worker_tphelp_apphelp_photo_ask(message)


def menu_worker_tphelp_restricted_area(message):
    id_req_tphelp = db.db_reqs.create_empty_tphelp_request(message.chat.id, TP_HELP_TYPES['restricted_area'])
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_TPHELP_REQ_CHECK.name, intval=id_req_tphelp)
    menu_worker_tphelp_restricted_area_photo_ask(message)


def menu_worker_tphelp_forgottenstuff_photo_ask(message):
    keyb_items = []
    row_width = 2
    keyb_items.append('Далее')
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    mes = 'Загрузите фотографию забытой вещи и нажмите Далее'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_TPHELP_FORGOTTENSTUFF_PHOTO_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(
    message.chat.id) == st.S_MENU_WORKER_TPHELP_FORGOTTENSTUFF_PHOTO_ASK.value)
def menu_worker_tphelp_forgottenstuff_photo_save(message):
    smena = db.db_smena.get_user_unfinished_smena(message.chat.id)
    id_smena = smena.id if smena else None
    req_tphelp = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_TPHELP_REQ_CHECK.name, is_delete_after_read=False)
    id_req_tphelp = req_tphelp.intval if req_tphelp else None
    id_media_type = MEDIA_TYPES['forgotten_stuff']
    media_tuple = db.db_media.get_media_tuple(message.chat.id, id_media_type, id_smena, id_req_tphelp)
    if message.photo:
        if media_tuple and len(media_tuple) > 2:
            BOT.send_message(message.chat.id, 'Уже достаточно фото!')
            return
        file_id = message.photo[-1].file_id
        db.db_media.save_media(message.chat.id, id_media_type, file_id, id_smena, id_req_tphelp)
        BOT.send_message(message.chat.id, 'Фото загружено')
    else:
        if message.text == 'Далее':
            if not media_tuple or len(media_tuple) == 0:
                BOT.send_message(message.chat.id, 'Вначале загрузи фотографии!')
                return
            menu_worker_tphelp_forgottenstuff_place_ask(message)


def menu_worker_tphelp_forgottenstuff_place_ask(message):
    keyb_items = []
    row_width = 2
    keyb_items.append('в бардачке')
    keyb_items.append('в багажнике')  # TODO из словаря
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    mes = 'Укажите где оставили забытую вещь'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_TPHELP_FORGOTTENSTUFF_PLACE_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(
    message.chat.id) == st.S_MENU_WORKER_TPHELP_FORGOTTENSTUFF_PLACE_ASK.value)
def menu_worker_tphelp_forgottenstuff_place_save(message):
    choice = message.text
    places = ['в бардачке', 'в багажнике']
    if choice not in places:
        BOT.send_message(message.chat.id, 'Выберите правильный вариант!')
        return

    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_TPHELP_FORGOTTENSTUFF_PLACE_ASK.name, textval=choice)
    menu_worker_tphelp_forgottenstuff_gosnomer_ask(message)


def menu_worker_tphelp_forgottenstuff_gosnomer_ask(message):
    keyboard = make_keyboard()
    mes = 'Введите госномер автомобиля русскими буквами по примеру А777АА799'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_TPHELP_FORGOTTENSTUFF_GOSNOMER_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(
    message.chat.id) == st.S_MENU_WORKER_TPHELP_FORGOTTENSTUFF_GOSNOMER_ASK.value)
def menu_worker_tphelp_forgottenstuff_gosnomer_save(message):
    gosnomer = message.text.upper()
    if len(gosnomer) != 9:  # TODO много где проверяется, можно и отдельным методом
        BOT.send_message(message.chat.id, 'Госномер должен содержать 9 символов')
        return
    if bool(re.search('[a-zA-Z]', gosnomer)):
        BOT.send_message(message.chat.id, 'Госномер должен быть написан русскими буквами')
        return

    db.db_tempvals.set_tmpval(
        message.chat.id, st.S_MENU_WORKER_TPHELP_FORGOTTENSTUFF_GOSNOMER_ASK.name, textval=gosnomer)
    menu_worker_tphelp_forgottenstuff_save(message)


def menu_worker_tphelp_forgottenstuff_save(message):
    id_req_tphelp = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_WORKER_TPHELP_REQ_CHECK.name).intval
    place = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_WORKER_TPHELP_FORGOTTENSTUFF_PLACE_ASK.name).textval
    gosnomer = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_TPHELP_FORGOTTENSTUFF_GOSNOMER_ASK.name).textval
    commentary = f'Зафиксируйте, пожалуйста, забытые вещи. Водитель оставил {place}'
    if db.db_reqs.update_tphelp_request_for_ready(id_req_tphelp, gosnomer, commentary):
        BOT.send_message(message.chat.id, 'Спасибо за информацию! Мы обязательно уведомим владельца.')
        mainmenu(message)
    else:
        BOT.send_message(message.chat.id, 'Ошибка записи в базу')


def menu_worker_tphelp_carstatus_photo_ask(message):
    keyb_items = []
    row_width = 2
    keyb_items.append('Далее')
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    mes = 'Загрузите фотографию неисправности автомобиля и нажмите Далее'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_TPHELP_CARSTATUS_PHOTO_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_TPHELP_CARSTATUS_PHOTO_ASK.value)
def menu_worker_tphelp_carstatus_photo_save(message):
    smena = db.db_smena.get_user_unfinished_smena(message.chat.id)
    id_smena = smena.id if smena else None
    req_tphelp = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_TPHELP_REQ_CHECK.name, is_delete_after_read=False)
    id_req_tphelp = req_tphelp.intval if req_tphelp else None
    id_media_type = MEDIA_TYPES['carstatus']
    media_tuple = db.db_media.get_media_tuple(message.chat.id, id_media_type, id_smena, id_req_tphelp)
    if message.photo:  # TODO весь этот метод много где используется, можно вынести отдельно
        if media_tuple and len(media_tuple) > 2:
            BOT.send_message(message.chat.id, 'Уже достаточно фото!')
            return
        file_id = message.photo[-1].file_id
        db.db_media.save_media(message.chat.id, id_media_type, file_id, id_smena, id_req_tphelp)
        BOT.send_message(message.chat.id, 'Фото загружено')
    else:
        if message.text == 'Далее':
            if not media_tuple or len(media_tuple) == 0:
                BOT.send_message(message.chat.id, 'Вначале загрузи фотографии!')
                return
            menu_worker_tphelp_carstatus_gosnomer_ask(message)


def menu_worker_tphelp_carstatus_gosnomer_ask(message):
    keyboard = make_keyboard()
    mes = 'Введите госномер автомобиля русскими буквами по примеру А777АА799'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_TPHELP_CARSTATUS_GOSNOMER_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_TPHELP_CARSTATUS_GOSNOMER_ASK.value)
def menu_worker_tphelp_carstatus_gosnomer_save(message):
    gosnomer = message.text.upper()
    if len(gosnomer) != 9:
        BOT.send_message(message.chat.id, 'Госномер должен содержать 9 символов')
        return
    if bool(re.search('[a-zA-Z]', gosnomer)):
        BOT.send_message(message.chat.id, 'Госномер должен быть написан русскими буквами')
        return

    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_TPHELP_CARSTATUS_GOSNOMER_ASK.name, textval=gosnomer)
    menu_worker_tphelp_carstatus_commentary_ask(message)


def menu_worker_tphelp_carstatus_commentary_ask(message):
    keyb_items = []
    row_width = 2
    keyb_items.append('спущено колесо')
    keyb_items.append('застрял')  # TODO из словаря
    keyb_items.append('сел АКБ')
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    mes = 'Выберите комментарий или напишите свой'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_TPHELP_CARSTATUS_COMMENTARY_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(
    message.chat.id) == st.S_MENU_WORKER_TPHELP_CARSTATUS_COMMENTARY_ASK.value)
def menu_worker_tphelp_carstatus_commentary_save(message):
    choice = message.text
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_TPHELP_CARSTATUS_COMMENTARY_ASK.name, textval=choice)

    if choice == 'спущено колесо':
        db.db_tempvals.set_tmpval(message.chat.id, 'req_tphelp_is_wheel', intval=1)
        menu_worker_tphelp_carstatus_wheel_ask(message)
    else:
        db.db_tempvals.set_tmpval(message.chat.id, 'req_tphelp_is_wheel', intval=0)
        menu_worker_tphelp_carstatus_save(message)


def menu_worker_tphelp_carstatus_wheel_ask(message):
    keyb_items = []
    row_width = 2
    keyb_items.append('переднее правое')
    keyb_items.append('переднее левое')  # TODO из словаря
    keyb_items.append('заднее правое')
    keyb_items.append('заднее левое')
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    mes = 'Укажите какое колесо спущено'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_TPHELP_CARSTATUS_WHEEL_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_TPHELP_CARSTATUS_WHEEL_ASK.value)
def menu_worker_tphelp_carstatus_wheel_save(message):
    choice = message.text
    wheels = ['переднее правое', 'переднее левое', 'заднее правое', 'заднее левое']
    if choice not in wheels:
        BOT.send_message(message.chat.id, 'Выберите правильный вариант!')
        return

    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_TPHELP_CARSTATUS_WHEEL_ASK.name, textval=choice)
    menu_worker_tphelp_carstatus_save(message)


def menu_worker_tphelp_carstatus_save(message):
    id_req_tphelp = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_WORKER_TPHELP_REQ_CHECK.name).intval
    gosnomer = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_WORKER_TPHELP_CARSTATUS_GOSNOMER_ASK.name).textval
    reason = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_WORKER_TPHELP_CARSTATUS_COMMENTARY_ASK.name).textval
    is_wheel = db.db_tempvals.get_tmpval(message.chat.id, 'req_tphelp_is_wheel').intval

    commentary = f'Зафиксируйте, пожалуйста - {reason}'
    if is_wheel == 1:
        wheel = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_WORKER_TPHELP_CARSTATUS_WHEEL_ASK.name).textval
        commentary += f' ({wheel})'

    if db.db_reqs.update_tphelp_request_for_ready(id_req_tphelp, gosnomer, commentary):
        BOT.send_message(message.chat.id, 'Спасибо за информацию! Передаём информацию техникам.')
        mainmenu(message)
    else:
        BOT.send_message(message.chat.id, 'Ошибка записи в базу')


def menu_worker_tphelp_apphelp_photo_ask(message):
    keyb_items = []
    row_width = 2
    keyb_items.append('Далее')
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    mes = 'Загрузите скриншот сервисного приложения и нажмите Далее'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_TPHELP_APPHELP_PHOTO_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_TPHELP_APPHELP_PHOTO_ASK.value)
def menu_worker_tphelp_apphelp_photo_save(message):
    smena = db.db_smena.get_user_unfinished_smena(message.chat.id)
    id_smena = smena.id if smena else None
    req_tphelp = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_TPHELP_REQ_CHECK.name, is_delete_after_read=False)
    id_req_tphelp = req_tphelp.intval if req_tphelp else None
    id_media_type = MEDIA_TYPES['app_help']
    media_tuple = db.db_media.get_media_tuple(message.chat.id, id_media_type, id_smena, id_req_tphelp)
    if message.photo:
        if media_tuple and len(media_tuple) > 2:
            BOT.send_message(message.chat.id, 'Уже достаточно фото!')
            return
        file_id = message.photo[-1].file_id
        db.db_media.save_media(message.chat.id, id_media_type, file_id, id_smena, id_req_tphelp)
        BOT.send_message(message.chat.id, 'Фото загружено')
    else:
        if message.text == 'Далее':
            if not media_tuple or len(media_tuple) == 0:
                BOT.send_message(message.chat.id, 'Вначале загрузи фотографии!')
                return
            menu_worker_tphelp_apphelp_gosnomer_ask(message)


def menu_worker_tphelp_apphelp_gosnomer_ask(message):
    keyb_items = []
    row_width = 2
    keyb_items.append('Пропустить')
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    mes = 'Введите госномер автомобиля русскими буквами по примеру: А777АА799.\nЕсли ошибка не связана с конкретным автомобилем, нажмите кнопку Пропустить'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_TPHELP_APPHELP_GOSNOMER_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_TPHELP_APPHELP_GOSNOMER_ASK.value)
def menu_worker_tphelp_apphelp_gosnomer_save(message):
    choice = message.text
    if choice == 'Пропустить':
        is_with_gosnomer = 0
    else:
        is_with_gosnomer = 1
        gosnomer = choice.upper()
        if len(gosnomer) != 9:
            BOT.send_message(message.chat.id, 'Госномер должен содержать 9 символов')
            return
        if bool(re.search('[a-zA-Z]', gosnomer)):
            BOT.send_message(message.chat.id, 'Госномер должен быть написан русскими буквами')
            return
        db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_TPHELP_APPHELP_GOSNOMER_ASK.name, textval=gosnomer)

    db.db_tempvals.set_tmpval(message.chat.id, 'is_with_gosnomer', intval=is_with_gosnomer)
    menu_worker_tphelp_apphelp_commentary_ask(message)


def menu_worker_tphelp_apphelp_commentary_ask(message):
    keyb_items = []
    row_width = 1
    keyb_items.append('Ошибка при входе в сервисное приложение')
    keyb_items.append('Не завершить задачу по плановой мойке. Селектор передач в положении P')  # TODO из словаря
    keyb_items.append('Ошибка при взятии автомобиля в аренду')
    keyb_items.append('Не находит автомобиль по GPS')
    keyb_items.append('Автомобиль не заводится')
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    mes = 'Выберите комментарий или напишите свой'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_TPHELP_APPHELP_COMMENTARY_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_TPHELP_APPHELP_COMMENTARY_ASK.value)
def menu_worker_tphelp_apphelp_commentary_save(message):
    choice = message.text
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_TPHELP_APPHELP_COMMENTARY_ASK.name, textval=choice)

    menu_worker_tphelp_apphelp_save(message)


def menu_worker_tphelp_apphelp_save(message):
    id_req_tphelp = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_WORKER_TPHELP_REQ_CHECK.name).intval
    gosnomer_item = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_WORKER_TPHELP_APPHELP_GOSNOMER_ASK.name)
    gosnomer = gosnomer_item.textval if gosnomer_item else None
    commentary = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_WORKER_TPHELP_APPHELP_COMMENTARY_ASK.name).textval

    if db.db_reqs.update_tphelp_request_for_ready(id_req_tphelp, gosnomer, commentary):
        BOT.send_message(message.chat.id, 'Ожидайте ответа от техподдержки. Обычно это занимает 2-3 минуты.')
        mainmenu(message)
    else:
        BOT.send_message(message.chat.id, 'Ошибка записи в базу')


def menu_worker_tphelp_restricted_area_photo_ask(message):
    keyb_items = []
    row_width = 2
    keyb_items.append('Далее')
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    mes = 'Загрузите фотографию закрытой территории и нажмите Далее'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_TPHELP_RESTRICTEDAREA_PHOTO_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(
    message.chat.id) == st.S_MENU_WORKER_TPHELP_RESTRICTEDAREA_PHOTO_ASK.value)
def menu_worker_tphelp_restricted_area_photo_save(message):
    smena = db.db_smena.get_user_unfinished_smena(message.chat.id)
    id_smena = smena.id if smena else None
    req_tphelp = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_TPHELP_REQ_CHECK.name, is_delete_after_read=False)
    id_req_tphelp = req_tphelp.intval if req_tphelp else None
    id_media_type = MEDIA_TYPES['restricted_area']
    media_tuple = db.db_media.get_media_tuple(message.chat.id, id_media_type, id_smena, id_req_tphelp)
    if message.photo:
        if media_tuple and len(media_tuple) > 2:
            BOT.send_message(message.chat.id, 'Уже достаточно фото!')
            return
        file_id = message.photo[-1].file_id
        db.db_media.save_media(message.chat.id, id_media_type, file_id, id_smena, id_req_tphelp)
        BOT.send_message(message.chat.id, 'Фото загружено')
    else:
        if message.text == 'Далее':
            if not media_tuple or len(media_tuple) == 0:
                BOT.send_message(message.chat.id, 'Вначале загрузи фотографии!')
                return
            menu_worker_tphelp_restricted_area_gosnomer_ask(message)


def menu_worker_tphelp_restricted_area_gosnomer_ask(message):
    keyboard = make_keyboard()
    mes = 'Введите госномер автомобиля русскими буквами по примеру А777АА799'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_TPHELP_RESTRICTEDAREA_GOSNOMER_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(
    message.chat.id) == st.S_MENU_WORKER_TPHELP_RESTRICTEDAREA_GOSNOMER_ASK.value)
def menu_worker_tphelp_restricted_area_gosnomer_save(message):
    gosnomer = message.text.upper()
    if len(gosnomer) != 9:
        BOT.send_message(message.chat.id, 'Госномер должен содержать 9 символов')
        return
    if bool(re.search('[a-zA-Z]', gosnomer)):
        BOT.send_message(message.chat.id, 'Госномер должен быть написан русскими буквами')
        return

    db.db_tempvals.set_tmpval(
        message.chat.id, st.S_MENU_WORKER_TPHELP_RESTRICTEDAREA_GOSNOMER_ASK.name, textval=gosnomer)
    menu_worker_tphelp_restricted_area_save(message)


def menu_worker_tphelp_restricted_area_save(message):
    id_req_tphelp = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_WORKER_TPHELP_REQ_CHECK.name).intval
    gosnomer = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_TPHELP_RESTRICTEDAREA_GOSNOMER_ASK.name).textval
    commentary = f'Зафиксируйте, пожалуйста - автомобиль на закрытой территории'

    if db.db_reqs.update_tphelp_request_for_ready(id_req_tphelp, gosnomer, commentary):
        BOT.send_message(message.chat.id, 'Спасибо за информацию! Передаём информацию техникам.')
        mainmenu(message)
    else:
        BOT.send_message(message.chat.id, 'Ошибка записи в базу')


def menu_worker_smena_close(message):
    user = db.db_users.get_user(message.chat.id)
    if not db.db_smena.is_user_on_smena(user.id):
        BOT.send_message(message.chat.id, 'Смена уже была завершена')
        mainmenu(message)
    else:
        menu_worker_smena_close_early_check(message)


def menu_worker_smena_close_early_check(message):
    today_datetime = datetime.datetime.now()
    if today_datetime.hour >= 6 and today_datetime.hour <= NIGHT_SMENA_END[0]:
        menu_worker_smena_close_early_end(message)
    else:
        keyboard = make_keyboard(row_width=2, fill_with_classifier=EarlySmenaEndReason)
        mes = 'Почему так рано?'

        BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
        states.set_state(message.chat.id, st.S_MENU_WORKER_SMENAEND_EARLY_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENAEND_EARLY_ASK.value)
def menu_worker_smena_close_early_save(message):
    choice = message.text
    early_reason = db.db_classifiers.find_classifier_object(EarlySmenaEndReason, name=choice)
    if not early_reason:
        BOT.send_message(message.chat.id, 'Выберите правильную причину')
        return
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_SMENAEND_EARLY_ASK.name,
                              intval=early_reason.id, textval=choice)
    if early_reason.id == EARLY_SMENA_END_REASONS['other']:
        menu_worker_smena_close_early_custom_ask(message)
    elif early_reason.id == EARLY_SMENA_END_REASONS['few_cars']:
        menu_worker_smena_close_early_fewcars_photo_ask(message)
    else:
        menu_worker_smena_close_early_end(message)


def menu_worker_smena_close_early_custom_ask(message):
    keyboard = make_keyboard()
    mes = 'Опишите причину раннего завершения смены'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_SMENAEND_EARLY_CUSTOM.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENAEND_EARLY_CUSTOM.value)
def menu_worker_smena_close_early_custom_save(message):
    choice = message.text
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_SMENAEND_EARLY_CUSTOM.name, textval=choice)
    menu_worker_smena_close_early_end(message)


def menu_worker_smena_close_early_fewcars_photo_ask(message):
    keyb_items = []
    row_width = 2
    keyb_items.append('Далее')
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    mes = 'Загрузи скриншот карты своего района с сервисного приложения и нажми Далее'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_SMENAEND_EARLY_FEWCARS_PHOTO_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(
    message.chat.id) == st.S_MENU_WORKER_SMENAEND_EARLY_FEWCARS_PHOTO_ASK.value)
def menu_worker_smena_close_early_fewcars_photo_save(message):
    smena = db.db_smena.get_user_unfinished_smena(message.chat.id)
    id_smena = smena.id if smena else None
    id_media_type = MEDIA_TYPES['screenshot_district_serviceapp']
    media_tuple = db.db_media.get_media_tuple(message.chat.id, id_media_type, id_smena)
    if message.photo:
        if media_tuple and len(media_tuple) > 0:
            BOT.send_message(message.chat.id, 'Уже достаточно фото!')
            return
        file_id = message.photo[-1].file_id
        db.db_media.save_media(message.chat.id, id_media_type, file_id, id_smena)
        BOT.send_message(message.chat.id, 'Фото загружено')
    else:
        if message.text == 'Далее':
            if not media_tuple or len(media_tuple) == 0:
                BOT.send_message(message.chat.id, 'Вначале загрузи фотографии!')
                return
            menu_worker_smena_close_early_end(message)


def menu_worker_smena_close_early_end(message):
    menu_worker_smena_close_carlist_approove_ask(message)


def menu_worker_smena_close_carlist_approove_ask(message):
    smena = db.db_smena.get_user_unfinished_smena(message.chat.id)
    smenaservices_tuple = db.db_smena.get_smenaservices_by_smena(smena.id)
    mes = ''
    count = 1
    if smenaservices_tuple:
        for smenaservice in smenaservices_tuple:
            mes += f'{count}. {smenaservice.gosnomer}\n'
            count += 1
        mes += '\nВ ваш отчёт будут записаны эти автомобили.\n'
    else:
        mes += 'Нет автомобилей за эту смену\n'
    mes += 'Если обнаружили ошибку в отчете, то нажмите Исправить. Если отчет верен, то нажмите Далее'

    keyb_items = []
    row_width = 2
    keyb_items.append('Далее')
    keyb_items.append('Исправить')
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_SMENAEND_CARLIST_APPROOVE_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENAEND_CARLIST_APPROOVE_ASK.value)
def menu_worker_smena_close_carlist_approove_save(message):
    choice = message.text
    if choice == 'Исправить':
        BOT.send_message(message.chat.id, 'В разработке...')  # TODO В разработке
    elif choice == 'Далее':
        menu_worker_smena_close_last_parked_car_photo_ask(message)


def menu_worker_smena_close_last_parked_car_photo_ask(message):
    keyb_items = []
    row_width = 2
    keyb_items.append('Далее')
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    mes = 'Убедись, что последний автомобиль стоит по ПДД. И отправь фотографию последнего припаркованного автомобиля'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_SMENAEND_LAST_PARKED_CAR_PHOTO_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(
    message.chat.id) == st.S_MENU_WORKER_SMENAEND_LAST_PARKED_CAR_PHOTO_ASK.value)
def menu_worker_smena_close_last_parked_car_photo_save(message):
    smena = db.db_smena.get_user_unfinished_smena(message.chat.id)
    id_smena = smena.id if smena else None
    id_media_type = MEDIA_TYPES['photo_last_parked_car']
    media_tuple = db.db_media.get_media_tuple(message.chat.id, id_media_type, id_smena)
    if message.photo:
        if media_tuple and len(media_tuple) > 0:
            BOT.send_message(message.chat.id, 'Уже достаточно фото!')
            return
        file_id = message.photo[-1].file_id
        db.db_media.save_media(message.chat.id, id_media_type, file_id, id_smena)
        BOT.send_message(message.chat.id, 'Фото загружено')
    else:
        if message.text == 'Далее':
            if not media_tuple or len(media_tuple) == 0:
                BOT.send_message(message.chat.id, 'Вначале загрузи фотографии!')
                return
            menu_worker_smena_close_leftovers_photo_check(message)


def menu_worker_smena_close_leftovers_photo_check(message):
    # TODO а как сопсна вести ветку завершения смены от Ситидрайва, если в одной смене все каршеринги вперемешку
    menu_worker_smena_close_leftovers_photo_ask(message)
    # id_carsharing = db.tempvals.get_tmpval(
    #     message.chat.id, st.S_MENU_WORKER_SMENASERVICE_CARSHARING_ASK.name, is_delete_after_read=False).intval
    # if id_carsharing == CARSHARINGS['yandexdrive']:
    #     menu_worker_smena_close_leftovers_photo_ask(message)
    # else:
    #     menu_worker_smena_close_save(message)


def menu_worker_smena_close_leftovers_photo_ask(message):
    keyb_items = []
    row_width = 2
    keyb_items.append('Далее')
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)

    mes = 'Какое количество автомобилей осталось на карте ЯндексДрайва?'
    resources_list = ['screenshot_yandex_leftover_1', 'screenshot_yandex_leftover_2']
    media_list = []
    mes_count = 0
    for res_name in resources_list:
        res_item = db.db_resources.get_res(res_name)
        if res_item:
            media_list.append(types.InputMediaPhoto(res_item.file_id, caption=(mes if mes_count == 0 else None)))
            mes_count += 1
    if media_list:
        BOT.send_media_group(message.chat.id, media_list)

    mes2 = 'Прикрепи скриншоты, как на примере'
    BOT.send_message(message.chat.id, mes2, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_SMENAEND_LEFTOVERS_PHOTO_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENAEND_LEFTOVERS_PHOTO_ASK.value)
def menu_worker_smena_close_leftovers_photo_save(message):
    smena = db.db_smena.get_user_unfinished_smena(message.chat.id)
    id_smena = smena.id if smena else None
    id_media_type = MEDIA_TYPES['screenshot_car_leftovers']
    media_tuple = db.db_media.get_media_tuple(message.chat.id, id_media_type, id_smena)
    if message.photo:
        if media_tuple and len(media_tuple) > 2:
            BOT.send_message(message.chat.id, 'Уже достаточно фото!')
            return
        file_id = message.photo[-1].file_id
        db.db_media.save_media(message.chat.id, id_media_type, file_id, id_smena)
        BOT.send_message(message.chat.id, 'Фото загружено')
    else:
        if message.text == 'Далее':
            if not media_tuple or len(media_tuple) == 0:
                BOT.send_message(message.chat.id, 'Вначале загрузи фотографии!')
                return
            menu_worker_smena_close_leftovers_kol_ask(message)


def menu_worker_smena_close_leftovers_kol_ask(message):
    keyboard = make_keyboard(row_width=2, fill_with_classifier=LeftoverCarsKol)
    mes = 'Какое количество автомобилей ЯндексДрайва осталось на районе?'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_SMENAEND_LEFTOVERS_KOL_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SMENAEND_LEFTOVERS_KOL_ASK.value)
def menu_worker_smena_close_leftovers_kol_save(message):
    choice = message.text
    leftover_cars_item = db.db_classifiers.find_classifier_object(LeftoverCarsKol, name=choice)
    if not leftover_cars_item:
        BOT.send_message(message.chat.id, 'Выберите правильное количество из предложенных')
        return
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_SMENAEND_LEFTOVERS_KOL_ASK.name,
                              intval=leftover_cars_item.id, textval=choice)
    menu_worker_smena_close_screenshot_example_photo_ask(message)


def menu_worker_smena_close_screenshot_example_photo_ask(message):
    keyb_items = []
    row_width = 2
    keyb_items.append('Далее')
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)

    mes = 'Необходимо прикрепить скриншоты общего вида карты, и района в котором вы работали'
    resources_list = ['map_districts_all', 'map_districts_one']
    media_list = []
    mes_count = 0
    for res_name in resources_list:
        res_item = db.db_resources.get_res(res_name)
        if res_item:
            media_list.append(types.InputMediaPhoto(res_item.file_id, caption=(mes if mes_count == 0 else None)))
            mes_count += 1
    if media_list:
        BOT.send_media_group(message.chat.id, media_list)

    mes2 = 'Прикрепи скриншоты, как на примере'
    BOT.send_message(message.chat.id, mes2, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_SMENAEND_SCREENSHOT_EXAMPLE_PHOTO_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(
    message.chat.id) == st.S_MENU_WORKER_SMENAEND_SCREENSHOT_EXAMPLE_PHOTO_ASK.value)
def menu_worker_smena_close_screenshot_example_photo_save(message):
    smena = db.db_smena.get_user_unfinished_smena(message.chat.id)
    id_smena = smena.id if smena else None
    id_media_type = MEDIA_TYPES['screenshot_example']
    media_tuple = db.db_media.get_media_tuple(message.chat.id, id_media_type, id_smena)
    if message.photo:
        if media_tuple and len(media_tuple) > 2:
            BOT.send_message(message.chat.id, 'Уже достаточно фото!')
            return
        file_id = message.photo[-1].file_id
        db.db_media.save_media(message.chat.id, id_media_type, file_id, id_smena)
        BOT.send_message(message.chat.id, 'Фото загружено')
    else:
        if message.text == 'Далее':
            if not media_tuple or len(media_tuple) == 0:
                BOT.send_message(message.chat.id, 'Вначале загрузи фотографии!')
                return
            menu_worker_smena_close_save(message)


def menu_worker_smena_close_save(message):
    smena = db.db_smena.get_user_unfinished_smena(message.chat.id)
    id_smena = smena.id if smena else None
    early_smena_end_reason = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_WORKER_SMENAEND_EARLY_ASK.name)
    id_early_smena_end_reason = early_smena_end_reason.intval if early_smena_end_reason else None
    custom_reason = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_WORKER_SMENAEND_EARLY_CUSTOM.name)
    custom_early_smena_end_reason = custom_reason.textval if custom_reason else None
    leftover_cars_kol = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_WORKER_SMENAEND_LEFTOVERS_KOL_ASK.name)
    id_leftover_cars_kol = leftover_cars_kol.intval if leftover_cars_kol else None

    if db.db_smena.close_smena(id_smena, id_early_smena_end_reason, custom_early_smena_end_reason,
                               id_leftover_cars_kol):
        BOT.send_message(message.chat.id, 'Смена закрыта')
        check_for_user_without_norm_schedule(message)

        smenaservices = db.db_smena.get_smenaservices_by_smena(id_smena=smena.id)
        if len(smenaservices) == 0:
            db.db_penalty.add_new_penalty(id_user=message.chat.id, id_smenaservice=None,
                                          id_penalty_category=50, id_author=None, id_penalty_type=None)

            BOT.send_message(chat_id=message.chat.id,
                             text='Вам выставлен штраф за прогул из-за отсутствия введённых автомобилей на смене')

    else:
        BOT.send_message(message.chat.id, 'Ошибка записи в базу')


def check_for_user_without_norm_schedule(message):
    cur_sched_item = db.db_schedule.get_user_schedule(message.chat.id)
    if not cur_sched_item or (cur_sched_item and cur_sched_item.week_template == '0000000'):
        menu_worker_assignsmena_nextday_ask(message)
    else:
        mainmenu(message)


def menu_worker_assignsmena_nextday_ask(message):
    keyb_items = []
    row_width = 2

    today_date = datetime.date.today()
    start_delta = 0
    if is_smena_evening_now():
        start_delta = 1
    for cur_delta in range(start_delta, 6):
        next_smena_date = today_date + datetime.timedelta(days=cur_delta)
        keyb_items.append(next_smena_date.strftime('%m.%d'))

    keyb_items.append('Другое')
    keyboard = make_keyboard(items=keyb_items, row_width=row_width, is_with_cancel=False)

    mes = 'Когда вы в следующий раз выходите на смену?\n'
    mes += 'Выберите дату из списка'
    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_ASSIGNSMENA_NEXTDAY_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_ASSIGNSMENA_NEXTDAY_ASK.value)
def menu_worker_assignsmena_nextday_save(message):
    choice = message.text

    if choice == 'Другое':
        keyboard = make_keyboard(is_reset=True)
        mes = 'Введите дату следующего выхода на смену, в виде ММ.ДД (месяц и день)'
        BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
        states.set_state(message.chat.id, st.S_MENU_WORKER_ASSIGNSMENA_NEXTDAY_CUSTOM_ASK.value)
        return

    smena_dates = []
    today_date = datetime.date.today()
    start_delta = 0
    if is_smena_evening_now():
        start_delta = 1
    for cur_delta in range(start_delta, 6):
        next_smena_date = today_date + datetime.timedelta(days=cur_delta)
        smena_dates.append(next_smena_date.strftime('%m.%d'))

    if choice not in smena_dates:
        BOT.send_message(message.chat.id, 'Выберите дату из списка!')
        return

    # Требование к ТЗ (странное) - чтобы выбор даты был в виде ММ.ДД. То есть, если работник вписал месяц и день,
    # а они в этом году оказались меньше текущей даты, то значит это дата следующего года
    chosen_date = datetime.datetime.strptime(f'{today_date.year}.{choice}', '%Y.%m.%d').date()
    if chosen_date < today_date:
        chosen_date = datetime.datetime.strptime(f'{today_date.year + 1}.{choice}', '%Y.%m.%d').date()
    menu_worker_assignsmena_save(message, chosen_date)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_ASSIGNSMENA_NEXTDAY_CUSTOM_ASK.value)
def menu_worker_assignsmena_nextday_custom_save(message):
    choice = message.text
    today_date = datetime.date.today()
    try:
        chosen_date = datetime.datetime.strptime(f'{today_date.year}.{choice}', '%Y.%m.%d').date()
        if chosen_date < today_date:
            chosen_date = datetime.datetime.strptime(f'{today_date.year + 1}.{choice}', '%Y.%m.%d').date()
    except ValueError:
        BOT.send_message(message.chat.id, 'Неправильно указана дата!')
        return
    menu_worker_assignsmena_save(message, chosen_date)


def menu_worker_assignsmena_save(message, chosen_date):
    db.db_smena.create_dopsmena(message.chat.id, chosen_date, auto_assigned=True)
    db.db_smena.set_dopsmena_approove(message.chat.id, chosen_date, 1)
    user_item = db.db_users.get_user(message.chat.id)
    db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['schedules'], user_item.id_city)
    db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['brig_schedules'], None)
    BOT.send_message(message.chat.id, 'Дата следующей смены записана')
    mainmenu(message)


def menu_worker_daily(message):
    user = db.db_users.get_user(message.chat.id)
    if not is_smena_period_now():
        keyb_items = []
        row_width = 2
        keyb_items.append('Выполнил дневной перегон')
        keyb_items.append('Согласование доп. услуги')
        keyb_items.append('Отчёт Rapid капот')
        if user.id_city == CITIES['moscow']:
            keyb_items.append('Отчёт РПН')
        keyb_items.append('Обращение в Support')
        keyboard = make_keyboard(items=keyb_items, row_width=row_width)
        mes = 'Выбери действие'
        BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
        states.set_state(message.chat.id, st.S_MENU_WORKER_DAILY.value)
    else:
        mes = 'Дневной перегон можно выполнить только с 10:00 по 21:00'  # TODO magic numbers
        BOT.send_message(message.chat.id, mes)
        mainmenu(message)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_DAILY.value)
def menu_worker_dailysmena_choice(message):
    user = db.db_users.get_user(message.chat.id)
    if not is_smena_period_now():
        choice = message.text
        if choice == 'Выполнил дневной перегон':
            menu_worker_daily_peregon_start(message)
        elif choice == 'Согласование доп. услуги':
            menu_worker_dopusl_new(message)
        elif choice == 'Отчёт Rapid капот':
            menu_worker_kapot_new(message)
        elif choice == 'Отчёт РПН' and user.id_city == CITIES['moscow']:
            menu_worker_rpn_new(message)
        elif choice == 'Обращение в Support':
            menu_worker_tphelp_new(message)
    else:  # TODO дубль, как в menu_worker_daily(message)
        mes = 'Дневной перегон можно выполнить только с 10:00 по 21:00'
        BOT.send_message(message.chat.id, mes)
        mainmenu(message)


def menu_worker_daily_peregon_start(message):
    db.db_tempvals.set_tmpval(message.chat.id, 'smenaservice_daily', intval=1)
    menu_worker_smenaservice_district_ask(message)


def menu_worker_kapot_new(message):
    last_wash = db.db_smena.get_last_user_wash(message.chat.id)
    if last_wash:
        db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_REQ_KAPOT_WASH_ASK.name,
                                  intval=last_wash.id, textval=last_wash.name)
        BOT.send_message(message.chat.id, f'Текущая мойка: {last_wash.name}')
        menu_worker_kapot_gosnomer_ask(message)
    else:
        menu_worker_kapot_district_ask(message)


def menu_worker_kapot_district_ask(message):
    user = db.db_users.get_user(message.chat.id)
    keyb_items = []
    districts_tuple = db.db_smena.get_districts_by_city(user.id_city)
    for district_item in districts_tuple:
        keyb_items.append(str(district_item.district))

    keyboard = make_keyboard(items=keyb_items, row_width=2)
    mes = 'Выберите номер района'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_REQ_KAPOT_DISTRICT_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_REQ_KAPOT_DISTRICT_ASK.value)
def menu_worker_kapot_district_save(message):
    choice = message.text
    user = db.db_users.get_user(message.chat.id)

    if not choice.isdigit() or not db.db_smena.is_district_exists(user.id_city, int(choice)):
        BOT.send_message(message.chat.id, 'Нет такого района')
        return
    district = int(choice)

    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_REQ_KAPOT_DISTRICT_ASK.name, intval=district)
    menu_worker_kapot_wash_ask(message)


def menu_worker_kapot_wash_ask(message):
    user = db.db_users.get_user(message.chat.id)
    district = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_REQ_KAPOT_DISTRICT_ASK.name, is_delete_after_read=False).intval
    keyb_items = []
    washes_tuple = db.db_smena.get_washes_by_district(user.id_city, district)
    if not washes_tuple:
        BOT.send_message(message.chat.id, 'Нет моек в этом районе')
        return
    for washes_item in washes_tuple:
        keyb_items.append(washes_item.name)

    keyboard = make_keyboard(items=keyb_items, row_width=2)
    mes = 'Выберите адрес мойки'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_REQ_KAPOT_WASH_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_REQ_KAPOT_WASH_ASK.value)
def menu_worker_kapot_wash_save(message):
    choice = message.text
    user = db.db_users.get_user(message.chat.id)
    district = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_REQ_KAPOT_DISTRICT_ASK.name, is_delete_after_read=False).intval

    wash = db.db_smena.get_wash_by_name(user.id_city, district, choice)

    if not wash:
        BOT.send_message(message.chat.id, 'Нет такой мойки')
        return

    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_REQ_KAPOT_WASH_ASK.name, intval=wash.id, textval=choice)
    menu_worker_kapot_gosnomer_ask(message)


def menu_worker_kapot_gosnomer_ask(message):
    keyboard = make_keyboard()
    mes = 'Введите госномер автомобиля русскими буквами по примеру А777АА799'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_REQ_KAPOT_GOSNOMER_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_REQ_KAPOT_GOSNOMER_ASK.value)
def menu_worker_kapot_gosnomer_save(message):
    gosnomer = message.text.upper()
    if len(gosnomer) != 9:
        BOT.send_message(message.chat.id, 'Госномер должен содержать 9 символов')
        return
    if bool(re.search('[a-zA-Z]', gosnomer)):
        BOT.send_message(message.chat.id, 'Госномер должен быть написан русскими буквами')
        return

    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_REQ_KAPOT_GOSNOMER_ASK.name, textval=gosnomer)

    id_wash = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_REQ_KAPOT_WASH_ASK.name, is_delete_after_read=False).intval
    id_req_kapot = db.db_reqs.create_empty_kapot_request(message.chat.id, id_wash, gosnomer)
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_REQ_KAPOT_CREATE.name, intval=id_req_kapot)

    menu_worker_kapot_video_ask(message)


def menu_worker_kapot_video_ask(message):
    keyb_items = []
    row_width = 2
    keyb_items.append('Далее')
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    mes = 'Загрузите короткое видео-подтверждение закрытого капота.\n\nПосле загрузки, нажмите Далее'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_REQ_KAPOT_VIDEO_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_REQ_KAPOT_VIDEO_ASK.value)
def menu_worker_kapot_video_save(message):
    id_req_kapot = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_REQ_KAPOT_CREATE.name, is_delete_after_read=False).intval
    id_media_type = MEDIA_TYPES['video_kapot_confirmation']
    media_tuple = db.db_media.get_media_tuple(message.chat.id, id_media_type, id_req_kapot=id_req_kapot)

    if message.video:
        if media_tuple and len(media_tuple) > 0:
            BOT.send_message(message.chat.id, 'Достаточно одного видео!')
            return
        file_id = message.video.file_id
        db.db_media.save_media(message.chat.id, id_media_type, file_id, id_req_kapot=id_req_kapot)
        BOT.send_message(message.chat.id, 'Видео загружено')
    else:
        if message.text == 'Далее':
            if not media_tuple or len(media_tuple) == 0:
                BOT.send_message(message.chat.id, 'Вначале загрузи видео!')
                return
            menu_worker_kapot_video_end(message)


def menu_worker_kapot_video_end(message):
    id_req_kapot = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_REQ_KAPOT_CREATE.name, is_delete_after_read=False).intval
    if db.db_reqs.update_kapot_request_for_ready(id_req_kapot):
        BOT.send_message(message.chat.id, 'Видео отправлено. Ожидайте подтверждения техподдержки')
    else:
        BOT.send_message(message.chat.id, 'Ошибка записи в базу')
    mainmenu(message)


def menu_worker_rpn_new(message):
    menu_worker_rpn_district_ask(message)


def menu_worker_rpn_district_ask(message):
    user = db.db_users.get_user(message.chat.id)
    keyb_items = []
    districts_tuple = db.db_smena.get_districts_by_city(user.id_city)
    for district_item in districts_tuple:
        keyb_items.append(str(district_item.district))

    keyboard = make_keyboard(items=keyb_items, row_width=2)
    mes = 'Выберите номер района'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_RPN_DISTRICT_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_RPN_DISTRICT_ASK.value)
def menu_worker_rpn_district_save(message):
    choice = message.text
    user = db.db_users.get_user(message.chat.id)

    if not choice.isdigit() or not db.db_smena.is_district_exists(user.id_city, int(choice)):
        BOT.send_message(message.chat.id, 'Нет такого района')
        return
    district = int(choice)

    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_RPN_DISTRICT_ASK.name, intval=district)
    menu_worker_rpn_wash_ask(message)


def menu_worker_rpn_wash_ask(message):
    user = db.db_users.get_user(message.chat.id)
    district = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_RPN_DISTRICT_ASK.name, is_delete_after_read=False).intval
    keyb_items = []
    washes_tuple = db.db_smena.get_washes_by_district(user.id_city, district)
    if not washes_tuple:
        BOT.send_message(message.chat.id, 'Нет моек в этом районе')
        return
    for washes_item in washes_tuple:
        keyb_items.append(washes_item.name)

    keyboard = make_keyboard(items=keyb_items, row_width=2)
    mes = 'Выберите адрес мойки'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_RPN_WASH_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_RPN_WASH_ASK.value)
def menu_worker_rpn_wash_save(message):
    choice = message.text
    user = db.db_users.get_user(message.chat.id)
    district = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_RPN_DISTRICT_ASK.name, is_delete_after_read=False).intval

    wash = db.db_smena.get_wash_by_name(user.id_city, district, choice)

    if not wash:
        BOT.send_message(message.chat.id, 'Нет такой мойки')
        return

    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_RPN_WASH_ASK.name, intval=wash.id, textval=choice)
    menu_worker_rpn_req_create(message)


def menu_worker_rpn_req_create(message):
    id_wash = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_WORKER_RPN_WASH_ASK.name,
                                        is_delete_after_read=False).intval
    id_req_rpn = db.db_reqs.create_empty_rpn_request(message.chat.id, id_wash)
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_RPN_REQ_ID.name, intval=id_req_rpn)
    menu_worker_rpn_temperaturelist_photo_ask(message)


def menu_worker_rpn_temperaturelist_photo_ask(message):
    keyb_items = []
    row_width = 2
    keyb_items.append('Далее')
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    mes = 'Сфотографируйте температурный лист. Его можно запросить у сотрудников мойки.\n⚠️Важно: не забудьте перед этим померить и внести в документ свою температуру и температуру мойщика на смене!\n\nПосле загрузки нажмите Далее'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_RPN_TEMPERATURELIST_PHOTO_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_RPN_TEMPERATURELIST_PHOTO_ASK.value)
def menu_worker_rpn_temperaturelist_photo_save(message):
    id_req_rpn = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_RPN_REQ_ID.name, is_delete_after_read=False).intval
    id_media_type = MEDIA_TYPES['rpn_temperature_list']
    media_tuple = db.db_media.get_media_tuple(message.chat.id, id_media_type, id_req_rpn=id_req_rpn)
    if message.photo:
        if media_tuple and len(media_tuple) >= 1:  # TODO плохо работает, можно всё таки загрузить и больше, если быстро
            BOT.send_message(message.chat.id, 'Уже достаточно фото!')
            return
        file_id = message.photo[-1].file_id
        db.db_media.save_media(message.chat.id, id_media_type, file_id, id_req_rpn=id_req_rpn)
        BOT.send_message(message.chat.id, 'Фото загружено')
    else:
        if message.text == 'Далее':
            if not media_tuple or len(media_tuple) == 0:
                BOT.send_message(message.chat.id, 'Вначале загрузи фотографии!')
                return
            menu_worker_rpn_gosnomer_ask(message)


def menu_worker_rpn_gosnomer_ask(message):
    keyboard = make_keyboard()
    mes = 'Введите госномер автомобиля русскими буквами по примеру А777АА799'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_RPN_GOSNOMER_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_RPN_GOSNOMER_ASK.value)
def menu_worker_rpn_gosnomer_save(message):
    gosnomer = message.text.upper()
    if len(gosnomer) != 9:
        BOT.send_message(message.chat.id, 'Госномер должен содержать 9 символов')
        return
    if bool(re.search('[a-zA-Z]', gosnomer)):
        BOT.send_message(message.chat.id, 'Госномер должен быть написан русскими буквами')
        return

    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_RPN_GOSNOMER_ASK.name, textval=gosnomer)
    menu_worker_rpn_workprocess_photo_ask(message)


def menu_worker_rpn_workprocess_photo_ask(message):
    keyb_items = []
    row_width = 2
    keyb_items.append('Далее')
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    mes = 'Загрузите три фотографии.\nОбратите внимание, что на фотографии должны присутствовать халат, маска и перчатки.'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_RPN_WORKPROCESS_PHOTO_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_RPN_WORKPROCESS_PHOTO_ASK.value)
def menu_worker_rpn_workprocess_photo_save(message):
    id_req_rpn = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_RPN_REQ_ID.name, is_delete_after_read=False).intval
    id_media_type = MEDIA_TYPES['rpn_work_process']
    media_tuple = db.db_media.get_media_tuple(message.chat.id, id_media_type, id_req_rpn=id_req_rpn)
    if message.photo:
        if media_tuple and len(media_tuple) >= 3:
            BOT.send_message(message.chat.id, 'Уже достаточно фото!')
            return
        file_id = message.photo[-1].file_id
        db.db_media.save_media(message.chat.id, id_media_type, file_id, id_req_rpn=id_req_rpn)
        BOT.send_message(message.chat.id, 'Фото загружено')
    else:
        if message.text == 'Далее':
            if not media_tuple or len(media_tuple) == 0:
                BOT.send_message(message.chat.id, 'Вначале загрузи фотографии!')
                return
            elif len(media_tuple) < 3:
                BOT.send_message(message.chat.id, 'Должно быть 3 фото!')
                return
            menu_worker_rpn_save(message)


def menu_worker_rpn_save(message):
    id_req_rpn = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_WORKER_RPN_REQ_ID.name).intval
    gosnomer = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_WORKER_RPN_GOSNOMER_ASK.name).textval
    if db.db_reqs.update_rpn_request_for_ready(id_req_rpn, gosnomer):
        BOT.send_message(message.chat.id, 'Фото отправлено. Ожидайте подтверждения техподдержки')
        mainmenu(message)
    else:
        BOT.send_message(message.chat.id, 'Ошибка записи в базу')


def menu_worker_myschedule_ask(message):
    keyb_items = []
    cur_sched = db.db_schedule.get_user_schedule(message.chat.id)
    if not cur_sched:
        mes = 'Вы ещё не выбрали себе график'
        keyb_items.append('Выбрать')
    else:
        mes = f'Ваши рабочие дни: {sched_week_template_to_words(cur_sched.week_template)}'
        # TODO сделать показ рабочих дат на 2 недели вперёд
        keyb_items.append('Изменить')

    row_width = 2
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_SCHED.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_SCHED.value)
def menu_worker_myschedule_save(message):
    choice = message.text
    if choice == 'Выбрать' or choice == 'Изменить':
        menu_worker_myschedule_new(message)


def menu_worker_myschedule_new(message):
    weekschedule_asking(message, f'_;{message.chat.id};-99')


def weekschedule_asking(message, data):
    params = data.split(';')
    result = int(params[1])
    id_user = message.chat.id

    weekschedule_new_template = db.db_tempvals.get_tmpval(
        id_user, 'weekschedule_new_template', is_delete_after_read=False)
    if weekschedule_new_template:  # TODO коряво, сделать типа как get_tmpval or ''
        weekschedule_new_template = weekschedule_new_template.textval
    else:
        weekschedule_new_template = ''
    cur_weekday = len(weekschedule_new_template)

    if result == 1:
        db.db_tempvals.set_tmpval(id_user, 'weekschedule_new_template', textval=f'{weekschedule_new_template}1')
        cur_weekday += 1
    elif result == 2:
        db.db_tempvals.set_tmpval(id_user, 'weekschedule_new_template', textval=f'{weekschedule_new_template}0')
        cur_weekday += 1

    if cur_weekday == 7:
        weekschedule_new_template = db.db_tempvals.get_tmpval(id_user, 'weekschedule_new_template').textval

        sched_id = db.db_schedule.create_user_schedule(id_user, weekschedule_new_template)
        user = db.db_users.get_user(id_user)
        if user.id_role == ROLES['brigadir'] or \
                (user.id_role == ROLES['admin'] and is_head_sup(id_user)):
            db.db_schedule.confirm_user_schedule(sched_id)
            BOT.send_message(message.chat.id, 'Новый график записан')
        else:
            head_notification_text = f'{user.fam} {user.im} желает взять новый график'
            if user.id_role in (ROLES['support'], ROLES['support_penaltier'], ROLES['support_daily']):
                BOT.send_message(message.chat.id, 'Запрос на новый график отправлен')
                try:
                    BOT.send_message(db.db_prefs.get_pref('id_head_support').intval, head_notification_text)
                except Exception as ex_blk:
                    LOGGER.error(ex_blk)
            else:
                BOT.send_message(message.chat.id, 'Запрос на новый график отправлен бригадиру')
                brigadir_item = db.db_users.get_my_random_brigadir(user)
                try:
                    BOT.send_message(brigadir_item.id, head_notification_text)
                except Exception as ex_blk:
                    LOGGER.error(ex_blk)

        mainmenu(message)
    else:
        mes = f'{WEEKDAYS_WHEN[cur_weekday]} работаем?'

        keyboard_inline = types.InlineKeyboardMarkup()
        keyboard_list = []
        keyboard_list.append(types.InlineKeyboardButton(text='Да', callback_data='weekschedule_asking;1'))
        keyboard_list.append(types.InlineKeyboardButton(text='Нет', callback_data='weekschedule_asking;2'))
        keyboard_inline.add(*keyboard_list, row_width=2)

        BOT.send_message(id_user, mes, reply_markup=keyboard_inline)


def sched_week_template_to_words(week_template):
    result = ''
    template_list = list(week_template)
    for cur_day in range(7):
        if template_list[cur_day] == '1':
            result += f'{WEEKDAYS_NUMBERS[cur_day + 1]}'
    if not result:
        result = 'вся неделя выходные'
    return result


def menu_worker_dopsmena_new(message):
    menu_worker_dopsmena_datesmena_ask(message)


def menu_worker_dopsmena_datesmena_ask(message):
    keyboard = make_keyboard()
    # TODO для красоты может показывать дату на неделю вперёд
    mes = 'На какую дату вы хотите взять доп.смену? (укажите в виде 15.01.2022)'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_DOPSMENA_SMENADATE_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_DOPSMENA_SMENADATE_ASK.value)
def menu_worker_dopsmena_datesmena_save(message):
    try:
        date_smena = datetime.datetime.strptime(message.text, '%d.%m.%Y').date()
        cur_date = datetime.date.today()
        if date_smena < cur_date:
            BOT.send_message(message.chat.id, 'Дата не должна быть раньше сегодняшней!')
            return
    except ValueError:
        BOT.send_message(message.chat.id, 'Неправильно указана дата!')
        return
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_DOPSMENA_SMENADATE_ASK.name, textval=message.text)
    menu_worker_dopsmena_save(message)


def menu_worker_dopsmena_save(message):
    user = db.db_users.get_user(message.chat.id)
    id_user = message.chat.id
    date_smena_text = db.db_tempvals.get_tmpval(id_user, st.S_MENU_WORKER_DOPSMENA_SMENADATE_ASK.name).textval
    date_smena = datetime.datetime.strptime(date_smena_text, '%d.%m.%Y').date()
    if db.db_smena.create_dopsmena(id_user, date_smena):
        if user.id_role == ROLES['brigadir']:
            db.db_smena.set_dopsmena_approove(id_user, date_smena, 1)
            BOT.send_message(message.chat.id, 'Допсмена записана')

            # TODO приглашение тут же пройти на смену, вынести в отдельный метод, и вообще это копия (уже третья здесь) кода из send_smena_start_notify()
            cur_date = datetime.date.today()
            if is_smena_evening_now() and cur_date == date_smena:
                smenadate_item = db.db_smena.get_last_smenadate()
                smenadate_button_text = smenadate_item.date_smena.strftime('%Y-%m-%d')
                keyboard_inline = types.InlineKeyboardMarkup()
                keyboard_list = []
                keyboard_list.append(types.InlineKeyboardButton(text='Начать работу',
                                                                callback_data=f'smena_start;{smenadate_button_text}'))
                keyboard_inline.add(*keyboard_list, row_width=1)

                if user.id_role in (ROLES['worker'], ROLES['brigadir']):
                    mes = 'Напоминаем, что сегодня по графику твоя смена. Нажми "Начать работу", как будешь готов приступить к перегону.'
                else:
                    mes = 'Напоминаем, что сегодня по графику твоя смена. Нажми "Начать работу", как будешь готов приступить к работе.'
                try:
                    BOT.send_message(id_user, mes, reply_markup=keyboard_inline)
                except Exception as ex_blk:
                    LOGGER.error(ex_blk)
                db.db_smena.set_smena_notify_users(smenadate_item, [user])

        else:
            BOT.send_message(message.chat.id, 'Заявка на доп.смену отправлена на рассмотрение')
            brigadir_item = db.db_users.get_my_random_brigadir(user)
            try:
                BOT.send_message(brigadir_item.id, f'{user.fam} {user.im} желает взять доп.смену')
            except Exception as ex_blk:
                LOGGER.error(ex_blk)
    else:
        BOT.send_message(message.chat.id, 'Ошибка записи отгула')
    mainmenu(message)


def menu_worker_otgul_new(message):
    menu_worker_otgul_datesmena_ask(message)


def menu_worker_otgul_datesmena_ask(message):
    keyboard = make_keyboard()
    # TODO для красоты может показывать дату на неделю вперёд
    mes = 'На какую дату смены вы хотите взять отгул? (укажите в виде 15.01.2022)'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_OTGUL_SMENADATE_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_OTGUL_SMENADATE_ASK.value)
def menu_worker_otgul_datesmena_save(message):
    try:
        date_smena = datetime.datetime.strptime(message.text, '%d.%m.%Y').date()
        cur_date = datetime.date.today()
        if date_smena < cur_date:
            BOT.send_message(message.chat.id, 'Дата не должна быть раньше сегодняшней!')
            return
    except ValueError:
        BOT.send_message(message.chat.id, 'Неправильно указана дата!')
        return
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_OTGUL_SMENADATE_ASK.name, textval=message.text)
    menu_worker_otgul_reason_description_ask(message)


def menu_worker_otgul_reason_description_ask(message):
    keyboard = make_keyboard()
    mes = 'Опишите причину для отгула'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_OTGUL_DESCRIPTION_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_OTGUL_DESCRIPTION_ASK.value)
def menu_worker_otgul_reason_description_save(message):
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_OTGUL_DESCRIPTION_ASK.name, textval=message.text)
    menu_worker_otgul_save(message)


def menu_worker_otgul_save(message):
    user = db.db_users.get_user(message.chat.id)
    id_user = message.chat.id
    date_smena_text = db.db_tempvals.get_tmpval(id_user, st.S_MENU_WORKER_OTGUL_SMENADATE_ASK.name).textval
    date_smena = datetime.datetime.strptime(date_smena_text, '%d.%m.%Y').date()
    reason_description = db.db_tempvals.get_tmpval(id_user, st.S_MENU_WORKER_OTGUL_DESCRIPTION_ASK.name).textval
    if db.db_smena.create_otgul(id_user, date_smena, reason_description):
        if user.id_role == ROLES['brigadir']:
            db.db_smena.set_otgul_approove(id_user, date_smena, 1)
            BOT.send_message(message.chat.id, 'Отгул записан')  # TODO что, все бригадиры могут лепить себе отгулы? :-)
        else:
            BOT.send_message(message.chat.id, 'Заявка на отгул отправлена на рассмотрение')
            brigadir_item = db.db_users.get_my_random_brigadir(user)
            try:
                BOT.send_message(brigadir_item.id, f'{user.fam} {user.im} желает взять отгул')
            except Exception as ex_blk:
                LOGGER.error(ex_blk)
    else:
        BOT.send_message(message.chat.id, 'Ошибка записи отгула')
    mainmenu(message)


def menu_lk(message):
    mes = ''
    id_user = message.chat.id
    user = db.db_users.get_user(id_user)
    role_item = db.db_classifiers.find_classifier_object(Role, id=user.id_role)
    role_item_karatel = db.db_classifiers.find_classifier_object(
        Role, id=ROLES['karatel']) if db.db_users.is_user_exists_as_karatel(id_user) else None
    role_item_teacher = db.db_classifiers.find_classifier_object(
        Role, id=ROLES['teacher']) if db.db_users.is_user_exists_as_teacher(user.phone) else None

    if user.active == 1 and user.reg == 1:
        status = 'работает'
    elif user.active == 1 and user.reg == 0:
        status = 'ожидание регистрации'
    else:
        status = 'не работает'

    mes += f'<b>ФИО:</b> {user.fam} {user.im} {user.ot}\n'
    mes += f'<b>Статус:</b> {status}\n'
    if role_item_karatel or role_item_teacher:
        mes += f'<b>Роли:</b> {role_item.name}'
        mes += f', {role_item_karatel.name}' if role_item_karatel else ''
        mes += f', {role_item_teacher.name}' if role_item_teacher else ''
        mes += '\n'
    else:
        mes += f'<b>Роль:</b> {role_item.name}\n'
    mes += f'<b>Номер телефона:</b> +{user.phone}\n'
    mes += f'<b>Почта:</b> {user.email or "не указано"}\n'

    if user.active == 1 and not user.email:
        keyboard_inline = types.InlineKeyboardMarkup()
        keyboard_list = []
        keyboard_list.append(types.InlineKeyboardButton(
            text='Указать почту', callback_data=f"menu_lk_actualize_email;1"))
        keyboard_inline.add(*keyboard_list, row_width=1)
        BOT.send_message(id_user, mes, parse_mode='html', reply_markup=keyboard_inline)
    else:
        BOT.send_message(id_user, mes, parse_mode='html')


def lk_actualize_email_ask(message, data):
    params = data.split(';')
    result = int(params[1])
    id_user = message.chat.id
    user = db.db_users.get_user(id_user)

    if result != 1 or user.active != 1:
        BOT.send_message(message.chat.id, 'Нет доступа')
        return

    if user.email:
        BOT.send_message(message.chat.id, 'Почта уже указана ранее')
        return

    keyboard = make_keyboard()
    mes = 'Напишите ваш email'
    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_ACTUALIZE_PERSONAL_DATA_EMAIL_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_ACTUALIZE_PERSONAL_DATA_EMAIL_ASK.value)
def lk_actualize_email_save(message):
    email = message.text.lower()
    if len(email) > 100:
        BOT.send_message(message.chat.id, 'Слишком длинный email')
        return

    if not bool(re.search(r"^[\w\.\+\-]+\@[\w]+\.[a-z]{2,3}$", email)):
        BOT.send_message(message.chat.id, 'Неправильный формат адреса email')
        return

    if db.db_users.update_email(message.chat.id, email):
        BOT.send_message(message.chat.id, 'Почта записана')
        menu_lk(message)
        mainmenu(message)
    else:
        BOT.send_message(message.chat.id, 'Ошибка записи отгула')


def cmd_update_resources(message):
    # cmd_fda77e8e323a_update_resources
    res_tuple = db.db_resources.get_unloaded_resources()
    if res_tuple:
        for res in res_tuple:
            with open(res.path, 'rb') as jpg_file:
                msg = BOT.send_photo(message.chat.id, jpg_file)
                db.db_resources.set_file_id(res.name, msg.photo[-1].file_id)
        BOT.send_message(message.chat.id, 'Ресурсы сохранены')


def make_keyboard(items=None, row_width=1, fill_with_classifier=None,
                  forbid_classifier_ids=None, is_classifier_reverse=False,
                  is_with_cancel=True, is_reset=False, is_with_back_btn=False,
                  is_yes_no_template=False):
    """Создание обычной клавиатуры с параметрами"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard_list = []

    if is_reset or (not items and not fill_with_classifier and not is_with_cancel):
        return types.ReplyKeyboardRemove()

    if fill_with_classifier:
        classifier_items = db.db_classifiers.get_classifier_items(
            fill_with_classifier, is_reverse=is_classifier_reverse)
        for item in classifier_items:
            if forbid_classifier_ids:
                if item.id not in forbid_classifier_ids:
                    keyboard_list.append(item.name)
            else:
                keyboard_list.append(item.name)

    if items:
        for item in items:
            keyboard_list.append(item)

    if is_yes_no_template:
        keyboard_list.append('Да')
        keyboard_list.append('Нет')
        if row_width == 1:
            row_width = 2

    # if is_with_back_btn:
    #     keyboard_list.append(BACK_BTN_TITLE)
    #     if row_width == 1:
    #         row_width = 2

    if is_with_cancel:
        keyboard_list.append('Отмена')

    keyboard.add(*keyboard_list, row_width=row_width)
    return keyboard


def timer_1min():
    """Таймер выполняющийся каждую 1 минуту"""
    LOGGER.info('Timer_1min thread started...')
    cycle_period = 60  # 10 if config.IS_TEST else 60
    while True:
        try:
            send_reqs_tphelp_to_support()
            send_reqs_rpn_to_support()
            send_reqs_kapot_to_support()
            send_reqs_dopusl_to_support()

            send_reqs_tphelp_responses_to_driver()
            send_reqs_rpn_responses_to_driver()
            send_reqs_kapot_responses_to_driver()
            send_reqs_dopusl_responses_to_driver()

            check_contragents_opl_periods_and_reestr()

            time.sleep(cycle_period)
        except Exception as ex_tm:
            LOGGER.error(ex_tm)
            time.sleep(cycle_period)


def timer_5min():
    """Таймер выполняющийся каждую 5 минуту"""
    LOGGER.info('Timer_5min thread started...')
    cycle_period = 10  # 10 if config.IS_TEST else 60
    while True:
        try:
            send_report_karatel_washcheck()
            send_report_karatel_outcheck()

            time.sleep(cycle_period)
        except Exception as ex_tm:
            LOGGER.error(ex_tm)
            time.sleep(cycle_period)


def send_report_karatel_washcheck():
    values_tuple = get_karatel_not_sent_washcheck()
    for value in values_tuple:
        summ_balls = 0
        id_user, gosnomer, datetime_create, washcheck_id = value

        now = datetime.datetime.now()

        if now.day == datetime_create.day and now.month == datetime_create.month and now.year == datetime_create.year:

            values_tuple_checklist = get_karatel_washchecks_checklist_by_id_washcheck(washcheck_id)
            for value in values_tuple_checklist:
                id_element, result = value

                if result == 1:
                    balls = get_karatel_balls_from_element_by_id(id_element)[0][0]
                    summ_balls += balls

            set_karatel_washcheck_sent(washcheck_id)

            BOT.send_message(chat_id=id_user, text=f'Результат проверки чистоты автомобиля: {gosnomer} \n'
                                                   f'Баллы по этой машине: {summ_balls} \n'
                                                   f'Проверка по мойкам')


def send_report_karatel_outcheck():
    values_tuple = get_karatel_not_sent_outcheck()
    for value in values_tuple:
        summ_balls = 0

        id_user, gosnomer, datetime_create, outcheck_id = value

        now = datetime.datetime.now()

        if now.day == datetime_create.day and now.month == datetime_create.month and now.year == datetime_create.year:

            values_tuple_checklist = get_karatel_outcheck_checklist_by_id_outcheck(outcheck_id)
            for value in values_tuple_checklist:
                id_element, result = value

                if id_element == 1 and result == 1:
                    summ_balls += 10

                if id_element == 4 and result == 1:
                    summ_balls += 10

                if id_element == 12 and result == 1:
                    summ_balls += 10

                if id_element == 13 and result == 1:
                    summ_balls += 10

                if id_element == 14 and result == 1:
                    summ_balls += 10


            set_karatel_outcheck_sent(outcheck_id)

            BOT.send_message(chat_id=id_user, text=f'Результат проверки чистоты автомобиля: {gosnomer} \n'
                                                   f'Баллы по этой машине: {summ_balls} \n'
                                                   f'Проверка по выездам')


def send_reqs_tphelp_to_support():
    if is_smena_period_now_for_support():
        supports_on_smena_tuple = db.db_reqs.get_supports_on_smena()
        if len(supports_on_smena_tuple) > 1:
            db.db_reqs.update_tphelp_noreaction_reqs_for_repeat()

    tphelp_requests_list = db.db_reqs.get_tphelp_requests_for_support()
    for tphelp_request in tphelp_requests_list:
        req_tphelp, fio, city_name, gosnomer, commentary, media_tuple = tphelp_request
        support = get_required_support(id_user_exclude=req_tphelp.id_support)
        if not support:
            return
        id_support = support.id

        keyboard_inline = types.InlineKeyboardMarkup()
        keyboard_list = []
        media_list = []
        id_req_tphelp = req_tphelp.id

        mes = f'{city_name}\n{gosnomer if gosnomer else "без госномера"}\n{fio}\n\n{commentary}'

        keyboard_list.append(types.InlineKeyboardButton(text='Уведомление передано',
                                                        callback_data=f"menu_support_check_tphelp;{id_req_tphelp};1"))
        keyboard_list.append(types.InlineKeyboardButton(text='Ответить перегонщику',
                                                        callback_data=f"menu_support_check_tphelp;{id_req_tphelp};2"))

        keyboard_inline.add(*keyboard_list, row_width=1)

        mes_count = 0
        for media_item in media_tuple:
            media_list.append(types.InputMediaPhoto(media_item.file_id, caption=(mes if mes_count == 0 else None)))
            mes_count += 1

        try:
            BOT.send_media_group(id_support, media_list)
            BOT.send_message(id_support, 'Выберите ответ на запрос', reply_markup=keyboard_inline)
            db.db_reqs.mark_req_tphelp_sent_to_support(id_req_tphelp, id_support)
        except Exception as ex_blk:
            LOGGER.error(ex_blk)


def menu_support_check_tphelp(message, data):
    params = data.split(';')
    id_req_tphelp = int(params[1])
    status = int(params[2])
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_TPHELP_ID_REQ.name, intval=id_req_tphelp)

    if status == 1:  # Ответ "Уведомление передано"
        db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_TPHELP_COMMENTARY_ASK.name, textval='')
        menu_support_check_tphelp_save(message)
    elif status == 2:  # Ввести свой ответ перегонщику
        keyboard = make_keyboard()

        BOT.send_message(message.chat.id, 'Напишите сообщение для ответа водителю', reply_markup=keyboard)
        states.set_state(message.chat.id, st.S_MENU_SUPPORT_CHECK_TPHELP_COMMENTARY_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_SUPPORT_CHECK_TPHELP_COMMENTARY_ASK.value)
def menu_support_check_tphelp_commentary_save(message):
    commentary = message.text
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_TPHELP_COMMENTARY_ASK.name, textval=commentary)
    menu_support_check_tphelp_save(message)


def menu_support_check_tphelp_save(message):
    id_req_tphelp = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_TPHELP_ID_REQ.name).intval
    commentary = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_TPHELP_COMMENTARY_ASK.name).textval

    req_tphelp_item = db.db_reqs.get_tphelp_request(id_req_tphelp)
    if req_tphelp_item and req_tphelp_item.processed_by_support == 1:
        BOT.send_message(message.chat.id, 'Другой саппорт уже обработал этот запрос')
        mainmenu(message)
        return

    if db.db_reqs.set_req_tphelp_response(id_req_tphelp, commentary):
        if commentary:
            mes = 'Комментарий передан перегонщику'
        else:
            mes = 'Уведомление передано перегонщику'
        BOT.send_message(message.chat.id, mes)
        mainmenu(message)
    else:
        BOT.send_message(message.chat.id, 'Ошибка записи в базу')


def send_reqs_tphelp_responses_to_driver():
    tphelp_responses_list = db.db_reqs.get_req_tphelp_responses_for_workers()
    for tphelp_item in tphelp_responses_list:
        commentary = tphelp_item.commentary_from_support if tphelp_item.commentary_from_support else 'Уведомление передано'
        date_create = tphelp_item.date_create.strftime('%d.%m.%Y %H:%M')
        type_text = db.db_classifiers.find_classifier_object(TpHelpTypes, id=tphelp_item.id_tphelp_type).name

        mes = f'Ответ на обращение \"{type_text}\" от {date_create}:\n{commentary}'
        try:
            BOT.send_message(tphelp_item.id_user, mes)
        except Exception as ex_blk:
            LOGGER.error(ex_blk)
        db.db_reqs.mark_req_tphelp_response_sent_to_worker(tphelp_item.id)


def send_reqs_rpn_to_support():
    rpn_requests_list = db.db_reqs.get_rpn_requests_for_support()
    for rpn_request in rpn_requests_list:
        # id_support_preferred_rpn_pref_item = db.prefs.get_pref('id_support_preferred_rpn')
        # id_support_preferred_rpn = id_support_preferred_rpn_pref_item.intval if id_support_preferred_rpn_pref_item else None

        # id_support_exclude_rpn_pref_item = db.prefs.get_pref('id_support_exclude_rpn')
        # id_support_exclude_rpn = id_support_exclude_rpn_pref_item.intval if id_support_exclude_rpn_pref_item else None

        support = get_required_support()
        if not support:
            return
        id_support = support.id

        # следующая строка, это если они одному саппорту слать РПН будут хотеть, независимо от времени смены
        # id_support = id_support_preferred_rpn

        keyboard_inline = types.InlineKeyboardMarkup()
        keyboard_list = []
        media_list = []

        id_req_rpn, fio, wash_name, gosnomer, media_tuple_temperlist, media_tuple_workprocess = rpn_request

        mes = f'Отчёт РПН\n\n{wash_name}\n{gosnomer}\n{fio}'

        keyboard_list.append(types.InlineKeyboardButton(text='Подтвердить',
                                                        callback_data=f"menu_support_check_rpn;{id_req_rpn};1"))
        keyboard_list.append(types.InlineKeyboardButton(
            text='Отклонить', callback_data=f"menu_support_check_rpn;{id_req_rpn};2"))

        keyboard_inline.add(*keyboard_list, row_width=1)

        mes_count = 0
        for media_item in media_tuple_temperlist:
            media_list.append(types.InputMediaPhoto(media_item.file_id, caption=(mes if mes_count == 0 else None)))
            mes_count += 1
        for media_item in media_tuple_workprocess:
            media_list.append(types.InputMediaPhoto(media_item.file_id))

        try:
            BOT.send_media_group(id_support, media_list)
            BOT.send_message(id_support, 'Выберите ответ на запрос', reply_markup=keyboard_inline)
            db.db_reqs.mark_req_rpn_sent_to_support(id_req_rpn, id_support)
        except Exception as ex_blk:
            LOGGER.error(ex_blk)


def menu_support_check_rpn(message, data):
    params = data.split(';')
    id_req_rpn = int(params[1])
    status = int(params[2])
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_RPN_ID_REQ.name, intval=id_req_rpn)

    if status == 1:  # Ответ "Подтвердить"
        db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_RPN_DECISION.name, intval=1)
        menu_support_check_rpn_save(message)
    elif status == 2:  # Ответ "Отклонить"
        db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_RPN_DECISION.name, intval=0)
        keyboard = make_keyboard(row_width=2, fill_with_classifier=ReqRpnRefuseReason)
        req_rpn_item = db.db_reqs.get_rpn_request(id_req_rpn)
        gosnomer = req_rpn_item.gosnomer or 'нет госномера'

        BOT.send_message(
            message.chat.id, f'Фото по авто {gosnomer} отклонено. Выберите комментарий', reply_markup=keyboard)
        states.set_state(message.chat.id, st.S_MENU_SUPPORT_CHECK_RPN_REFUSE_REASON_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_SUPPORT_CHECK_RPN_REFUSE_REASON_ASK.value)
def menu_support_check_rpn_refuse_reason_save(message):
    choice = message.text
    refuse_reason_item = db.db_classifiers.find_classifier_object(ReqRpnRefuseReason, name=choice)
    if not refuse_reason_item:
        BOT.send_message(message.chat.id, 'Выберите один из вариантов')
        return

    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_RPN_REFUSE_REASON_ASK.name,
                              intval=refuse_reason_item.id)
    if refuse_reason_item.id == REQS_RPN_REFUSE_REASONS['other']:
        menu_support_check_rpn_commentary_ask(message)
    else:
        menu_support_check_rpn_save(message)


def menu_support_check_rpn_commentary_ask(message):
    keyboard = make_keyboard()
    mes = 'Напишите свой комментарий'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_SUPPORT_CHECK_RPN_COMMENTARY_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_SUPPORT_CHECK_RPN_COMMENTARY_ASK.value)
def menu_support_check_rpn_commentary_save(message):
    choice = message.text
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_RPN_COMMENTARY_ASK.name, textval=choice)
    menu_support_check_rpn_save(message)


def menu_support_check_rpn_save(message):
    id_req_rpn = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_RPN_ID_REQ.name).intval
    decision = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_RPN_DECISION.name).intval
    refuse_reason_item = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_RPN_REFUSE_REASON_ASK.name)
    id_refuse_reason = refuse_reason_item.intval if refuse_reason_item else None
    commentary_item = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_RPN_COMMENTARY_ASK.name)
    custom_refuse_reason = commentary_item.textval if commentary_item else None

    req_rpn_item = db.db_reqs.get_rpn_request(id_req_rpn)
    gosnomer = req_rpn_item.gosnomer or 'нет госномера'

    if req_rpn_item and req_rpn_item.processed_by_support == 1:
        BOT.send_message(message.chat.id, 'Другой саппорт уже обработал этот запрос')
        mainmenu(message)
        return

    if db.db_reqs.set_req_rpn_response(id_req_rpn, decision, id_refuse_reason, custom_refuse_reason):
        if id_refuse_reason == REQS_RPN_REFUSE_REASONS['other']:
            mes = 'Комментарий отправлен'
        else:
            mes = f'Фото по авто {gosnomer} принято'
        BOT.send_message(message.chat.id, mes)
        mainmenu(message)
    else:
        BOT.send_message(message.chat.id, 'Ошибка записи в базу')


def send_reqs_rpn_responses_to_driver():
    rpn_responses_list = db.db_reqs.get_req_rpn_responses_for_workers()
    for rpn_item in rpn_responses_list:
        mes = 'РПН\n'
        if rpn_item.id_refuse_reason:
            if rpn_item.id_refuse_reason == REQS_RPN_REFUSE_REASONS['other']:
                commentary = rpn_item.custom_refuse_reason
            else:
                refuse_reason_item = db.db_classifiers.find_classifier_object(
                    ReqRpnRefuseReason, id=rpn_item.id_refuse_reason)
                commentary = refuse_reason_item.name

            mes += f'Фото по автомобилю {rpn_item.gosnomer} отклонено.\nКомментарий от техподдержки: {commentary}\n\nИсправьте фото по данному авто'
        else:
            mes += f'Фото по автомобилю {rpn_item.gosnomer} принято'

        try:
            BOT.send_message(rpn_item.id_user, mes)
        except Exception as ex_blk:
            LOGGER.error(ex_blk)
        db.db_reqs.mark_req_rpn_response_sent_to_worker(rpn_item.id)


def send_reqs_kapot_to_support():
    if is_smena_period_now_for_support():
        supports_on_smena_tuple = db.db_reqs.get_supports_on_smena()
        if len(supports_on_smena_tuple) > 1:
            db.db_reqs.update_kapot_noreaction_reqs_for_repeat()

    kapot_requests_list = db.db_reqs.get_kapot_requests_for_support()
    for kapot_request in kapot_requests_list:
        req_kapot, fio, wash_name, gosnomer, media_tuple = kapot_request
        support = get_required_support(id_user_exclude=req_kapot.id_support)
        if not support:
            return
        id_support = support.id

        keyboard_inline = types.InlineKeyboardMarkup()
        keyboard_list = []
        media_list = []
        id_req_kapot = req_kapot.id

        mes = f'Отчёт по капоту Škoda Rapid\n\n{wash_name}\n{gosnomer}\n{fio}'

        keyboard_list.append(types.InlineKeyboardButton(text='Подтвердить',
                                                        callback_data=f"menu_support_check_kapot;{id_req_kapot};1"))
        keyboard_list.append(types.InlineKeyboardButton(
            text='Отклонить', callback_data=f"menu_support_check_kapot;{id_req_kapot};2"))

        keyboard_inline.add(*keyboard_list, row_width=1)

        mes_count = 0
        for media_item in media_tuple:
            media_list.append(types.InputMediaVideo(media_item.file_id, caption=(mes if mes_count == 0 else None)))
            mes_count += 1

        try:
            BOT.send_media_group(id_support, media_list)
            BOT.send_message(id_support, 'Выберите ответ на запрос', reply_markup=keyboard_inline)
            db.db_reqs.mark_req_kapot_sent_to_support(id_req_kapot, id_support)
        except Exception as ex_blk:
            LOGGER.error(ex_blk)


def menu_support_check_kapot(message, data):
    params = data.split(';')
    id_req_kapot = int(params[1])
    status = int(params[2])
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_KAPOT_ID_REQ.name, intval=id_req_kapot)

    if status == 1:  # Ответ "Подтвердить"
        db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_KAPOT_DECISION.name, intval=1)
        menu_support_check_kapot_save(message)
    elif status == 2:  # Ответ "Отклонить"
        db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_KAPOT_DECISION.name, intval=0)
        keyboard = make_keyboard(row_width=2, fill_with_classifier=ReqKapotRefuseReason)
        req_kapot_item = db.db_reqs.get_kapot_request(id_req_kapot)
        gosnomer = req_kapot_item.gosnomer or 'нет госномера'

        BOT.send_message(
            message.chat.id, f'Видео по авто {gosnomer} отклонено. Выберите комментарий', reply_markup=keyboard)
        states.set_state(message.chat.id, st.S_MENU_SUPPORT_CHECK_KAPOT_REFUSE_REASON_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_SUPPORT_CHECK_KAPOT_REFUSE_REASON_ASK.value)
def menu_support_check_kapot_refuse_reason_save(message):
    choice = message.text
    refuse_reason_item = db.db_classifiers.find_classifier_object(ReqKapotRefuseReason, name=choice)
    if not refuse_reason_item:
        BOT.send_message(message.chat.id, 'Выберите один из вариантов')
        return

    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_KAPOT_REFUSE_REASON_ASK.name,
                              intval=refuse_reason_item.id)
    if refuse_reason_item.id == REQS_KAPOT_REFUSE_REASONS['other']:
        menu_support_check_kapot_commentary_ask(message)
    else:
        menu_support_check_kapot_save(message)


def menu_support_check_kapot_commentary_ask(message):
    keyboard = make_keyboard()
    mes = 'Напишите свой комментарий'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_SUPPORT_CHECK_KAPOT_COMMENTARY_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_SUPPORT_CHECK_KAPOT_COMMENTARY_ASK.value)
def menu_support_check_kapot_commentary_save(message):
    choice = message.text
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_KAPOT_COMMENTARY_ASK.name, textval=choice)
    menu_support_check_kapot_save(message)


def menu_support_check_kapot_save(message):
    id_req_kapot = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_KAPOT_ID_REQ.name).intval
    decision = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_KAPOT_DECISION.name).intval
    refuse_reason_item = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_SUPPORT_CHECK_KAPOT_REFUSE_REASON_ASK.name)
    id_refuse_reason = refuse_reason_item.intval if refuse_reason_item else None
    commentary_item = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_KAPOT_COMMENTARY_ASK.name)
    custom_refuse_reason = commentary_item.textval if commentary_item else None

    req_kapot_item = db.db_reqs.get_kapot_request(id_req_kapot)
    gosnomer = req_kapot_item.gosnomer or 'нет госномера'

    if req_kapot_item and req_kapot_item.processed_by_support == 1:
        BOT.send_message(message.chat.id, 'Другой саппорт уже обработал этот запрос')
        mainmenu(message)
        return

    if db.db_reqs.set_req_kapot_response(id_req_kapot, decision, id_refuse_reason, custom_refuse_reason):
        if id_refuse_reason == REQS_KAPOT_REFUSE_REASONS['other']:
            mes = 'Комментарий отправлен'
        else:
            mes = f'Видео по авто {gosnomer} принято'
        BOT.send_message(message.chat.id, mes)
        mainmenu(message)
    else:
        BOT.send_message(message.chat.id, 'Ошибка записи в базу')


def send_reqs_kapot_responses_to_driver():
    kapot_responses_list = db.db_reqs.get_req_kapot_responses_for_workers()
    for kapot_item in kapot_responses_list:
        mes = 'Отчёт по капоту Škoda Rapid:\n'
        if kapot_item.id_refuse_reason:
            if kapot_item.id_refuse_reason == REQS_KAPOT_REFUSE_REASONS['other']:
                commentary = kapot_item.custom_refuse_reason
            else:
                refuse_reason_item = db.db_classifiers.find_classifier_object(
                    ReqKapotRefuseReason, id=kapot_item.id_refuse_reason)
                commentary = refuse_reason_item.name

            mes += f'Видео по автомобилю {kapot_item.gosnomer} отклонено.\nКомментарий от техподдержки: {commentary}\n\nИсправьте данное авто и пришлите новое видео'
        else:
            mes += f'Видео по автомобилю {kapot_item.gosnomer} принято'

        try:
            BOT.send_message(kapot_item.id_user, mes)
        except Exception as ex_blk:
            LOGGER.error(ex_blk)
        db.db_reqs.mark_req_kapot_response_sent_to_worker(kapot_item.id)


def send_reqs_dopusl_to_support():
    if is_smena_period_now_for_support():  # переотправку неотвеченных делаем только для ночных саппортов
        supports_on_smena_tuple = db.db_reqs.get_supports_on_smena()
        if len(supports_on_smena_tuple) > 1:
            db.db_reqs.update_dopusl_noreaction_reqs_for_repeat()

    dopusl_requests_list = db.db_reqs.get_dopusl_requests_for_support()
    for dopusl_request in dopusl_requests_list:
        req_dopusl, req_dopusl_dirty, fio, city_name, wash_name, dopusl_type_name, media_tuple, media_tuple_additional_dirty = dopusl_request
        id_support_dirty = req_dopusl_dirty.id_support if req_dopusl_dirty else None
        LOGGER.info(
            f'New DopUsl request {req_dopusl.id} gosnomer {req_dopusl.gosnomer} purity {req_dopusl.id_purity} id_support_dirty {id_support_dirty}')
        # если есть id_support, но пометка sent_to_support==0, значит этот саппорт не ответил на запрос, и нужно отправлять другому (если такой есть на смене)
        support = get_required_support(id_support_preferred=id_support_dirty, id_user_exclude=req_dopusl.id_support)
        if not support:
            return
        id_support = support.id

        keyboard_inline = types.InlineKeyboardMarkup()
        keyboard_list = []
        media_list = []
        id_req_dopusl = req_dopusl.id

        mes = 'Фото грязных элементов\n\n' if req_dopusl.id_purity == REQS_DOPUSL_PURITY[
            'dirty'] else 'Фото грязных+чистых элементов\n\n'
        mes += f'{city_name}\n{wash_name}\n{req_dopusl.gosnomer}\n{fio}\n{dopusl_type_name}\n'
        mes += f'Кол-во услуг: {req_dopusl.kol_elem}' if req_dopusl.id_dopusl_type == REQS_DOPUSL_TYPES['chem'] else ''

        keyboard_list.append(types.InlineKeyboardButton(text='Подтвердить',
                                                        callback_data=f"menu_support_check_dopusl;{id_req_dopusl};1"))
        keyboard_list.append(types.InlineKeyboardButton(
            text='Отклонить', callback_data=f"menu_support_check_dopusl;{id_req_dopusl};2"))

        keyboard_inline.add(*keyboard_list, row_width=1)

        mes_count = 0
        if media_tuple_additional_dirty:
            for media_item in media_tuple_additional_dirty:
                media_list.append(types.InputMediaPhoto(media_item.file_id, caption=(mes if mes_count == 0 else None)))
                mes_count += 1
        for media_item in media_tuple:
            media_list.append(types.InputMediaPhoto(media_item.file_id, caption=(mes if mes_count == 0 else None)))
            mes_count += 1
        try:
            BOT.send_media_group(id_support, media_list)
            BOT.send_message(id_support, 'Выберите ответ на запрос', reply_markup=keyboard_inline)
            db.db_reqs.mark_req_dopusl_sent_to_support(id_req_dopusl, id_support)
            db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['supports'], None)
            LOGGER.info(f'DopUsl request {req_dopusl.id} gosnomer {req_dopusl.gosnomer} sent to support {id_support}')
        except Exception as ex_blk:
            LOGGER.error(ex_blk)


def menu_support_check_dopusl(message, data):
    params = data.split(';')
    id_req_dopusl = int(params[1])
    status = int(params[2])
    req_dopusl = db.db_reqs.get_dopusl_request(id_req_dopusl)
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_DOPUSL_ID_REQ.name, intval=id_req_dopusl)

    if status == 1:  # Ответ "Подтвердить"
        db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_DOPUSL_DECISION.name, intval=1)
        menu_support_check_dopusl_save(message)
    elif status == 2:  # Ответ "Отклонить"
        db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_DOPUSL_DECISION.name, intval=0)
        keyboard = make_keyboard(row_width=2, fill_with_classifier=DopuslRefuseReason)
        gosnomer = req_dopusl.gosnomer or 'нет госномера'
        elem_purity_text = 'грязных' if req_dopusl.id_purity == REQS_DOPUSL_PURITY['dirty'] else 'чистых'

        BOT.send_message(
            message.chat.id, f'Фото {elem_purity_text} элементов по авто {gosnomer} отклонено. Выберите комментарий',
            reply_markup=keyboard)
        states.set_state(message.chat.id, st.S_MENU_SUPPORT_CHECK_DOPUSL_REFUSE_REASON_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(
    message.chat.id) == st.S_MENU_SUPPORT_CHECK_DOPUSL_REFUSE_REASON_ASK.value)
def menu_support_check_dopusl_refuse_reason_save(message):
    choice = message.text
    refuse_reason_item = db.db_classifiers.find_classifier_object(DopuslRefuseReason, name=choice)
    if not refuse_reason_item:
        BOT.send_message(message.chat.id, 'Выберите один из вариантов')
        return

    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_DOPUSL_REFUSE_REASON_ASK.name,
                              intval=refuse_reason_item.id)
    if refuse_reason_item.id == REQS_DOPUSL_REFUSE_REASONS['other']:
        menu_support_check_dopusl_commentary_ask(message)
    else:
        menu_support_check_dopusl_save(message)


def menu_support_check_dopusl_commentary_ask(message):
    keyboard = make_keyboard()
    mes = 'Напишите свой комментарий'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_SUPPORT_CHECK_DOPUSL_COMMENTARY_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_SUPPORT_CHECK_DOPUSL_COMMENTARY_ASK.value)
def menu_support_check_dopusl_commentary_save(message):
    choice = message.text
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_DOPUSL_COMMENTARY_ASK.name, textval=choice)
    menu_support_check_dopusl_save(message)


def menu_support_check_dopusl_save(message):
    id_req_dopusl = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_DOPUSL_ID_REQ.name).intval
    decision = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_DOPUSL_DECISION.name).intval
    refuse_reason_item = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_SUPPORT_CHECK_DOPUSL_REFUSE_REASON_ASK.name)
    id_refuse_reason = refuse_reason_item.intval if refuse_reason_item else None
    commentary_item = db.db_tempvals.get_tmpval(message.chat.id, st.S_MENU_SUPPORT_CHECK_DOPUSL_COMMENTARY_ASK.name)
    custom_refuse_reason = commentary_item.textval if commentary_item else None

    req_dopusl_item = db.db_reqs.get_dopusl_request(id_req_dopusl)
    gosnomer = req_dopusl_item.gosnomer or 'нет госномера'

    if req_dopusl_item and req_dopusl_item.processed_by_support == 1:
        BOT.send_message(message.chat.id, 'Другой саппорт уже обработал этот запрос')
        mainmenu(message)
        return

    if db.db_reqs.set_req_dopusl_response(id_req_dopusl, decision, id_refuse_reason, custom_refuse_reason):
        db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['supports'], None)
        BOT.send_message(message.chat.id, f'Комментарий по авто {gosnomer} отправлен')
        LOGGER.info(
            f'DopUsl {req_dopusl_item.id} gosnomer {req_dopusl_item.gosnomer} processed by support {message.chat.id}')
        mainmenu(message)
    else:
        BOT.send_message(message.chat.id, 'Ошибка записи в базу')


def send_reqs_dopusl_responses_to_driver():
    dopusl_responses_list = db.db_reqs.get_req_dopusl_responses_for_workers()
    for dopusl_item in dopusl_responses_list:
        dopusl_type_item = db.db_classifiers.find_classifier_object(DopuslTypes, id=dopusl_item.id_dopusl_type)
        dopusl_type_name = dopusl_type_item.name if dopusl_type_item else ""
        mes = f'Ответ по доп.услугам ({dopusl_type_name}):\n\n'
        gosnomer = dopusl_item.gosnomer
        # TODO как то тут всё понамешано

        if dopusl_item.id_refuse_reason:
            if dopusl_item.id_refuse_reason == REQS_DOPUSL_REFUSE_REASONS['other']:
                commentary = dopusl_item.custom_refuse_reason
            else:
                refuse_reason_item = db.db_classifiers.find_classifier_object(
                    DopuslRefuseReason, id=dopusl_item.id_refuse_reason)
                commentary = refuse_reason_item.name

        keyboard_inline = None

        if dopusl_item.id_purity == REQS_DOPUSL_PURITY['dirty']:
            if dopusl_item.id_refuse_reason:
                mes += f'Отклонены фотографии грязных элементов по автомобилю {gosnomer}\nКомментарий техподдержки: {commentary}'
            else:
                mes += f'Фото грязных элементов по авто {gosnomer} приняты'
                keyboard_inline = types.InlineKeyboardMarkup()
                keyboard_list = []
                keyboard_list.append(types.InlineKeyboardButton(text='Загрузить фото чистых элементов',
                                                                callback_data=f"menu_worker_dopusl_clean_photo_ask;{dopusl_item.id}"))
                keyboard_inline.add(*keyboard_list, row_width=1)
        else:
            if dopusl_item.id_refuse_reason:
                mes += f'Необходимо переделать фотографии чистых элементов по автомобилю {gosnomer}\nКомментарий техподдержки: {commentary}'
                keyboard_inline = types.InlineKeyboardMarkup()
                keyboard_list = []
                keyboard_list.append(types.InlineKeyboardButton(text='Загрузить фото чистых элементов',
                                                                callback_data=f"menu_worker_dopusl_clean_photo_ask;{dopusl_item.id_req_dirty}"))
                keyboard_inline.add(*keyboard_list, row_width=1)
            else:
                mes += f'Фото чистых элементов по авто {gosnomer} приняты'

        try:
            if keyboard_inline:
                BOT.send_message(dopusl_item.id_user, mes, reply_markup=keyboard_inline)
            else:
                BOT.send_message(dopusl_item.id_user, mes)
            LOGGER.info(f'DopUsl response by request {dopusl_item.id} gosnomer {dopusl_item.gosnomer} sent to driver')
        except Exception as ex_blk:
            LOGGER.error(ex_blk)
        db.db_reqs.mark_req_dopusl_response_sent_to_worker(dopusl_item.id)
        db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['supports'], None)
        # TODO после каждого телодвижения в сторону доп.услуг мы сейчас полностью перерисовываем таблицу отчёта
        # саппортов, вместе с листом про смены, который достаточно вообще раз в сутки. Как то это оптимизировать надо


def menu_worker_dopusl_clean_photo_ask(message, data):
    params = data.split(';')
    id_req_dopusl_dirty = int(params[1])
    req_dopusl_dirty_item = db.db_reqs.get_dopusl_request(id_req_dopusl_dirty)
    id_purity = REQS_DOPUSL_PURITY['clean']
    id_req_dopusl = db.db_reqs.create_empty_dopusl_request(message.chat.id, id_req_dopusl_dirty, id_purity,
                                                           req_dopusl_dirty_item.id_wash,
                                                           req_dopusl_dirty_item.gosnomer,
                                                           req_dopusl_dirty_item.id_dopusl_type,
                                                           req_dopusl_dirty_item.kol_elem)
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_CREATE_CLEAN.name, intval=id_req_dopusl)

    keyb_items = []
    row_width = 2
    keyb_items.append('Далее')
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)
    mes = 'Загрузите фотографию чистых элементов и нажмите Далее'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_CLEAN_PHOTO_ASK.value)


@BOT.message_handler(
    func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_WORKER_REQ_DOPUSL_CLEAN_PHOTO_ASK.value)
def menu_worker_dopusl_clean_photo_save(message):
    smena = db.db_smena.get_user_unfinished_smena(message.chat.id)
    id_smena = smena.id if smena else None
    id_req_dopusl = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_CREATE_CLEAN.name, is_delete_after_read=False).intval
    id_media_type = MEDIA_TYPES['dopusl_clean']
    media_tuple = db.db_media.get_media_tuple(message.chat.id, id_media_type,
                                              id_smena=id_smena, id_req_dopusl=id_req_dopusl)
    if message.photo:
        if media_tuple and len(media_tuple) > 3:
            BOT.send_message(message.chat.id, 'Уже достаточно фото!')
            return
        file_id = message.photo[-1].file_id
        db.db_media.save_media(message.chat.id, id_media_type, file_id, id_smena=id_smena, id_req_dopusl=id_req_dopusl)
        BOT.send_message(message.chat.id, 'Фото загружено')
    else:
        if message.text == 'Далее':
            if not media_tuple or len(media_tuple) == 0:
                BOT.send_message(message.chat.id, 'Вначале загрузи фотографии!')
                return
            menu_worker_dopusl_clean_save(message)


def menu_worker_dopusl_clean_save(message):
    id_req_dopusl = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_WORKER_REQ_DOPUSL_CREATE_CLEAN.name, is_delete_after_read=False).intval
    if db.db_reqs.update_dopusl_request_for_ready(id_req_dopusl):
        db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['supports'], None)
        BOT.send_message(message.chat.id, 'Ожидайте ответа от техподдержки. Обычно это занимает 2-3 минуты.')
        mainmenu(message)
    else:
        BOT.send_message(message.chat.id, 'Ошибка записи в базу')


def timer_smena():
    """Таймер начала смены"""
    LOGGER.info('Timer_smenastart thread started...')
    cycle_period = 60
    while True:
        try:
            today_datetime = datetime.datetime.now()
            if is_smena_evening_now():
                today_date = datetime.date.today()
                last_smenadate = db.db_smena.get_last_smenadate()
                if not last_smenadate or today_date > last_smenadate.date_smena:
                    db.db_smena.set_last_smenadate(today_date)
                    send_smena_start_notify()  # TODO как то проверять, всем ли юзерам дошло уведомление с кнопкой о начале смены
            elif not is_smena_period_now():
                db.db_smena.finish_smenadate()
                # TODO по-моему этот процесс тут каждую минуту идёт. Достаточно один раз вне времени смены, какой то флаг чтоли поднимать
                users_ids_list = db.db_smena.close_abandoned_smenas()
                if users_ids_list:
                    for id_user in users_ids_list:
                        try:
                            BOT.send_message(id_user, 'Смена завершена принудительно')
                        except Exception as ex_blk:
                            LOGGER.error(ex_blk)

                last_smenadate = db.db_smena.get_last_smenadate()

                all_opozd_users_lst = db.db_penalty.put_progul_penalties(last_smenadate.id)
                if all_opozd_users_lst:
                    for id_user in all_opozd_users_lst:
                        try:
                            BOT.send_message(
                                id_user,
                                f'Вам назначен штраф за прогул по смене {last_smenadate.date_smena.strftime("%d.%m.%Y")}')
                        except Exception as ex_blk:
                            LOGGER.error(ex_blk)

                    city_items = db.db_classifiers.get_classifier_items(City)
                    for city_item in city_items:
                        db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['schedules'], city_item.id)
                    db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['brig_schedules'], None)

            # TODO как то проверять, выгружены ли последущие отчёты, вдруг в это время прога не работала
            if today_datetime.hour == NIGHT_SMENA_END[0] + 1 and today_datetime.minute == 0:
                date_period_to_update = None
                # если сейчас первый день нового периода, то мы всё равно должны обновить отчёты по последнему дню предыдущего
                if today_datetime.day in (1, 11, 21):
                    date_period_to_update = datetime.date.today() - datetime.timedelta(days=1)
                for id_city in CITIES.values():
                    db.db_spreadsheets.mark_spreadsheet_need_update(
                        SPREADSHEET_TYPES['smena_results'], id_city, date_period_to_update)
                db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['auto_avg_kol_by_category'], None)

            time.sleep(cycle_period)
        except Exception as ex_tm:
            LOGGER.error(ex_tm)
            time.sleep(cycle_period)


def send_smena_start_notify():
    smenadate_item = db.db_smena.get_last_smenadate()
    smenadate_text = smenadate_item.date_smena.strftime('%Y-%m-%d')
    keyboard_inline = types.InlineKeyboardMarkup()
    keyboard_list = []
    keyboard_list.append(types.InlineKeyboardButton(text='Начать работу',
                                                    callback_data=f'smena_start;{smenadate_text}'))
    keyboard_inline.add(*keyboard_list, row_width=1)

    users_list = get_users_for_smena()
    for user in users_list:
        if user.id_role in (ROLES['worker'], ROLES['brigadir']):
            mes = 'Напоминаем, что сегодня по графику твоя смена. Нажми "Начать работу", как будешь готов приступить к перегону.'
        else:
            mes = 'Напоминаем, что сегодня по графику твоя смена. Нажми "Начать работу", как будешь готов приступить к работе.'
        try:
            BOT.send_message(user.id, mes, reply_markup=keyboard_inline)
        except Exception as ex_blk:
            LOGGER.error(ex_blk)
    db.db_smena.set_smena_notify_users(smenadate_item, users_list)


def get_users_for_smena():
    users_list = []
    users_ids_list = []
    cur_weekday = datetime.datetime.now().weekday()
    smenadate = db.db_smena.get_last_smenadate()
    sheds_tuple, users_tuple, dopsmena_tuple, otgul_tuple = db.db_smena.get_scheds_stuff(smenadate)
    for sched in sheds_tuple:
        if sched.week_template[cur_weekday:cur_weekday + 1] == '1':
            users_ids_list.append(sched.id_user)
    for otgul_item in otgul_tuple:
        if otgul_item.id_user in users_ids_list:
            users_ids_list.remove(otgul_item.id_user)
    for dopsmena_item in dopsmena_tuple:
        if dopsmena_item.id_user not in users_ids_list:
            users_ids_list.append(dopsmena_item.id_user)

    for user in users_tuple:
        if (user.id in users_ids_list) and (user.id not in users_list):  # TODO это максимально тупо и непродуктивно
            users_list.append(user)
    return users_list


def smena_start(message, data):
    params = data.split(';')
    smenadate_button_text = params[1]
    id_user = message.chat.id

    smenadate = db.db_smena.get_last_smenadate()
    if smenadate.date_smena.strftime('%Y-%m-%d') != smenadate_button_text:
        BOT.send_message(id_user, 'Устаревшая смена')
        mainmenu(message)
    else:
        cur_smena = db.db_smena.get_user_cur_opened_smena_by_date(id_user, smenadate)
        if cur_smena:
            BOT.send_message(id_user, 'Смена уже открыта')
        else:
            if db.db_smena.open_smena(id_user, smenadate):
                BOT.send_message(id_user, 'Смена начата')
                mainmenu(message)
            else:
                BOT.send_message(id_user, 'Ошибка начала смены')


def is_smena_period_now() -> bool:
    today_datetime = datetime.datetime.now()
    if (today_datetime.hour >= NIGHT_SMENA_START[0] or today_datetime.hour <= NIGHT_SMENA_END[0]) and (
            today_datetime.minute >= NIGHT_SMENA_START[1] or today_datetime.minute <= NIGHT_SMENA_END[1]):
        return True  # TODO проверка минут тут по сути не работает, пока период с 0 по 59 минут оно то норм, всё равно только на час смотрит
    else:
        return False


def is_smena_period_now_for_support() -> bool:
    today_datetime = datetime.datetime.now()
    if (today_datetime.hour == NIGHT_SMENA_SUPPORTCHECK_START[0] and today_datetime.minute >=
        NIGHT_SMENA_SUPPORTCHECK_START[1]) or today_datetime.hour > NIGHT_SMENA_SUPPORTCHECK_START[
        0] or today_datetime.hour < NIGHT_SMENA_SUPPORTCHECK_END[0] or (
            today_datetime.hour == NIGHT_SMENA_SUPPORTCHECK_END[0] and today_datetime.minute <=
            NIGHT_SMENA_SUPPORTCHECK_END[1]):
        return True
    else:
        return False


def is_smena_evening_now() -> bool:
    today_datetime = datetime.datetime.now()
    if today_datetime.hour >= NIGHT_SMENA_START[0] and today_datetime.minute >= NIGHT_SMENA_START[1]:
        return True
    else:
        return False


def get_period_dates(custom_date=None):  # TODO такой же метод есть в spreadsheets.py
    period_date = custom_date if custom_date else datetime.date.today()

    if 1 <= period_date.day <= 10:
        date_start = period_date.replace(day=1)
        date_end = period_date.replace(day=10)
    elif 11 <= period_date.day <= 20:
        date_start = period_date.replace(day=11)
        date_end = period_date.replace(day=20)
    elif period_date.day > 20:
        date_start = period_date.replace(day=21)
        date_end = datetime.date(period_date.year, period_date.month,
                                 calendar.monthrange(period_date.year, period_date.month)[1])
    return (date_start, date_end)


def get_period_dates_doublemonth(custom_date=None):
    period_date = custom_date if custom_date else datetime.date.today()

    if 1 <= period_date.day <= 15:
        date_start = period_date.replace(day=1)
        date_end = period_date.replace(day=15)
    else:
        date_start = period_date.replace(day=16)
        date_end = datetime.date(period_date.year, period_date.month,
                                 calendar.monthrange(period_date.year, period_date.month)[1])
    return (date_start, date_end)


def check_contragents_opl_periods_and_reestr():
    today_datetime = datetime.datetime.now()
    pref_item = db.db_prefs.get_pref('last_contragents_opl_periods_calculate')
    if not pref_item or today_datetime - datetime.timedelta(days=1) >= pref_item.datetimeval:
        today_date = datetime.date.today()
        last_period_item = db.db_contragents.get_last_contragents_opl_period()
        if not last_period_item.date_start <= today_date <= last_period_item.date_end:
            new_date_start, new_date_end = get_period_dates_doublemonth()
            db.db_contragents.set_last_contragents_opl_period(new_date_start, new_date_end)

        last_3_periods_items_tuple = db.db_contragents.get_last_3_contragents_opl_periods()
        for period_item in last_3_periods_items_tuple:
            db.db_contragents.check_and_create_opl_reestr_items(period_item.id)

        db.db_prefs.set_pref('last_contragents_opl_periods_calculate', datetimeval=today_datetime)


def get_required_support(id_support_preferred: int = None, id_user_exclude: int = None) -> User:
    if is_smena_period_now_for_support():
        support = db.db_reqs.get_random_support_on_smena(
            id_support_preferred=id_support_preferred, id_user_exclude=id_user_exclude)
    else:
        support = db.db_reqs.get_random_support_daily()
    return support


def timer_reports():
    """Таймер отчётности"""
    LOGGER.info('Timer_reports thread started...')
    cycle_period = 60
    while True:
        try:
            today_datetime = datetime.datetime.now()

            # TODO сделать проверку, отправлялся ли сегодня отчёт (вдруг в 10:00 бот был выключен)
            if today_datetime.hour == 10 and today_datetime.minute == 0:
                show_chatreport_major_smenaresults()
            if today_datetime.hour == 10 and today_datetime.minute == 30:
                show_chatreport_major_today_workers_kol()

            if today_datetime.hour == 0 and today_datetime.minute == 0:
                check_period_spreadsheets()

            if today_datetime.day > 25 and today_datetime.hour == 10 and today_datetime.minute == 30:
                update_schedules_report_nextmonth()

            if today_datetime.day == 1 and today_datetime.hour == 10 and today_datetime.minute == 0:
                LOGGER.info('supports table - updating prev month last day')
                date_period_to_update = datetime.date.today() - datetime.timedelta(days=1)
                db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['supports'], date_period_to_update)

            check_brig_schedules_exists()
            update_sheet_reports()  # TODO А там в реестре перегонщиков есть sql, который тянет данные из старой БД карателей, который выполняется несколько минут
            send_media_to_chats()  # TODO ТАК! СЮДА добавить асинхронности!!! Там внутри есть таймер, который может затормозить весь поток на себя

            time.sleep(cycle_period)
        except Exception as ex_tm:
            LOGGER.error(ex_tm)
            time.sleep(cycle_period)


def update_schedules_report_nextmonth():
    today_date = datetime.date.today()
    date_period_to_update = today_date + datetime.timedelta(days=7)
    city_items = db.db_classifiers.get_classifier_items(City)
    for city_item in city_items:
        db.db_spreadsheets.mark_spreadsheet_need_update(
            SPREADSHEET_TYPES['schedules'], city_item.id, date_period_to_update)


def check_brig_schedules_exists():
    """Проверка, есть ли у каждого из бригадиров (вдруг новый появится) личная таблица графиков по его подчинённым"""
    brigs_ids_tuple = db.db_users.get_brigadirs_ids_without_schedules_table()
    for id_brigadir in brigs_ids_tuple:
        if spreadsheets.create_blank_spreadsheet_by_type(None, SPREADSHEET_TYPES['brig_schedules'],
                                                         id_user=id_brigadir):
            LOGGER.info('Created new spreadsheet with type: brig_schedules for brigadir %s', id_brigadir)


def update_sheet_reports():
    sh_tuple = db.db_spreadsheets.get_spreadsheets_to_update()
    for sheet in sh_tuple:
        if spreadsheets.update_spreadsheet(sheet):
            db.db_spreadsheets.mark_spreadsheet_updated(sheet.id)


def send_media_to_chats():
    # Ситидрайв - отправка в канал фото грязных/чистых авто
    smenaservice_media_dirtyclean_lst = db.db_reports.get_smenaservice_media_dirtyclean_unsent()
    if smenaservice_media_dirtyclean_lst:
        channel_id = db.db_reports.get_service_chat('citydrive_photo').chat_id

        for smenaservice_item in smenaservice_media_dirtyclean_lst:
            gosnomer, date_create, fio, phone, wash_name, dirty_media_tuple, clean_media_tuple = smenaservice_item

            mes = f'{gosnomer}\n{date_create}\n{fio}\n{phone}\n{wash_name}'
            media_list_dirty = []
            media_list_clean = []
            updated_media_ids_lst = []

            mes_count = 0
            for media_item in clean_media_tuple:
                id_media, file_id = media_item
                media_list_clean.append(types.InputMediaPhoto(file_id, caption=(
                    f'<b>Чистое авто</b>\n\n{mes}' if mes_count == 0 else None), parse_mode='html'))
                updated_media_ids_lst.append(id_media)
                mes_count += 1
            mes_count = 0
            for media_item in dirty_media_tuple:
                id_media, file_id = media_item
                media_list_dirty.append(types.InputMediaPhoto(file_id, caption=(
                    f'<b>Грязное авто</b>\n\n{mes}' if mes_count == 0 else None), parse_mode='html'))
                updated_media_ids_lst.append(id_media)
                mes_count += 1

            try:
                if media_list_clean:
                    BOT.send_media_group(channel_id, media_list_clean)
                if media_list_dirty:
                    BOT.send_media_group(channel_id, media_list_dirty)
                db.db_media.mark_media_sent(updated_media_ids_lst)
                time.sleep(10)  # TODO ага, вот эти ребята
            except Exception as ex_blk:
                LOGGER.error(ex_blk)


def show_chatreport_major_smenaresults():
    chat_id = db.db_reports.get_service_chat('major').chat_id

    last_smenadate_item = db.db_smena.get_last_smenadate()
    datetime_start_text = last_smenadate_item.date_smena.strftime("%Y-%m-%d 10:00:00")
    datetime_end_text = (last_smenadate_item.date_smena + datetime.timedelta(days=1)).strftime("%Y-%m-%d 09:59:59")

    mes = f'<b>Отчёт за смену {last_smenadate_item.date_smena.strftime("%d.%m.%Y")}</b>\n\n'

    city_items = db.db_classifiers.get_classifier_items(City)
    for city_item in city_items:
        mes += f'{city_item.icon} <b>{city_item.name}</b>\n'
        # TODO там ещё расчёт залитых канистр был в старом боте, в зимнее время
        report_items = db.db_reports.get_chatreport_major_smenaresults(
            city_item.id, datetime_start_text, datetime_end_text, last_smenadate_item)
        kol_rab, kol_rab_dn, kol_rab_new, kol_auto, kol_auto_dn, kol_auto_new, kol_rab_lost = report_items
        car_leftover_item = db.db_smena.get_car_leftover(city_item.id, last_smenadate_item.id)
        leftovers_percent = 'не введён'
        if car_leftover_item:
            if kol_auto + car_leftover_item.kol_leftover > 0:
                leftovers_percent = round(car_leftover_item.kol_leftover * 100 /
                                          (kol_auto + car_leftover_item.kol_leftover))
                leftovers_percent = f'{leftovers_percent}%'
            else:
                leftovers_percent = '0%'
        kol_rab_all = kol_rab + kol_rab_dn + kol_rab_new
        kol_auto_all = kol_auto + kol_auto_dn + kol_auto_new
        kol_auto_average = round(kol_auto_all / kol_rab_all, 1) if kol_rab_all > 0 else 0

        mes += f'Исполнителей: {kol_rab}\n'
        mes += f'Исполнителей (дневн.): {kol_rab_dn}\n'
        mes += f'Исполнителей (новички): {kol_rab_new}\n'
        mes += f'Исполнителей (всего): {kol_rab_all}\n\n'
        mes += f'Авто: {kol_auto}\n'
        mes += f'Авто (дневн.): {kol_auto_dn}\n'
        mes += f'Авто (новички): {kol_auto_new}\n'
        mes += f'Авто (всего): {kol_auto_all}\n\n'
        mes += f'Среднее (авто): {kol_auto_average}\n'
        mes += f'Остаток: {leftovers_percent}\n'
        mes += f'Потери: {kol_rab_lost}\n\n'

        db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['schedules'], city_item.id)
    db.db_spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['brig_schedules'], None)

    BOT.send_message(chat_id, mes, parse_mode='html')


def show_chatreport_major_today_workers_kol():
    chat_id = db.db_reports.get_service_chat('major').chat_id
    today_date = datetime.date.today()
    is_has_data = False

    mes = f'<b>Смена {today_date.strftime("%d.%m.%Y")}</b>\n\n'

    city_items = db.db_classifiers.get_classifier_items(City)
    for city_item in city_items:
        mes += f'{city_item.icon} <b>{city_item.name}</b>\n'

        workers_count_item = db.db_smena.get_workers_count(today_date, city_item.id)
        if workers_count_item:
            mes += f'По графику на текущий момент: {workers_count_item.kol} чел.\n\n'
            is_has_data = True
        else:
            mes += 'Нет работников по графику\n\n'

    if is_has_data:
        BOT.send_message(chat_id, mes, parse_mode='html')


@BOT.message_handler(content_types=['text'])
def dummy_message(message):
    """Любая другая текстовая команда"""
    cmd_start(message)


def get_prev_and_curr_month_dates():
    date_today = datetime.date.today()
    date_last_day_prev_month = date_today.replace(day=1) - datetime.timedelta(days=1)
    return (date_last_day_prev_month.strftime("%Y-%m"), date_today.strftime("%Y-%m"))


def list_to_chunks(lst, size):
    return [lst[i * size:(i + 1) * size] for i in range((len(lst) + size - 1) // size)]


def startup_actions():
    """Стартовые действия"""
    check_unloaded_resources()
    check_nonperiod_spreadsheets()
    check_period_spreadsheets()  # это выполняется ещё периодически, раз в сутки


def check_unloaded_resources():
    res_tuple = db.db_resources.get_unloaded_resources()
    if res_tuple:
        LOGGER.error('There are some unloaded resources. Please, exec command /cmd_fda77e8e323a_update_resources')


def check_nonperiod_spreadsheets():
    city_items = db.db_classifiers.get_classifier_items(City)
    for city in city_items:  # TODO сегодня сказали что это нужно вчера, поэтому говнокод
        sh1 = db.db_spreadsheets.get_spreadsheet(city.id, SPREADSHEET_TYPES['schedules'])
        if not sh1:
            if spreadsheets.create_blank_spreadsheet_by_type(city, SPREADSHEET_TYPES['schedules']):
                LOGGER.info('Created new spreadsheet with type: schedules')
        sh2 = db.db_spreadsheets.get_spreadsheet(city.id, SPREADSHEET_TYPES['smena_results'])
        if not sh2:
            if spreadsheets.create_blank_spreadsheet_by_type(city, SPREADSHEET_TYPES['smena_results']):
                LOGGER.info('Created new spreadsheet with type: smena_results')


def check_period_spreadsheets():
    # TODO создание таблиц, общих для всех городов - тут заменить все введённые вручную табл на автозаполнение
    period_text = datetime.date.today().strftime("%Y-%m")

    sheet_payment_registry = db.db_spreadsheets.get_spreadsheet(
        None, SPREADSHEET_TYPES['payment_registry'], period=period_text)
    if not sheet_payment_registry:
        if spreadsheets.create_blank_spreadsheet_by_type(None, SPREADSHEET_TYPES['payment_registry'],
                                                         period=period_text):
            LOGGER.info('Created new spreadsheet with type: payment_registry')

    sheet_supports = db.db_spreadsheets.get_spreadsheet(None, SPREADSHEET_TYPES['supports'])
    if not sheet_supports:
        if spreadsheets.create_blank_spreadsheet_by_type(None, SPREADSHEET_TYPES['supports']):
            LOGGER.info('Created new spreadsheet with type: supports')

    sheet_auto_avg = db.db_spreadsheets.get_spreadsheet(None, SPREADSHEET_TYPES['auto_avg_kol_by_category'])
    if not sheet_auto_avg:
        if spreadsheets.create_blank_spreadsheet_by_type(None, SPREADSHEET_TYPES['auto_avg_kol_by_category']):
            LOGGER.info('Created new spreadsheet with type: auto_avg_kol_by_category')


if __name__ == '__main__':
    startup_actions()

    TIMER_1MIN_THREAD = threading.Thread(target=timer_1min)
    TIMER_1MIN_THREAD.daemon = True
    TIMER_1MIN_THREAD.start()

    TIMER_5MIN_THREAD = threading.Thread(target=timer_5min)
    TIMER_5MIN_THREAD.daemon = True
    TIMER_5MIN_THREAD.start()

    TIMER_SMENA_THREAD = threading.Thread(target=timer_smena)
    TIMER_SMENA_THREAD.daemon = True
    TIMER_SMENA_THREAD.start()

    TIMER_REPORTS_THREAD = threading.Thread(target=timer_reports)
    TIMER_REPORTS_THREAD.daemon = True
    TIMER_REPORTS_THREAD.start()

    try:
        BOT.infinity_polling()
    except Exception as ex:
        LOGGER.error(ex)
        sys.exit()
