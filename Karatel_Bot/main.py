#!venv/bin/python
"""Main module"""

import logging
import logging.handlers as loghandlers
import os
import re
import sys
import threading
import time

import telebot
from telebot import types

import config
import db
import spreadsheets
from outcheck_cloud import get_cloud_outcheck_folder_id
from outcheck_cloud import save_outcheck_photo_to_cloud
import states
from models.reports import (SPREADSHEET_TYPES, SPREADSHEET_TYPES_CAPTIONS,
                            SpreadsheetType)
from models.service import MEDIA_FORMATS, MEDIA_TYPES
from models.users import ROLES, City
from states import States as st

BOT = telebot.TeleBot(config.TOKEN_BOT)

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
    """При команде Отмена из любого места возвращает в главное меню"""
    cmd_start(message)


@BOT.callback_query_handler(func=lambda call: True)
def inline_buttons_router(call):
    """Роутер для инлайновых кнопок"""
    if call.message:
        key = call.data.split(';')[0]
        is_del_inline_keyb = True

        # if key == 'menu_karatel_carcheck_problems':
        #     menu_karatel_carcheck_problems_save(call.id, call.message, call.data)
        #     is_del_inline_keyb = False

        if is_del_inline_keyb:
            BOT.edit_message_reply_markup(chat_id=call.message.chat.id,
                                          message_id=call.message.id, reply_markup=types.InlineKeyboardMarkup())


@BOT.message_handler(content_types=['photo'])
def photo_router(message):
    """Роутер для сообщений с фото"""
    if states.get_cur_state(message.chat.id) == st.S_MENU_KARATEL_OUTCHECK_PHOTOELEMENTS_ASK.value:
        menu_karatel_outcheck_photo_save(message)


@BOT.message_handler(content_types=['video'])
def video_router(message):
    """Роутер для сообщений с видео"""
    pass
    # if states.get_cur_state(message.chat.id) == st.S_MENU_KARATEL_CARCHECK_MEDIA_ASK.value:
    #     menu_karatel_carcheck_media_save(message)


@BOT.message_handler(commands=['start'])
def cmd_start(message):
    """Старт диалога с ботом"""
    if message.chat.id < 0:  # чтобы бот не отвечал, если он состоит в группе и его кто-то упомянет
        return
    user = db.users.get_user(message.chat.id)
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
    db.tempvals.clear_user_tempvals(message.chat.id)
    BOT.send_message(message.chat.id, 'Добро пожаловать в бот! Приступим к регистрации.')
    menu_reg_city_ask(message)


def menu_reg_city_ask(message):
    """Регистрация - выбор города"""
    keyboard = make_keyboard(row_width=2, fill_with_classifier=City)
    mes = 'Выберите ваш город'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_REG_ASK_CITY.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_REG_ASK_CITY.value)
def menu_reg_city_save(message):
    """Регистрация - сохранение города"""
    choice = message.text
    city = db.classifiers.find_classifier_object(City, name_object=choice)
    if not city:
        BOT.send_message(message.chat.id, 'Нет такого города')
        return
    db.tempvals.set_tmpval(message.chat.id, st.S_REG_ASK_CITY.name, intval=city.id)
    menu_reg_fam_ask(message)


def menu_reg_fam_ask(message):
    """Регистрация - запрос фамилии"""
    keyboard = make_keyboard()
    mes = 'Напишите вашу фамилию'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_REG_ASK_FAM.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_REG_ASK_FAM.value)
def menu_reg_fam_save(message):
    """Регистрация - сохранение фамилии"""
    fam = message.text
    if len(fam) > 100:
        BOT.send_message(message.chat.id, 'Слишком длинная фамилия')
        return
    if not fam.replace(' ', '').isalpha():
        BOT.send_message(message.chat.id, 'Недопустимые символы в фамилии')
        return
    db.tempvals.set_tmpval(message.chat.id, st.S_REG_ASK_FAM.name, textval=fam)
    menu_reg_im_ask(message)


def menu_reg_im_ask(message):
    """Регистрация - запрос имени"""
    keyboard = make_keyboard()
    mes = 'Напишите ваше имя'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_REG_ASK_IM.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_REG_ASK_IM.value)
def menu_reg_im_save(message):
    """Регистрация - сохранение имени"""
    im = message.text
    if len(im) > 100:
        BOT.send_message(message.chat.id, 'Слишком длинное имя')
        return
    if not im.replace(' ', '').isalpha():
        BOT.send_message(message.chat.id, 'Недопустимые символы в имени')
        return
    db.tempvals.set_tmpval(message.chat.id, st.S_REG_ASK_IM.name, textval=im)
    menu_reg_save(message)


def menu_reg_save(message):
    """Сохранение регистрации"""
    id_user = message.chat.id
    id_city = db.tempvals.get_tmpval(id_user, st.S_REG_ASK_CITY.name).intval
    fam = db.tempvals.get_tmpval(id_user, st.S_REG_ASK_FAM.name).textval
    im = db.tempvals.get_tmpval(id_user, st.S_REG_ASK_IM.name).textval
    nick = message.chat.username

    city = db.classifiers.find_classifier_object(City, id_object=id_city)

    if db.users.add_new_user(id_user, id_city, fam, im, nick):
        BOT.send_message(message.chat.id, 'Регистрация прошла успешно')

        admins_tuple = db.users.get_admins()
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
    """Ожидание подтверждения регистрации"""
    user = db.users.get_user(message.chat.id)
    if user and user.id_role != ROLES['pending']:
        cmd_start(message)
    else:
        keyb_items = ['Обновить']
        keyboard = make_keyboard(items=keyb_items, is_with_cancel=False)
        mes = 'Ожидайте подтверждения регистрации. Обычно она занимает 15 минут.\nДля проверки статуса нажмите кнопку Обновить'
        BOT.send_message(message.chat.id, mes, reply_markup=keyboard)


def mainmenu(message):
    """Главное меню"""
    db.tempvals.clear_user_tempvals(message.chat.id)
    user = db.users.get_user(message.chat.id)
    keyb_items = []
    row_width = 1

    if user.id_role == ROLES['admin']:
        # keyb_items.append('Управление пользователями')
        keyb_items.append('Отчёты')
        row_width = 2

    elif user.id_role == ROLES['karatel']:
        # keyb_items.append('Проверка авто')
        keyb_items.append('Проверка мойки')
        keyb_items.append('Проверка выездная')
        row_width = 2

    keyboard = make_keyboard(items=keyb_items, row_width=row_width, is_with_cancel=False)
    mes = 'Вы в главном меню'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MAINMENU.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_MAINMENU.value)
def mainmenu_choice(message):
    """Обработка нажатия в главном меню"""
    choice = message.text
    user = db.users.get_user(message.chat.id)

    if user.id_role == ROLES['admin']:
        if choice == 'Управление пользователями':
            menu_admin_usersmanage(message)
        elif choice == 'Отчёты':
            menu_admin_showlinks_reports(message)
        else:
            mainmenu(message)
    elif user.id_role == ROLES['karatel']:
        if choice == 'Проверка мойки':
            menu_karatel_washcheck(message)
        elif choice == 'Проверка выездная':
            menu_karatel_outcheck(message)
        else:
            mainmenu(message)


def menu_admin_usersmanage(message):
    # TODO
    mainmenu(message)


def menu_admin_showlinks_reports(message):
    mes = '<b>Отчёты:</b>\n'
    sheet_item_checklist_avg = db.spreadsheets.get_spreadsheet(SPREADSHEET_TYPES['checklist_avg'])
    if sheet_item_checklist_avg:
        hyperlink = f'https://docs.google.com/spreadsheets/d/{sheet_item_checklist_avg.id_drive}/edit#gid=1'
        mes += f'{SPREADSHEET_TYPES_CAPTIONS[SPREADSHEET_TYPES["checklist_avg"]]}: {hyperlink}\n'
        mes += '\n'

    sheet_item_check_report = db.spreadsheets.get_spreadsheet(SPREADSHEET_TYPES['check_report'])
    if sheet_item_check_report:
        hyperlink = f'https://docs.google.com/spreadsheets/d/{sheet_item_check_report.id_drive}/edit#gid=1'
        mes += f'{SPREADSHEET_TYPES_CAPTIONS[SPREADSHEET_TYPES["check_report"]]}: {hyperlink}\n'
        mes += '\n'

    BOT.send_message(message.chat.id, mes, parse_mode='html', disable_web_page_preview=True)


def menu_karatel_washcheck(message):
    menu_karatel_washcheck_wash_ask(message)


def menu_karatel_outcheck(message):
    menu_karatel_outcheck_gosnomer_ask(message)


def menu_karatel_washcheck_wash_ask(message):
    keyb_items = []
    washes_tuple = db.workprocess.get_washcheck_washes()
    if not washes_tuple:
        BOT.send_message(message.chat.id, 'Нет доступных моек')
        return
    for washes_item in washes_tuple:
        name_wash = washes_item[1]
        keyb_items.append(name_wash)

    keyboard = make_keyboard(items=keyb_items, row_width=2)
    mes = 'Выберите мойку для проверки'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_KARATEL_WASHCHECK_WASH_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_KARATEL_WASHCHECK_WASH_ASK.value)
def menu_karatel_washcheck_wash_save(message):
    choice = message.text
    id_wash = db.workprocess.get_washcheck_wash_by_name(choice)

    if not id_wash:
        BOT.send_message(message.chat.id, 'Нет такой мойки')
        return

    db.tempvals.set_tmpval(message.chat.id, st.S_MENU_KARATEL_WASHCHECK_WASH_ASK.name, intval=id_wash, textval=choice)
    menu_karatel_washcheck_gosnomer_ask(message)


def menu_karatel_washcheck_gosnomer_ask(message):
    keyboard = make_keyboard()
    mes = 'Введите госномер автомобиля русскими буквами по примеру А777АА799'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_KARATEL_WASHCHECK_GOSNOMER_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_KARATEL_WASHCHECK_GOSNOMER_ASK.value)
def menu_karatel_washcheck_gosnomer_save(message):
    gosnomer = message.text.upper()
    if len(gosnomer) != 9:
        BOT.send_message(message.chat.id, 'Госномер должен содержать 9 символов')
        return
    if bool(re.search('[a-zA-Z]', gosnomer)):
        BOT.send_message(message.chat.id, 'Госномер должен быть написан русскими буквами')
        return

    id_wash = db.tempvals.get_tmpval(
        message.chat.id, st.S_MENU_KARATEL_WASHCHECK_WASH_ASK.name, is_delete_after_read=False).intval
    id_washcheck = db.workprocess.create_new_washcheck(message.chat.id, id_wash, gosnomer)

    db.tempvals.set_tmpval(message.chat.id, 'cur_washcheck_id', intval=id_washcheck)
    menu_karatel_washcheck_elements_ask(message)


def menu_karatel_washcheck_elements_ask(message):
    exclude_elements_item = db.tempvals.get_tmpval(
        message.chat.id, 'cur_washcheck_checked_elements', is_delete_after_read=False)
    exclude_elements_str = exclude_elements_item.textval if exclude_elements_item else None
    exclude_elements_lst = [x for x in exclude_elements_str.split(";") if x] if exclude_elements_str else []

    elements_tuple = db.workprocess.get_washcheck_elements(exclude_elements_lst)
    if not elements_tuple:
        menu_karatel_washcheck_save(message)
        return

    keyb_items = []
    keyb_items.append('Да')
    keyb_items.append('Нет')
    keyboard = make_keyboard(items=keyb_items, row_width=2)

    washcheck_element_item = elements_tuple[0]
    db.tempvals.set_tmpval(message.chat.id, 'cur_washcheck_element_id', intval=washcheck_element_item.id)

    mes = f'Выполняется ли услуга \"{washcheck_element_item.name}\"?'
    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_KARATEL_WASHCHECK_ELEMENTS_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_KARATEL_WASHCHECK_ELEMENTS_ASK.value)
def menu_karatel_washcheck_elements_save(message):
    choice = message.text
    id_washcheck_element = db.tempvals.get_tmpval(
        message.chat.id, 'cur_washcheck_element_id', is_delete_after_read=False).intval

    if choice == 'Да':
        result = 1
    elif choice == 'Нет':
        result = 0
    else:
        BOT.send_message(message.chat.id, 'Неправильный выбор')
        return

    db.tempvals.set_tmpval(message.chat.id, f'washcheck_element_{id_washcheck_element}_result', intval=result)

    exclude_elements_item = db.tempvals.get_tmpval(
        message.chat.id, 'cur_washcheck_checked_elements', is_delete_after_read=False)
    exclude_elements_str = exclude_elements_item.textval if exclude_elements_item else ''
    exclude_elements_str += f'{id_washcheck_element};'
    db.tempvals.set_tmpval(message.chat.id, 'cur_washcheck_checked_elements', textval=exclude_elements_str)

    menu_karatel_washcheck_elements_ask(message)


def menu_karatel_washcheck_save(message):
    id_washcheck = db.tempvals.get_tmpval(message.chat.id, 'cur_washcheck_id', is_delete_after_read=False).intval
    washcheck_elements_results_lst = []

    elements_tuple = db.workprocess.get_washcheck_elements([])
    for elements_item in elements_tuple:
        washcheck_element_result = db.tempvals.get_tmpval(
            message.chat.id, f'washcheck_element_{elements_item.id}_result', is_delete_after_read=False).intval
        washcheck_elements_results_lst.append((elements_item.id, washcheck_element_result))

    if db.workprocess.save_washcheck_elements(id_washcheck, washcheck_elements_results_lst):
        # TODO таблицу такого плана лучше через таймер периодически разв минуту проверять и обновлять (смотреть в БД, есть ли неотправленные)
        db.spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['check_report'])
        BOT.send_message(message.chat.id, 'Данные записаны')
        mainmenu(message)
    else:
        BOT.send_message(message.chat.id, 'Ошибка сохранения в базу')


def menu_karatel_outcheck_gosnomer_ask(message):
    keyboard = make_keyboard()
    mes = 'Введите госномер автомобиля русскими буквами по примеру А777АА799'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_KARATEL_OUTCHECK_GOSNOMER_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_KARATEL_OUTCHECK_GOSNOMER_ASK.value)
def menu_karatel_outcheck_gosnomer_save(message):
    gosnomer = message.text.upper()
    if len(gosnomer) != 9:
        BOT.send_message(message.chat.id, 'Госномер должен содержать 9 символов')
        return
    if bool(re.search('[a-zA-Z]', gosnomer)):
        BOT.send_message(message.chat.id, 'Госномер должен быть написан русскими буквами')
        return

    id_outcheck = db.workprocess.create_new_outcheck(message.chat.id, gosnomer)
    db.tempvals.set_tmpval(message.chat.id, 'cur_outcheck_id', intval=id_outcheck)

    menu_karatel_outcheck_elements_ask(message)


def menu_karatel_outcheck_elements_ask(message):
    exclude_elements_item = db.tempvals.get_tmpval(
        message.chat.id, 'cur_check_checked_elements', is_delete_after_read=False)
    exclude_elements_str = exclude_elements_item.textval if exclude_elements_item else None
    exclude_elements_lst = [x for x in exclude_elements_str.split(";") if x] if exclude_elements_str else []

    elements_tuple = db.workprocess.get_washcheck_elements(exclude_elements_lst)
    if not elements_tuple:
        menu_karatel_outcheck_save(message)
        return

    keyb_items = []
    keyb_items.append('Да')
    keyb_items.append('Нет')
    keyboard = make_keyboard(items=keyb_items, row_width=2)

    element_item = elements_tuple[0]
    db.tempvals.set_tmpval(message.chat.id, 'cur_check_element_id', intval=element_item.id, textval=element_item.name)

    mes = f'Выполняется ли услуга \"{element_item.name}\"?'
    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_KARATEL_OUTCHECK_ELEMENTS_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_KARATEL_OUTCHECK_ELEMENTS_ASK.value)
def menu_karatel_outcheck_elements_save(message):
    choice = message.text
    id_element = db.tempvals.get_tmpval(message.chat.id, 'cur_check_element_id', is_delete_after_read=False).intval

    if choice == 'Да':
        result = 1
    elif choice == 'Нет':
        result = 0
    else:
        BOT.send_message(message.chat.id, 'Неправильный выбор')
        return

    db.tempvals.set_tmpval(message.chat.id, f'check_element_{id_element}_result', intval=result)

    exclude_elements_item = db.tempvals.get_tmpval(
        message.chat.id, 'cur_check_checked_elements', is_delete_after_read=False)
    exclude_elements_str = exclude_elements_item.textval if exclude_elements_item else ''
    exclude_elements_str += f'{id_element};'
    db.tempvals.set_tmpval(message.chat.id, 'cur_check_checked_elements', textval=exclude_elements_str)

    menu_karatel_outcheck_photo_ask(message)


def menu_karatel_outcheck_photo_ask(message):
    keyb_items = []
    row_width = 2
    keyb_items.append('Далее')
    keyboard = make_keyboard(items=keyb_items, row_width=row_width)

    element_item = db.tempvals.get_tmpval(message.chat.id, 'cur_check_element_id', is_delete_after_read=False)
    name_element = element_item.textval
    mes = f'Загрузите одно фото элемента \"{name_element}\", и нажмите Далее'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_KARATEL_OUTCHECK_PHOTOELEMENTS_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_KARATEL_OUTCHECK_PHOTOELEMENTS_ASK.value)
def menu_karatel_outcheck_photo_save(message):
    id_media_format = MEDIA_FORMATS['photo']
    id_media_type = MEDIA_TYPES['outcheck']
    id_outcheck = db.tempvals.get_tmpval(message.chat.id, 'cur_outcheck_id', is_delete_after_read=False).intval
    element_item = db.tempvals.get_tmpval(message.chat.id, 'cur_check_element_id', is_delete_after_read=False)
    id_element = element_item.intval
    media_tuple = db.media.get_media_tuple(message.chat.id, id_media_type,
                                           id_outcheck=id_outcheck, id_washcheck_element=id_element)
    if message.photo:
        if media_tuple and len(media_tuple) >= 1:
            BOT.send_message(message.chat.id, 'Уже достаточно фото!')
            return
        file_id = message.photo[-1].file_id
        file_info = BOT.get_file(file_id)

        downloaded_file = BOT.download_file(file_info.file_path)
        file_extension = file_info.file_path.split(".")[-1]
        file_name = f'{file_info.file_unique_id}.{file_extension}'

        pref_item = db.prefs.get_pref('cloud_folder_photos_checked_cars')
        root_cloud_folder_id = pref_item and pref_item.textval

        cloud_folder_id = get_cloud_outcheck_folder_id(root_cloud_folder_id, id_outcheck)
        cloud_file_id = save_outcheck_photo_to_cloud(downloaded_file, file_name, cloud_folder_id)

        db.media.save_media(
            message.chat.id,
            id_media_format,
            id_media_type,
            file_id,
            cloud_file_id,
            id_outcheck=id_outcheck,
            id_washcheck_element=id_element
        )
        BOT.send_message(message.chat.id, 'Фото загружено')
    else:
        if message.text == 'Далее':
            if not media_tuple or len(media_tuple) == 0:
                BOT.send_message(message.chat.id, 'Вначале загрузите фото!')
                return
            menu_karatel_outcheck_elements_ask(message)


def menu_karatel_outcheck_save(message):
    id_outcheck = db.tempvals.get_tmpval(message.chat.id, 'cur_outcheck_id', is_delete_after_read=False).intval
    elements_results_lst = []

    elements_tuple = db.workprocess.get_washcheck_elements([])
    for elements_item in elements_tuple:
        check_element_result = db.tempvals.get_tmpval(
            message.chat.id, f'check_element_{elements_item.id}_result', is_delete_after_read=False).intval
        elements_results_lst.append((elements_item.id, check_element_result))

    if db.workprocess.save_outcheck_elements(id_outcheck, elements_results_lst):
        db.spreadsheets.mark_spreadsheet_need_update(SPREADSHEET_TYPES['check_report'])
        BOT.send_message(message.chat.id, 'Данные записаны')
        mainmenu(message)
    else:
        BOT.send_message(message.chat.id, 'Ошибка сохранения в базу')


@BOT.message_handler(content_types=['text'])
def dummy_message(message):
    """Любая другая текстовая команда"""
    cmd_start(message)


def make_keyboard(items=None, row_width=1, fill_with_classifier=None, is_classifier_reverse=False, is_with_cancel=True):
    """Создание обычной клавиатуры с параметрами"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard_list = []

    if fill_with_classifier:
        classifier_items = db.classifiers.get_classifier_items(fill_with_classifier, is_reverse=is_classifier_reverse)
        for item in classifier_items:
            keyboard_list.append(item.name)

    if items:
        for item in items:
            keyboard_list.append(item)

    if is_with_cancel:
        keyboard_list.append('Отмена')

    if not items and not fill_with_classifier and not is_with_cancel:
        return types.ReplyKeyboardRemove()

    keyboard.add(*keyboard_list, row_width=row_width)
    return keyboard


def startup_actions():
    """Стартовые действия"""
    check_spreadsheets()


def check_spreadsheets():
    spreadsheets_types = db.classifiers.get_classifier_items(SpreadsheetType)
    for spreadsheet_type_item in spreadsheets_types:
        # TODO таблица без периода и города, поэтому так просто, для более сложных таблиц дополнить
        if not db.spreadsheets.get_spreadsheet(spreadsheet_type_item.id):
            if spreadsheets.create_blank_spreadsheet_by_type(spreadsheet_type_item.id):
                LOGGER.info('Created new spreadsheet with type: %s' % spreadsheet_type_item.name)


def timer_1min():
    """Таймер выполняющийся каждую 1 минуту"""
    LOGGER.info('Timer_1min thread started...')
    cycle_period = 60  # 10 if config.IS_TEST else 60
    while True:
        try:
            pass

            time.sleep(cycle_period)
        except Exception as ex_tm:
            LOGGER.error(ex_tm)
            time.sleep(cycle_period)


def timer_reports():
    """Таймер отчётов"""
    LOGGER.info('Timer_reports thread started...')
    cycle_period = 60
    while True:
        try:
            update_sheet_reports()

            time.sleep(cycle_period)
        except Exception as ex_tm:
            LOGGER.error(ex_tm)
            time.sleep(cycle_period)


def update_sheet_reports():
    sh_tuple = db.spreadsheets.get_spreadsheets_to_update()
    for sheet in sh_tuple:
        if spreadsheets.update_spreadsheet(sheet):
            db.spreadsheets.mark_spreadsheet_updated(sheet.id)


if __name__ == '__main__':
    startup_actions()

    TIMER_1MIN_THREAD = threading.Thread(target=timer_1min)
    TIMER_1MIN_THREAD.daemon = True
    TIMER_1MIN_THREAD.start()

    TIMER_REPORTS_THREAD = threading.Thread(target=timer_reports)
    TIMER_REPORTS_THREAD.daemon = True
    TIMER_REPORTS_THREAD.start()

    try:
        BOT.infinity_polling()
    except Exception as ex:
        LOGGER.error(ex)
        sys.exit()
