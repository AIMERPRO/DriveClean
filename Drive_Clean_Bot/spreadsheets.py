"""Создание отчётных таблиц (Google Sheets)"""
import calendar
import datetime
import logging
# import random

import gspread
from dateutil import relativedelta
# from faker import Faker
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from gspread.cell import Cell
from gspread.exceptions import WorksheetNotFound
from gspread_formatting import (BooleanCondition, BooleanRule, CellFormat,
                                Color, ConditionalFormatRule, GridRange,
                                NumberFormat, TextFormat, format_cell_range,
                                format_cell_ranges,
                                get_conditional_format_rules, set_frozen)

import db
from models.model_service import WEEKDAYS_NUMBERS
from models.model_spreadsheets import (SPREADSHEET_TYPES,
                                       SPREADSHEET_TYPES_CAPTIONS, Spreadsheet)
from models.model_users import CITIES, ROLES, City

LOGGER = logging.getLogger('applog')

scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
credentials = Credentials.from_service_account_file(
    './cert/credentials.json',
    scopes=scopes
)
cloud_instance = gspread.authorize(credentials)
drive_api = build('drive', 'v3', credentials=credentials)
MIME_TYPE = 'application/vnd.google-apps.spreadsheet'


def rgb_to_googlecolor(red: int, green: int, blue: int) -> Color:
    """Перевод RGB-цвета (0-255) в Color(0-1)"""
    return Color(round(red / 255, 2), round(green / 255, 2), round(blue / 255, 2))


fmt_gray_bold_center = CellFormat(
    backgroundColor=Color(0.66, 0.66, 0.66),
    textFormat=TextFormat(bold=True),
    horizontalAlignment='CENTER'
)

fmt_center = CellFormat(
    horizontalAlignment='CENTER'
)


fmt_lightfiol_bold_center = CellFormat(
    backgroundColor=rgb_to_googlecolor(217, 230, 252),
    textFormat=TextFormat(bold=True),
    horizontalAlignment='CENTER'
)

fmt_darkfiol_bold_center = CellFormat(
    backgroundColor=rgb_to_googlecolor(80, 60, 146),
    textFormat=TextFormat(bold=True, foregroundColor=rgb_to_googlecolor(255, 255, 255)),
    horizontalAlignment='CENTER'
)

fmt_somegreen_bold_center = CellFormat(
    backgroundColor=Color(0, 0.69, 0.31),
    textFormat=TextFormat(bold=True),
    horizontalAlignment='CENTER'
)


fmt_gray_whitefont = CellFormat(
    backgroundColor=Color(0.66, 0.66, 0.66),
    textFormat=TextFormat(foregroundColor=Color(1, 1, 1)),
)

fmt_standart = CellFormat(
    backgroundColor=Color(1, 1, 1),
    textFormat=TextFormat(bold=False, foregroundColor=Color(0, 0, 0)),
)

fmt_currency = CellFormat(
    numberFormat=NumberFormat(type='NUMBER', pattern='_-* # ##0.00 ₽_-;-* # ##0.00 ₽_-;_-* "-"?? ₽_-;_-@_-')
)


def create_blank_spreadsheet_by_type(city: City, id_type: int, id_user: int = None, period: str = None) -> bool:
    """Общий метод создания таблиц"""
    if id_type == SPREADSHEET_TYPES['schedules']:
        return create_blank_spreadsheet_schedules(city)
    if id_type == SPREADSHEET_TYPES['smena_results']:
        return create_blank_spreadsheet_smena_results(city)
    if id_type == SPREADSHEET_TYPES['payment_registry']:
        return create_blank_spreadsheet_payment_registry(period)
    if id_type == SPREADSHEET_TYPES['supports']:
        return create_blank_spreadsheet_supports()
    if id_type == SPREADSHEET_TYPES['brig_schedules']:
        return create_blank_spreadsheet_brig_schedules(id_user)
    if id_type == SPREADSHEET_TYPES['auto_avg_kol_by_category']:
        return create_blank_spreadsheet_auto_avg_kol_by_category()
    return False


def create_blank_spreadsheet(spreadsheet_name: str, id_folder: str) -> str:
    """Создание общей пустой таблицы"""
    file_metadata = {
        'name': spreadsheet_name,
        'mimeType': MIME_TYPE,
        'parents': [id_folder]
    }
    new_sheet = drive_api.files().create(body=file_metadata).execute()  # pylint: disable=maybe-no-member
    return new_sheet["id"]


def create_blank_spreadsheet_schedules(city: City) -> bool:
    """Создание пустой заготовки для отчёта schedules"""
    id_folder = get_id_cloud_folder_reports()
    if not id_folder:
        return False
    spreadsheet_name = f'{SPREADSHEET_TYPES_CAPTIONS[SPREADSHEET_TYPES["schedules"]]} ({city.name})'

    id_drive = create_blank_spreadsheet(spreadsheet_name, id_folder)
    db.db_spreadsheets.create_spreadsheet(city.id, SPREADSHEET_TYPES["schedules"], id_drive)
    return True


def create_blank_spreadsheet_brig_schedules(id_user: int) -> bool:
    """Создание пустой заготовки для отчёта brig_schedules"""
    id_folder = get_id_cloud_folder_reports()
    if not id_folder:
        return False
    brigadir_item = db.db_users.get_user(id_user)
    spreadsheet_name = f'{SPREADSHEET_TYPES_CAPTIONS[SPREADSHEET_TYPES["brig_schedules"]]} ({brigadir_item.fam} {brigadir_item.im})'

    id_drive = create_blank_spreadsheet(spreadsheet_name, id_folder)
    db.db_spreadsheets.create_spreadsheet(None, SPREADSHEET_TYPES["brig_schedules"], id_drive, id_user=id_user)
    return True


def create_blank_spreadsheet_smena_results(city: City) -> bool:
    """Создание пустой заготовки для отчёта smena_results"""
    id_folder = get_id_cloud_folder_reports()
    if not id_folder:
        return False
    spreadsheet_name = f'{SPREADSHEET_TYPES_CAPTIONS[SPREADSHEET_TYPES["smena_results"]]} ({city.name})'

    id_drive = create_blank_spreadsheet(spreadsheet_name, id_folder)
    db.db_spreadsheets.create_spreadsheet(city.id, SPREADSHEET_TYPES["smena_results"], id_drive)

    return True


def create_blank_spreadsheet_payment_registry(period: str) -> bool:
    """Создание пустой заготовки для отчёта payment_registry"""
    id_folder = get_id_cloud_folder_reports()
    if not id_folder:
        return False
    spreadsheet_name = f'{SPREADSHEET_TYPES_CAPTIONS[SPREADSHEET_TYPES["payment_registry"]]} {period}'

    id_drive = create_blank_spreadsheet(spreadsheet_name, id_folder)
    db.db_spreadsheets.create_spreadsheet(None, SPREADSHEET_TYPES["payment_registry"], id_drive, period=period)

    return True


def create_blank_spreadsheet_supports() -> bool:
    """Создание пустой заготовки для отчёта supports"""
    id_folder = get_id_cloud_folder_reports()
    if not id_folder:
        return False
    spreadsheet_name = f'{SPREADSHEET_TYPES_CAPTIONS[SPREADSHEET_TYPES["supports"]]}'

    id_drive = create_blank_spreadsheet(spreadsheet_name, id_folder)
    db.db_spreadsheets.create_spreadsheet(None, SPREADSHEET_TYPES["supports"], id_drive)

    return True


def create_blank_spreadsheet_auto_avg_kol_by_category() -> bool:
    """Создание пустой заготовки для отчёта auto_avg_kol_by_category"""
    id_folder = get_id_cloud_folder_reports()
    if not id_folder:
        return False
    spreadsheet_name = f'{SPREADSHEET_TYPES_CAPTIONS[SPREADSHEET_TYPES["auto_avg_kol_by_category"]]}'

    id_drive = create_blank_spreadsheet(spreadsheet_name, id_folder)
    db.db_spreadsheets.create_spreadsheet(None, SPREADSHEET_TYPES["auto_avg_kol_by_category"], id_drive)

    return True


def update_spreadsheet(sheet_item: Spreadsheet) -> bool:
    """Обновление таблицы"""
    if sheet_item.id_type == SPREADSHEET_TYPES['schedules']:
        return update_spreadsheet_schedules(sheet_item)
    if sheet_item.id_type == SPREADSHEET_TYPES['smena_results']:
        return update_spreadsheet_smena_results(sheet_item)
    if sheet_item.id_type == SPREADSHEET_TYPES['payment_registry']:
        return update_spreadsheet_payment_registry(sheet_item)
    if sheet_item.id_type == SPREADSHEET_TYPES['supports']:
        return update_spreadsheet_supports(sheet_item)
    if sheet_item.id_type == SPREADSHEET_TYPES['brig_schedules']:
        return update_spreadsheet_schedules(sheet_item, is_for_brig=True)
    if sheet_item.id_type == SPREADSHEET_TYPES['auto_avg_kol_by_category']:
        return update_spreadsheet_auto_avg_kol_by_category(sheet_item)
    return False


def update_spreadsheet_schedules(sheet_item: Spreadsheet, is_for_brig: bool = False) -> bool:
    """Обновление таблицы schedules"""
    date_start, date_end, sheet_title = get_month_period_dates(sheet_item.date_period_to_update)
    dates_list = date_range_list(date_start, date_end)

    spreadsheet = cloud_instance.open_by_key(sheet_item.id_drive)

    try:
        worksheet = spreadsheet.worksheet(sheet_title)
    except WorksheetNotFound:
        cells = []
        worksheet = spreadsheet.add_worksheet(title=sheet_title, rows=1000, cols=50, index=0)
        header_dates = []
        header_kol = []
        col = 6
        for date_item in dates_list:
            header_dates.append(f'{date_item.day:02d} ({WEEKDAYS_NUMBERS[date_item.weekday()+1]})')
            col_letter = ecn(col)
            # TODO вместо 500 количество работников
            header_kol.append(
                f'=COUNTIFS({col_letter}4:{col_letter}500,"Работает")+COUNTIFS({col_letter}4:{col_letter}500,"Работает(бот)")+COUNTIFS({col_letter}4:{col_letter}500,"Доп")')
            col += 1
        worksheet.append_row(header_dates, value_input_option='USER_ENTERED', table_range='F1')
        worksheet.append_row(header_kol, value_input_option='USER_ENTERED', table_range='F3')
        cells.append(Cell.from_address('A3', 'Район'))
        cells.append(Cell.from_address('B3', 'ФИО'))
        cells.append(Cell.from_address('C3', 'Номер телефона'))
        cells.append(Cell.from_address('D3', 'Яндекс'))  # TODO заполнять из классификатора
        cells.append(Cell.from_address('E3', 'Сити'))
        worksheet.update_cells(cells, value_input_option='USER_ENTERED')
        set_frozen(worksheet, rows=1, cols=2)
        format_cell_range(worksheet, 'A1:AJ3', fmt_center)
        format_cell_range(worksheet, 'C4:AJ500', fmt_center)
        format_cell_range(worksheet, 'A4:A500', fmt_center)

        rules = get_conditional_format_rules(worksheet)
        rules.clear()

        # TODO вместо 500 количество работников
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('D4:AJ500', worksheet)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Работает']),
                format=CellFormat(backgroundColor=Color(0.57, 0.81, 0.31))  # (#92D050)
            )
        )
        rules.append(rule)
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('D4:AJ500', worksheet)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Работает(бот)']),
                format=CellFormat(backgroundColor=Color(0.57, 0.81, 0.31))  # (#92D050)
            )
        )
        rules.append(rule)
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('D4:AJ500', worksheet)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Доп']),
                format=CellFormat(backgroundColor=Color(0.57, 0.81, 0.31))  # (#92D050)
            )
        )
        rules.append(rule)
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('D4:AJ500', worksheet)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Выходной']),
                format=CellFormat(backgroundColor=Color(1, 1, 0))  # (#FFFF00)
            )
        )
        rules.append(rule)
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('D4:AJ500', worksheet)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Отгул']),
                format=CellFormat(backgroundColor=Color(0.54, 0.7, 0.97))  # (#8CB5F9)
            )
        )
        rules.append(rule)
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('D4:AJ500', worksheet)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Опоздание']),
                format=CellFormat(backgroundColor=Color(1, 0.75, 0))  # (#FFC000)
            )
        )
        rules.append(rule)
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('D4:AJ500', worksheet)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Прогул']),
                format=CellFormat(backgroundColor=Color(1, 0, 0))  # (#FF0000)
            )
        )
        rules.append(rule)
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('D4:AJ500', worksheet)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Активно']),
                format=CellFormat(backgroundColor=Color(0.81, 0.94, 0.85))  # (#D1F1DA)
            )
        )
        rules.append(rule)
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('D4:AJ500', worksheet)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Неактивно']),
                format=CellFormat(backgroundColor=Color(0.98, 0.85, 0.84))  # (#FBDAD7)
            )
        )
        rules.append(rule)
        rules.save()

    report_tuples = db.db_spreadsheets.get_report_data_schedules(
        sheet_item.id_city, date_start, date_end, sheet_item.id_user)
    if report_tuples:
        report_data, specprojects_data = report_tuples
        cells = []
        fios_list = worksheet.col_values(2)
        row = len(fios_list) + 1
        worksheet.batch_clear([f'A4:AJ{row}'])
        format_cell_range(worksheet, f'A4:AJ{row}', fmt_standart)

        workers_count_dict = {}

        all_rows_list = []
        for report_data_row in report_data:
            row_data = []
            id_user, district, fio, phone, nick, active, week_template, dopsmena_dates_str, otgul_dates_str, proguls_penalty_dates_str, kol_carsharing_yandex, kol_carsharing_city = report_data_row
            dopsmena_dates = []
            if dopsmena_dates_str:
                dopsmena_dates_lst = dopsmena_dates_str.split(";")
                dopsmena_dates = [datetime.datetime.strptime(date, "%Y-%m-%d").date() for date in dopsmena_dates_lst]

            otgul_dates = []
            if otgul_dates_str:
                otgul_dates_lst = otgul_dates_str.split(";")
                otgul_dates = [datetime.datetime.strptime(date, "%Y-%m-%d").date() for date in otgul_dates_lst]

            proguls_penalty_dates = []
            if proguls_penalty_dates_str:
                proguls_penalty_dates_lst = proguls_penalty_dates_str.split(";")
                proguls_penalty_dates = [datetime.datetime.strptime(date, "%Y-%m-%d").date() for date in proguls_penalty_dates_lst]

            row_data.append(district)
            row_data.append(f'=HYPERLINK("https://t.me/{nick}", "{fio}")' if nick else fio)
            row_data.append(phone)

            # TODO сделать как то автоматом, чтобы само каршеринги из базы подтягивало

            # яндекс
            if active == 0:  # TODO здесь не будет 0, всех уволенных нету в выборке
                row_data.append('Неактивно')
            elif kol_carsharing_yandex > 0:
                row_data.append('Активно')
            else:
                row_data.append('-')

            # сити
            if active == 0:
                row_data.append('Неактивно')
            elif kol_carsharing_city > 0:
                row_data.append('Активно')
            else:
                row_data.append('-')

            month_template_list = []
            for date_item in dates_list:
                if not week_template and date_item not in dopsmena_dates and date_item not in otgul_dates:
                    month_template_list.append('-')
                    workers_count_inc = 0

                elif date_item in otgul_dates and date_item in dopsmena_dates:
                    # ... значит нужно смотреть, что из этого (отгул или допсмена) сделано позже, то и будет главнее
                    dopsmena_item = db.db_smena.get_dopsmena(id_user, date_item)
                    otgul_item = db.db_smena.get_otgul(id_user, date_item)
                    if otgul_item and otgul_item.date_create > dopsmena_item.date_create:
                        month_template_list.append('Отгул')
                        workers_count_inc = 0
                    else:
                        if dopsmena_item and dopsmena_item.auto_assigned == 1:
                            month_template_list.append('Работает(бот)')
                        else:
                            month_template_list.append('Доп')
                        workers_count_inc = 1

                elif date_item in otgul_dates:
                    month_template_list.append('Отгул')
                    workers_count_inc = 0
                elif date_item in dopsmena_dates:
                    dopsmena_item = db.db_smena.get_dopsmena(id_user, date_item)
                    if dopsmena_item and dopsmena_item.auto_assigned == 1:
                        month_template_list.append('Работает(бот)')
                    else:
                        month_template_list.append('Доп')
                    workers_count_inc = 1
                elif date_item in proguls_penalty_dates:
                    month_template_list.append('Прогул')
                    workers_count_inc = 0
                else:
                    month_template_list.append(week_template[date_item.weekday()])
                    if week_template[date_item.weekday()] == '1':
                        workers_count_inc = 1
                    else:
                        workers_count_inc = 0

                workers_count_dict[date_item] = workers_count_dict[date_item] + \
                    workers_count_inc if date_item in workers_count_dict else workers_count_inc

            # TODO опоздания и прогулы

            for month_item in month_template_list:
                row_data.append('Работает' if month_item == '1' else 'Выходной' if month_item == '0' else month_item)

            all_rows_list.append(row_data)

        if not is_for_brig:
            for specprojects_data_row in specprojects_data:
                row_data = []
                fio, phone, status = specprojects_data_row
                row_data.append('Спец проекты')
                row_data.append(fio)
                row_data.append(phone)
                row_data.append(status)
                all_rows_list.append(row_data)

        update_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
        cells.append(Cell.from_address('B1', f'Обновлено {update_time}'))

        worksheet.append_rows(all_rows_list, value_input_option='USER_ENTERED', table_range='A4')
        worksheet.update_cells(cells, value_input_option='USER_ENTERED')

        if not is_for_brig:
            db.db_smena.insert_workers_count(workers_count_dict, sheet_item.id_city)

        worksheet.columns_auto_resize(1, 3)

    return True


def update_spreadsheet_smena_results(sheet_item: Spreadsheet) -> bool:
    """Обновление таблицы smena_results"""
    spreadsheet = cloud_instance.open_by_key(sheet_item.id_drive)
    date_start, date_end, sheet_title = get_period_dates(sheet_item.date_period_to_update)

    try:
        worksheet = spreadsheet.worksheet(sheet_title)
    except WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=sheet_title, rows=1000, cols=50,
                                              index=1 if sheet_item.date_period_to_update else 0)
        cells = []
        row = 1
        col = 1
        header = ['Дата', 'ФИО', 'Телефон', 'Район', 'Адрес мойки', 'Время', 'Госномер',
                  'Каршеринг', 'Класс авто', 'Срочность', 'Вид мойки', 'Омывайка', 'Дневная', 'п.б.', 'п.с.', 'хим', 'битум']
        for header_item in header:
            cells.append(Cell(row=row, col=col, value=header_item))
            col += 1
        row += 1
        col = 1

        worksheet.update_cells(cells, value_input_option='USER_ENTERED')
        format_cell_range(worksheet, 'A1:Q1', fmt_somegreen_bold_center)
        set_frozen(worksheet, rows=1)

    datetime_start_text = date_start.strftime("%Y-%m-%d 10:00:00")
    datetime_end_text = (date_end + datetime.timedelta(days=1)).strftime("%Y-%m-%d 09:59:59")

    report_data = db.db_spreadsheets.get_report_data_smena_results(
        sheet_item.id_city, date_start, date_end, datetime_start_text, datetime_end_text)
    if report_data:
        fios_list = worksheet.col_values(2)
        row = len(fios_list) + 1
        worksheet.batch_clear([f'A2:Q{row}'])

        all_rows_list = []
        cells = []

        for row_data in report_data:
            all_rows_list.append(row_data)

        update_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
        cells.append(Cell.from_address('S1', f'Обновлено {update_time}'))

        worksheet.append_rows(all_rows_list, value_input_option='USER_ENTERED', table_range='A2')
        worksheet.update_cells(cells, value_input_option='USER_ENTERED')
        worksheet.columns_auto_resize(1, 2)
        worksheet.columns_auto_resize(4, 5)

    return True


def update_spreadsheet_payment_registry(sheet_item: Spreadsheet) -> bool:
    """Обновление таблицы payment_registry"""
    update_spreadsheet_payment_registry_peregon(sheet_item)
    update_spreadsheet_payment_registry_tp(sheet_item)
    # update_spreadsheet_payment_registry_callcenter(sheet_item)
    return True


def update_spreadsheet_payment_registry_peregon(sheet_item: Spreadsheet) -> bool:
    """Обновление таблицы payment_registry - лист перегонщиков"""
    today_period = datetime.date.today().strftime("%Y-%m")
    if not sheet_item.date_period_to_update and sheet_item.period != today_period:
        LOGGER.error(
            'Для обновления прошлой таблицы нужно дополнительно задать дату обновления (date_period_to_update) из её периодов')
        return False

    # TODO этот кусок не работает! Нужно следить за "прошлым периодом" для обновления таблицы, чтобы не перерисовать текущую прошлыми данными
    # if sheet_item.date_period_to_update and sheet_item.date_period_to_update.strftime("%Y-%m")!=today_period:
    #     LOGGER.error('Обновить прошлый период в таблице payment_registry можно только в пределах её месяца')
    #     return False

    spreadsheet = cloud_instance.open_by_key(sheet_item.id_drive)
    date_start, date_end, _ = get_period_dates(sheet_item.date_period_to_update)
    sheet_title_peregon = f'Перегон {date_start.strftime("%d.%m")} - {date_end.strftime("%d.%m.%Y")}'

    cells = []
    cells_formatted = []

    spreadsheet_specprojects = cloud_instance.open_by_key(db.db_prefs.get_pref('id_drive_table_specprojects').textval)
    worksheet_specprojects_logans = spreadsheet_specprojects.worksheet('Транзиты_Логаны')
    specprojects_loganssheet_checked_items_cells = []
    worksheet_specprojects_vozvr = spreadsheet_specprojects.worksheet('Возврат')
    specprojects_vozvrsheet_checked_items_cells = []

    try:
        worksheet_peregon = spreadsheet.worksheet(sheet_title_peregon)
    except WorksheetNotFound:
        worksheet_peregon = spreadsheet.add_worksheet(title=sheet_title_peregon, rows=1000, cols=70,
                                                      index=1 if sheet_item.date_period_to_update else 0)
        header = [
            'Форма оплаты',
            'ФИО',
            'Телефон (бот)',
            'Телефон (konsol)',
            'Город',
            'Район',
            'Ставка ночь (шт)',
            'Ставка день (шт)',
            'Ставка новичок (шт)',
            'Ставка бригадир (шт) ',
            'Ставка тренер (шт) ',
            'Ставка проверяющий  (шт)',
            'Ставка Транзиты (час)',
            'Ставка Логаны (час)',
            'Ставка реновация',
            'Ставка возврат',
            'Ставка съёмки',
            'Ставка подгон',
            'Ставка новые авто',
            'Ставка шиномонтаж',
            'Ставка проверка фото',
            'Ночь -Яндекс',
            'Ночь - Сити',
            'День - Яндекс',
            'Новичок',
            'Бригадир',
            'Тренер',
            'Проверяющий',
            'Транзиты - Яндекс',
            'Логаны - Яндекс',
            'Реновация - Яндекс',
            'Возврат - Яндекс',
            'Съёмки - Яндекс',
            'Подгон - Яндекс',
            'Новые авто',
            'Шиномонтаж',
            'Проверка фото',
            'Прогул',
            'Опоздание',
            'Фото',
            'Перепробег',
            'Парковка',
            'Эвакуация',
            'ДТП',
            'Проверка чистоты',
            'Лишние авто',
            'Сумма штрафов',
            'Бонус',
            'Доп. выплаты',
            'Налог',
            'Сумма акта',
            'Статус акта',
            'Статус оплаты',
        ]
        row = 2
        col = 1
        for header_item in header:
            cells.append(Cell(row=row, col=col, value=header_item))
            col += 1

        cells.append(Cell.from_address('A1', 'Данные исполнителя'))
        cells.append(Cell.from_address('G1', 'Условия оплаты'))
        cells.append(Cell.from_address('V1', 'Результаты'))
        cells.append(Cell.from_address('AL1', 'Штрафы'))
        cells.append(Cell.from_address('AV1', 'Доплата'))
        cells.append(Cell.from_address('AZ1', 'Итоги'))

        merge_cells(spreadsheet, sheet_title_peregon, 1, 1, 2, 7)
        merge_cells(spreadsheet, sheet_title_peregon, 1, 7, 2, 22)
        merge_cells(spreadsheet, sheet_title_peregon, 1, 22, 2, 38)
        merge_cells(spreadsheet, sheet_title_peregon, 1, 38, 2, 48)
        merge_cells(spreadsheet, sheet_title_peregon, 1, 48, 2, 52)
        merge_cells(spreadsheet, sheet_title_peregon, 1, 52, 2, 54)

        cells_formatted.append(('A1:BA1', fmt_darkfiol_bold_center))
        cells_formatted.append(('A2:BA2', fmt_lightfiol_bold_center))
        cells_formatted.append(('G:U', fmt_currency))
        cells_formatted.append(('AL:AY', fmt_currency))

        rules = get_conditional_format_rules(worksheet_peregon)
        rules.clear()

        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('AZ3:BA500', worksheet_peregon)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Не оплачен']),
                format=CellFormat(backgroundColor=rgb_to_googlecolor(229, 229, 229))  # (#E5E5E5)
            )
        )
        rules.append(rule)
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('AZ3:BA500', worksheet_peregon)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Ожидает сверки']),
                format=CellFormat(backgroundColor=rgb_to_googlecolor(229, 229, 229))  # (#E5E5E5)
            )
        )
        rules.append(rule)
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('AZ3:BA500', worksheet_peregon)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Оплачен']),
                format=CellFormat(backgroundColor=rgb_to_googlecolor(210, 241, 218))  # (#D2F1DA)
            )
        )
        rules.append(rule)
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('AZ3:BA500', worksheet_peregon)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Акт сформирован']),
                format=CellFormat(backgroundColor=rgb_to_googlecolor(210, 241, 218))  # (#D2F1DA)
            )
        )
        rules.append(rule)
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('AZ3:BA500', worksheet_peregon)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Акт подтверждён']),
                format=CellFormat(backgroundColor=rgb_to_googlecolor(254, 241, 204))  # (#FEF1CC)
            )
        )
        rules.append(rule)
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('AZ3:BA500', worksheet_peregon)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Ошибка оплаты']),
                format=CellFormat(backgroundColor=rgb_to_googlecolor(250, 217, 214))  # (#FAD9D6)
            )
        )
        rules.append(rule)

        rules.save()

        set_frozen(worksheet_peregon, rows=2)

    datetime_start_text = date_start.strftime("%Y-%m-%d 10:00:00")
    datetime_end_text = (date_end + datetime.timedelta(days=1)).strftime("%Y-%m-%d 09:59:59")

    specprojects_phones_set = set()
    specprojects_phones_str = ""
    specprojects_loganssheet_checked_rows_lst = worksheet_specprojects_logans.col_values(9)
    row_specprojects_loganssheet_start = len(specprojects_loganssheet_checked_rows_lst) + 1
    specprojects_loganssheet_dates_list = worksheet_specprojects_logans.col_values(1)
    row_specprojects_loganssheet_end = len(specprojects_loganssheet_dates_list)
    specprojects_loganssheet_new_data_lst = worksheet_specprojects_logans.get(f'A{row_specprojects_loganssheet_start}:H{row_specprojects_loganssheet_end}')
    for specprojects_loganssheet_new_data_row in specprojects_loganssheet_new_data_lst:
        specprojects_phones_set.add(specprojects_loganssheet_new_data_row[2])

    specprojects_vozvrsheet_checked_rows_lst = worksheet_specprojects_vozvr.col_values(8)
    row_specprojects_vozvrsheet_start = len(specprojects_vozvrsheet_checked_rows_lst) + 1
    specprojects_vozvrsheet_dates_list = worksheet_specprojects_vozvr.col_values(1)
    row_specprojects_vozvrsheet_end = len(specprojects_vozvrsheet_dates_list)
    specprojects_vozvrsheet_new_data_lst = worksheet_specprojects_vozvr.get(f'A{row_specprojects_vozvrsheet_start}:G{row_specprojects_vozvrsheet_end}')
    for specprojects_vozvrsheet_new_data_row in specprojects_vozvrsheet_new_data_lst:
        specprojects_phones_set.add(specprojects_vozvrsheet_new_data_row[2])

    if specprojects_phones_set:
        for specprojects_phone in specprojects_phones_set:
            specprojects_phones_str += f', \"{specprojects_phone}\"' if specprojects_phones_str else f'\"{specprojects_phone}\"'

    all_rows_list = []
    report_data, novichok_lst, karatel_ids_lst, karatel_outcheck_carskol_tuple, \
        karatel_washcheck_carskol_tuple, trainer_phones_lst, trainers_with_students_count, \
        penalty_progul_tuple, penalty_photo_tuple, msk_leftover_percent_average, \
        msk_kol_brig_cars_divided_pabratski = db.db_spreadsheets.get_workers_payment_registry_report_data_peregon(
            date_start, date_end, datetime_start_text, datetime_end_text, specprojects_phones_str)
    if report_data:
        fios_list = worksheet_peregon.col_values(2)
        row = len(fios_list) + 1
        worksheet_peregon.batch_clear([f'A3:BA{row}'])

    row = 3
    for row_data in report_data:
        id_user, id_city, id_role, opl_type, fio, phone_bot, phone_konsol, city_name, district, \
            smena_kol, night_cars_kol, noch_ya, noch_city, day_ya, transit_ya, renov_ya = row_data
        opozd = 0

        is_konsol = True if opl_type == 'Konsol' else False

        pereprobeg = 0
        parkovka = 0
        evac = 0
        dtp = 0
        lishn = 0
        bonus = 0
        dop_vypl = 0
        nalog = 0

        night_auto_average = int(night_cars_kol / smena_kol) if smena_kol > 0 else night_cars_kol

        stavka_transit = 0
        stavka_renov = 0

        # -------------------- Расчёт с подтягиванием данных из таблицы спецпроектов --------------------------
        stavka_specprojects = 257.5 if is_konsol else 250

        stavka_vozvr = 0
        stavka_logan = 0
        stavka_sjem = 0
        stavka_podgon = 0
        stavka_nov_auto = 0
        stavka_shin = 0
        stavka_prov_photo = 0

        vozvr_ya = 0
        logan_ya = 0
        sjem_ya = 0
        podgon_ya = 0
        nov_auto = 0
        shin = 0
        prov_photo = 0

        if id_user in (658949357, 380171161):
            prov_photo = 1
            stavka_prov_photo = 2060

        cur_specprojects_row = row_specprojects_loganssheet_start
        for specprojects_data_item in specprojects_loganssheet_new_data_lst:
            spec_phone = specprojects_data_item[2]
            if spec_phone and spec_phone == phone_bot:
                spec_type = specprojects_data_item[3]
                if spec_type == 'Логан':
                    logan_hourly_item = specprojects_data_item[7]
                    if logan_hourly_item:
                        logan_ya += int(logan_hourly_item)
                        stavka_logan = stavka_specprojects
                        specprojects_loganssheet_checked_items_cells.append(Cell(row=cur_specprojects_row, col=9, value='да'))
                elif spec_type == 'Съёмки':
                    sjem_hourly_item = specprojects_data_item[7]
                    if sjem_hourly_item:
                        sjem_ya += int(sjem_hourly_item)
                        stavka_sjem = stavka_specprojects
                        specprojects_loganssheet_checked_items_cells.append(Cell(row=cur_specprojects_row, col=9, value='да'))
                elif spec_type == 'Подгон':
                    podgon_hourly_item = specprojects_data_item[7]
                    if podgon_hourly_item:
                        podgon_ya += int(podgon_hourly_item)
                        stavka_podgon = stavka_specprojects
                        specprojects_loganssheet_checked_items_cells.append(Cell(row=cur_specprojects_row, col=9, value='да'))
                elif spec_type == 'Новые авто':
                    nov_auto_hourly_item = specprojects_data_item[7]
                    if nov_auto_hourly_item:
                        nov_auto += int(nov_auto_hourly_item)
                        stavka_nov_auto = stavka_specprojects
                        specprojects_loganssheet_checked_items_cells.append(Cell(row=cur_specprojects_row, col=9, value='да'))
                elif spec_type == 'Шиномонтаж':
                    shin_hourly_item = specprojects_data_item[7]
                    if shin_hourly_item:
                        shin += int(shin_hourly_item)
                        stavka_shin = stavka_specprojects
                        specprojects_loganssheet_checked_items_cells.append(Cell(row=cur_specprojects_row, col=9, value='да'))
            cur_specprojects_row += 1

        cur_specprojects_row = row_specprojects_vozvrsheet_start
        for specprojects_data_item in specprojects_vozvrsheet_new_data_lst:
            spec_phone = specprojects_data_item[2]
            if spec_phone and spec_phone == phone_bot:
                spec_type = specprojects_data_item[3]
                if spec_type == 'Возврат':
                    vozvr_hourly_item = specprojects_data_item[6]
                    if vozvr_hourly_item:
                        vozvr_ya += int(vozvr_hourly_item)
                        stavka_vozvr = stavka_specprojects
                        specprojects_vozvrsheet_checked_items_cells.append(Cell(row=cur_specprojects_row, col=8, value='да'))
            cur_specprojects_row += 1

        # -----------------------------------------------------------------------------------------------------

        stavka_karatel = 0
        karatel = 0

        if karatel_ids_lst:
            if id_user in karatel_ids_lst:
                stavka_karatel = 72.10

        if karatel_outcheck_carskol_tuple:
            for karatel_carskol in karatel_outcheck_carskol_tuple:
                id_remote_karatel, carskol = karatel_carskol
                if id_user == id_remote_karatel:
                    karatel += carskol
                    break

        if karatel_washcheck_carskol_tuple:
            for karatel_carskol in karatel_washcheck_carskol_tuple:
                id_remote_karatel, carskol = karatel_carskol
                if id_user == id_remote_karatel:
                    karatel += carskol
                    break

        purity_penalty = 0
        cells.append(Cell.from_address(f'AM{row}', f'={purity_penalty}*G{row}*-1'))

        trainer = 0
        stavka_trainer = 0

        if trainer_phones_lst:
            for trainer_phone in trainer_phones_lst:
                if trainer_phone == phone_bot:
                    # TODO у мск тут хитро считается (см. в постановке), "каждый прошедший обучение" и
                    # "каждый вышедший на 5 смену". Это сейчас они совпадают, как бы не получилось что они резко
                    # цифры изменили, и придётся весь код перелопачивать

                    # TODO а вообще непонятно, зачем "каждый вышедший на 5 смену" если выплата за 1 ученика только 1 раз,
                    # и он всё равно проходит как "каждый прошедший обучение"

                    if id_city == CITIES['moscow']:
                        if is_konsol:
                            stavka_trainer = 412
                        else:
                            stavka_trainer = 400

                        if trainers_with_students_count:
                            for trainer_with_student in trainers_with_students_count:
                                phone_trainer, kol_stud = trainer_with_student
                                if phone_trainer == phone_bot:
                                    trainer = kol_stud

                    elif id_city == CITIES['piter']:
                        if is_konsol:
                            stavka_trainer = 1717
                        else:
                            stavka_trainer = 1667

                        # TODO повторение как выше
                        if trainers_with_students_count:
                            for trainer_with_student in trainers_with_students_count:
                                phone_trainer, kol_stud = trainer_with_student
                                if phone_trainer == phone_bot:
                                    trainer = kol_stud

        stavka_brig = 0
        brig = 0
        if id_role == ROLES['brigadir']:
            if id_city == CITIES['moscow']:
                brig = msk_kol_brig_cars_divided_pabratski
                if is_konsol:
                    if msk_leftover_percent_average > 35:
                        stavka_brig = 0
                    elif 20 <= msk_leftover_percent_average <= 35:
                        stavka_brig = 1.03
                    elif 14 <= msk_leftover_percent_average <= 19:
                        stavka_brig = 2.06
                    elif 7 <= msk_leftover_percent_average <= 13:
                        stavka_brig = 2.58
                    elif msk_leftover_percent_average < 7:
                        stavka_brig = 3.09
                else:
                    if msk_leftover_percent_average > 35:
                        stavka_brig = 0
                    elif 20 <= msk_leftover_percent_average <= 35:
                        stavka_brig = 1
                    elif 14 <= msk_leftover_percent_average <= 19:
                        stavka_brig = 2
                    elif 7 <= msk_leftover_percent_average <= 13:
                        stavka_brig = 2.5
                    elif msk_leftover_percent_average < 7:
                        stavka_brig = 3
            elif id_city == CITIES['piter']:
                brig = 1
                if is_konsol:
                    stavka_brig = 3434
                else:
                    stavka_brig = 3334

        stavka_novichok = 0
        novichok = 0
        for novichok_item in novichok_lst:
            id_user_novichok, kol_first_cars = novichok_item
            if id_user_novichok == id_user:
                stavka_novichok = 133.9
                novichok = kol_first_cars
                noch_ya = noch_ya - kol_first_cars
                if noch_ya < 0:
                    noch_ya = 0

        stavka_noch = 0
        stavka_day = 0
        if id_city == CITIES['moscow']:
            if id_role == ROLES['brigadir']:
                stavka_noch = 154.5
            else:
                if 1 <= smena_kol <= 3:
                    if night_auto_average <= 11:
                        stavka_noch = 100
                    elif 12 <= night_auto_average <= 15:
                        stavka_noch = 120
                    elif 16 <= night_auto_average <= 20:
                        stavka_noch = 130
                    elif night_auto_average >= 21:
                        stavka_noch = 140
                elif 4 <= smena_kol <= 7:
                    if night_auto_average <= 11:
                        stavka_noch = 110
                    elif 12 <= night_auto_average <= 15:
                        stavka_noch = 130
                    elif 16 <= night_auto_average <= 20:
                        stavka_noch = 140
                    elif night_auto_average >= 21:
                        stavka_noch = 150
                elif smena_kol >= 8:
                    if night_auto_average <= 11:
                        stavka_noch = 120
                    elif 12 <= night_auto_average <= 15:
                        stavka_noch = 140
                    elif 16 <= night_auto_average <= 20:
                        stavka_noch = 150
                    elif night_auto_average >= 21:
                        stavka_noch = 165
                else:
                    stavka_noch = 0

                stavka_noch += stavka_noch * 0.03

            if is_konsol:
                if 1 <= day_ya <= 25:
                    stavka_day = 206
                elif day_ya > 25:
                    stavka_day = 257
                else:
                    stavka_day = 0
            else:
                if 1 <= day_ya <= 25:
                    stavka_day = 200
                elif day_ya > 25:
                    stavka_day = 250
                else:
                    stavka_day = 0

        elif id_city == CITIES['piter']:
            if is_konsol:
                if id_role == ROLES['brigadir']:
                    stavka_noch = 154.5
                else:
                    stavka_noch = 133.90
                stavka_day = 206
            else:
                if id_role == ROLES['brigadir']:
                    stavka_noch = 150
                else:
                    stavka_noch = 130
                stavka_day = 200

        stavka_progul = 12
        stavka_photo = 1
        progul = 0
        photo = 0
        if penalty_progul_tuple:
            for penalty_progul in penalty_progul_tuple:
                id_penalty_user, penalty_kol = penalty_progul
                if id_penalty_user == id_user:
                    cells.append(Cell.from_address(f'AL{row}', f'={penalty_kol}*{stavka_progul}*G{row}*-1'))

        if penalty_photo_tuple:
            for penalty_photo in penalty_photo_tuple:
                id_penalty_user, penalty_kol = penalty_photo
                if id_penalty_user == id_user:
                    cells.append(Cell.from_address(f'AN{row}', f'={penalty_kol}*{stavka_photo}*G{row}*-1'))

        act_status = 'Ожидает сверки'
        opl_status = 'Не оплачен'

        all_rows_list.append([opl_type, fio, phone_bot, phone_konsol, city_name, district, stavka_noch, stavka_day, stavka_novichok, stavka_brig, stavka_trainer, stavka_karatel, stavka_transit, stavka_logan, stavka_renov, stavka_vozvr, stavka_sjem, stavka_podgon, stavka_nov_auto, stavka_shin, stavka_prov_photo,
                             noch_ya, noch_city, day_ya, novichok, brig, trainer, karatel, transit_ya, logan_ya, renov_ya, vozvr_ya, sjem_ya, podgon_ya, nov_auto, shin, prov_photo, progul, opozd, photo, pereprobeg, parkovka, evac, dtp, None, lishn, None, bonus, dop_vypl, nalog])

        cells.append(Cell.from_address(f'AU{row}', f'=SUM(AL{row}:AT{row})'))
        cells.append(Cell.from_address(f'AY{row}', f'=(G{row}*V{row}+G{row}*W{row}+H{row}*X{row}+I{row}*Y{row}+J{row}*Z{row}+K{row}*AA{row}+L{row}*AB{row}+M{row}*AC{row}+N{row}*AD{row}+O{row}*AE{row}+P{row}*AF{row}+Q{row}*AG{row}+R{row}*AH{row}+S{row}*AI{row}+T{row}*AJ{row}+U{row}*AK{row})+AU{row}+AV{row}+AW{row}+AX{row}'))
        cells.append(Cell.from_address(f'AZ{row}', act_status))
        cells.append(Cell.from_address(f'BA{row}', opl_status))
        row += 1

    update_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    cells.append(Cell.from_address('BD1', f'Обновлено {update_time}'))

    if cells_formatted:
        format_cell_ranges(worksheet_peregon, cells_formatted)
    if all_rows_list:
        worksheet_peregon.append_rows(all_rows_list, value_input_option='USER_ENTERED', table_range='A3')

    # сначала записывается all_rows_list, потом поверх него записываются cell, поэтому если что-то есть и там и там, то cells всё это перезапишет
    worksheet_peregon.update_cells(cells, value_input_option='USER_ENTERED')
    worksheet_peregon.columns_auto_resize(0, 53)

    if specprojects_loganssheet_checked_items_cells:
        worksheet_specprojects_logans.update_cells(specprojects_loganssheet_checked_items_cells, value_input_option='USER_ENTERED')

    if specprojects_vozvrsheet_checked_items_cells:
        worksheet_specprojects_vozvr.update_cells(specprojects_vozvrsheet_checked_items_cells, value_input_option='USER_ENTERED')

    return True


def update_spreadsheet_payment_registry_tp(sheet_item: Spreadsheet) -> bool:
    """Обновление таблицы payment_registry - лист саппортов"""
    today_period = datetime.date.today().strftime("%Y-%m")
    if not sheet_item.date_period_to_update and sheet_item.period != today_period:
        LOGGER.error(
            'Для обновления прошлой таблицы нужно дополнительно задать дату обновления (date_period_to_update) из её периодов')
        return False

    # TODO этот кусок не работает! Нужно следить за "прошлым периодом" для обновления таблицы, чтобы не перерисовать текущую прошлыми данными
    # if sheet_item.date_period_to_update and sheet_item.date_period_to_update.strftime("%Y-%m")!=today_period:
    #     LOGGER.error('Обновить прошлый период в таблице payment_registry можно только в пределах её месяца')
    #     return False

    spreadsheet = cloud_instance.open_by_key(sheet_item.id_drive)
    date_start, date_end, _ = get_period_dates(sheet_item.date_period_to_update)
    sheet_title_tp = f'Техподдержка {date_start.strftime("%d.%m")} - {date_end.strftime("%d.%m.%Y")}'

    cells = []
    cells_formatted = []

    try:
        worksheet_tp = spreadsheet.worksheet(sheet_title_tp)
    except WorksheetNotFound:
        worksheet_tp = spreadsheet.add_worksheet(title=sheet_title_tp, rows=1000, cols=45,
                                                 index=1 if sheet_item.date_period_to_update else 0)
        header_tp = [
            'Форма оплаты',
            'ФИО',
            'Телефон (бот)',
            'Телефон (konsol)',
            'Ставка час',
            'Часов',
            'Прогул',
            'Опоздание',
            'Субординация',
            'Сумма штрафов',
            'Бонус',
            'Доп. выплаты',
            'Налог',
            'Сумма акта',
            'Статус акта',
            'Статус оплаты',
        ]
        row = 2
        col = 1
        for header_item in header_tp:
            cells.append(Cell(row=row, col=col, value=header_item))
            col += 1

        cells.append(Cell.from_address('A1', 'Данные исполнителя'))
        cells.append(Cell.from_address('E1', 'Условия оплаты'))
        cells.append(Cell.from_address('F1', 'Результаты'))
        cells.append(Cell.from_address('G1', 'Штрафы'))
        cells.append(Cell.from_address('K1', 'Доплата'))
        cells.append(Cell.from_address('N1', 'Итоги'))

        merge_cells(spreadsheet, sheet_title_tp, 1, 1, 2, 5)
        merge_cells(spreadsheet, sheet_title_tp, 1, 7, 2, 11)
        merge_cells(spreadsheet, sheet_title_tp, 1, 11, 2, 14)
        merge_cells(spreadsheet, sheet_title_tp, 1, 14, 2, 17)

        cells_formatted.append(('A1:P1', fmt_darkfiol_bold_center))
        cells_formatted.append(('A2:P2', fmt_lightfiol_bold_center))
        cells_formatted.append(('E:E', fmt_currency))
        cells_formatted.append(('G:N', fmt_currency))

        rules = get_conditional_format_rules(worksheet_tp)
        rules.clear()

        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('O3:P500', worksheet_tp)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Не оплачен']),
                format=CellFormat(backgroundColor=rgb_to_googlecolor(229, 229, 229))  # (#E5E5E5)
            )
        )
        rules.append(rule)
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('O3:P500', worksheet_tp)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Ожидает сверки']),
                format=CellFormat(backgroundColor=rgb_to_googlecolor(229, 229, 229))  # (#E5E5E5)
            )
        )
        rules.append(rule)
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('O3:P500', worksheet_tp)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Оплачен']),
                format=CellFormat(backgroundColor=rgb_to_googlecolor(210, 241, 218))  # (#D2F1DA)
            )
        )
        rules.append(rule)
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('O3:P500', worksheet_tp)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Акт сформирован']),
                format=CellFormat(backgroundColor=rgb_to_googlecolor(210, 241, 218))  # (#D2F1DA)
            )
        )
        rules.append(rule)
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('O3:P500', worksheet_tp)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Акт подтверждён']),
                format=CellFormat(backgroundColor=rgb_to_googlecolor(254, 241, 204))  # (#FEF1CC)
            )
        )
        rules.append(rule)
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('O3:P500', worksheet_tp)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Ошибка оплаты']),
                format=CellFormat(backgroundColor=rgb_to_googlecolor(250, 217, 214))  # (#FAD9D6)
            )
        )
        rules.append(rule)

        rules.save()

        set_frozen(worksheet_tp, rows=2)

    all_rows_list = []
    report_data, penalty_progul_tuple = db.db_spreadsheets.get_workers_payment_registry_report_data_tp(date_start, date_end)
    if report_data:
        fios_list = worksheet_tp.col_values(2)
        row = len(fios_list) + 1
        worksheet_tp.batch_clear([f'A3:P{row}'])

    row = 3
    for row_data in report_data:
        id_user, opl_type, fio, phone_bot, phone_konsol, worked_hours = row_data
        is_konsol = True if opl_type == 'Konsol' else False
        worked_hours = int(worked_hours) if worked_hours else None

        if is_konsol:
            stavka_tp = 187.7
        else:
            stavka_tp = 182.3

        stavka_progul = 8
        progul = 0  # для тех у кого нет штрафов
        if penalty_progul_tuple:
            for penalty_progul in penalty_progul_tuple:
                id_penalty_user, penalty_kol = penalty_progul
                if id_penalty_user == id_user:
                    cells.append(Cell.from_address(f'G{row}', f'={penalty_kol}*{stavka_progul}*E{row}*-1'))

        act_status = 'Ожидает сверки'
        opl_status = 'Не оплачен'

        all_rows_list.append([opl_type, fio, phone_bot, phone_konsol, stavka_tp, worked_hours, progul])

        cells.append(Cell.from_address(f'J{row}', f'=SUM(G{row}:I{row})'))
        cells.append(Cell.from_address(f'N{row}', f'=(E{row}*F{row}+K{row}+J{row}+M{row}+L{row})'))
        cells.append(Cell.from_address(f'O{row}', act_status))
        cells.append(Cell.from_address(f'P{row}', opl_status))
        row += 1

    update_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    cells.append(Cell.from_address('U1', f'Обновлено {update_time}'))

    if cells_formatted:
        format_cell_ranges(worksheet_tp, cells_formatted)
    if all_rows_list:
        worksheet_tp.append_rows(all_rows_list, value_input_option='USER_ENTERED', table_range='A3')

    worksheet_tp.update_cells(cells, value_input_option='USER_ENTERED')
    worksheet_tp.columns_auto_resize(0, 16)

    return True


# TODO таблицу коллцентра полностью переделать, сейчас она не используется
def update_spreadsheet_payment_registry_callcenter(sheet_item: Spreadsheet) -> bool:
    """Обновление таблицы payment_registry - лист коллцентра"""
    today_period = datetime.date.today().strftime("%Y-%m")
    if not sheet_item.date_period_to_update and sheet_item.period != today_period:
        LOGGER.error(
            'Для обновления прошлой таблицы нужно дополнительно задать дату обновления (date_period_to_update) из её периодов')
        return False

    # TODO этот кусок не работает! Нужно следить за "прошлым периодом" для обновления таблицы, чтобы не перерисовать текущую прошлыми данными
    # if sheet_item.date_period_to_update and sheet_item.date_period_to_update.strftime("%Y-%m")!=today_period:
    #     LOGGER.error('Обновить прошлый период в таблице payment_registry можно только в пределах её месяца')
    #     return False

    spreadsheet = cloud_instance.open_by_key(sheet_item.id_drive)
    date_start, date_end, _ = get_period_dates(sheet_item.date_period_to_update)
    sheet_title_callcenter = f'Колл-центр {date_start.strftime("%d.%m")} - {date_end.strftime("%d.%m.%Y")}'

    cells = []
    cells_formatted = []

    try:
        worksheet_callcenter = spreadsheet.worksheet(sheet_title_callcenter)
    except WorksheetNotFound:
        worksheet_callcenter = spreadsheet.add_worksheet(title=sheet_title_callcenter, rows=1000, cols=45,
                                                         index=1 if sheet_item.date_period_to_update else 0)
        header_callcenter = [
            'Форма оплаты',
            'ФИО',
            'Телефон (бот)',
            'Телефон (konsol)',
            'Ставка диалог',
            'Ставка обучение',
            'Ставка 1 смена',
            'Диалог',
            'Обучение',
            '1 смена',
            'Прогул',
            'Опоздание',
            'Скрипт',
            'Субординация',
            'Сумма штрафов',
            'Бонус',
            'Доп. выплаты',
            'Налог',
            'Сумма акта',
            'Статус акта',
            'Статус оплаты',
        ]
        row = 2
        col = 1
        for header_item in header_callcenter:
            cells.append(Cell(row=row, col=col, value=header_item))
            col += 1

        cells.append(Cell.from_address('A1', 'Данные исполнителя'))
        cells.append(Cell.from_address('E1', 'Условия оплаты'))
        cells.append(Cell.from_address('H1', 'Результаты'))
        cells.append(Cell.from_address('K1', 'Штрафы'))
        cells.append(Cell.from_address('P1', 'Доплата'))
        cells.append(Cell.from_address('S1', 'Итоги'))

        merge_cells(spreadsheet, sheet_title_callcenter, 1, 1, 2, 5)
        merge_cells(spreadsheet, sheet_title_callcenter, 1, 5, 2, 8)
        merge_cells(spreadsheet, sheet_title_callcenter, 1, 8, 2, 11)
        merge_cells(spreadsheet, sheet_title_callcenter, 1, 11, 2, 16)
        merge_cells(spreadsheet, sheet_title_callcenter, 1, 16, 2, 19)
        merge_cells(spreadsheet, sheet_title_callcenter, 1, 19, 2, 22)

        cells_formatted.append(('A1:U1', fmt_darkfiol_bold_center))
        cells_formatted.append(('A2:U2', fmt_lightfiol_bold_center))
        cells_formatted.append(('E:G', fmt_currency))
        cells_formatted.append(('K:S', fmt_currency))

        rules = get_conditional_format_rules(worksheet_callcenter)
        rules.clear()

        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('T3:U500', worksheet_callcenter)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Не оплачен']),
                format=CellFormat(backgroundColor=rgb_to_googlecolor(229, 229, 229))  # (#E5E5E5)
            )
        )
        rules.append(rule)
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('T3:U500', worksheet_callcenter)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Ожидает сверки']),
                format=CellFormat(backgroundColor=rgb_to_googlecolor(229, 229, 229))  # (#E5E5E5)
            )
        )
        rules.append(rule)
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('T3:U500', worksheet_callcenter)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Оплачен']),
                format=CellFormat(backgroundColor=rgb_to_googlecolor(210, 241, 218))  # (#D2F1DA)
            )
        )
        rules.append(rule)
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('T3:U500', worksheet_callcenter)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Акт сформирован']),
                format=CellFormat(backgroundColor=rgb_to_googlecolor(210, 241, 218))  # (#D2F1DA)
            )
        )
        rules.append(rule)
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('T3:U500', worksheet_callcenter)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Акт подтверждён']),
                format=CellFormat(backgroundColor=rgb_to_googlecolor(254, 241, 204))  # (#FEF1CC)
            )
        )
        rules.append(rule)
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('T3:U500', worksheet_callcenter)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['Ошибка оплаты']),
                format=CellFormat(backgroundColor=rgb_to_googlecolor(250, 217, 214))  # (#FAD9D6)
            )
        )
        rules.append(rule)

        rules.save()

        set_frozen(worksheet_callcenter, rows=2)

    all_rows_list = []

    pass  # TODO данные отчёта

    update_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    cells.append(Cell.from_address('Z1', f'Обновлено {update_time}'))

    if cells_formatted:
        format_cell_ranges(worksheet_callcenter, cells_formatted)
    if all_rows_list:
        worksheet_callcenter.append_rows(all_rows_list, value_input_option='USER_ENTERED', table_range='A3')

    worksheet_callcenter.update_cells(cells, value_input_option='USER_ENTERED')

    return True


def update_spreadsheet_supports(sheet_item: Spreadsheet) -> bool:
    """Обновление таблицы supports"""
    spreadsheet = cloud_instance.open_by_key(sheet_item.id_drive)
    date_start, date_end, sheet_title = get_month_period_dates(sheet_item.date_period_to_update)
    sheet_title_smenas = f'{sheet_title} Смены'
    sheet_title_dopusl = f'{sheet_title} Доп.услуги'
    sheet_title_reqs = f'{sheet_title} Запросы'
    sheet_title_penalty = f'{sheet_title} Штрафы'

    try:
        worksheet_smenas = spreadsheet.worksheet(sheet_title_smenas)
    except WorksheetNotFound:
        worksheet_smenas = spreadsheet.add_worksheet(title=sheet_title_smenas, rows=1000, cols=50,
                                                     index=1 if sheet_item.date_period_to_update else 0)
        cells = []
        row = 1
        col = 1
        header = ['Дата смены', 'ФИО', 'Начало работы', 'Конец работы']
        for header_item in header:
            cells.append(Cell(row=row, col=col, value=header_item))
            col += 1
        row += 1
        col = 1

        worksheet_smenas.update_cells(cells, value_input_option='USER_ENTERED')
        format_cell_range(worksheet_smenas, 'A1:D1', fmt_gray_bold_center)
        set_frozen(worksheet_smenas, rows=1)

    try:
        worksheet_dopusl = spreadsheet.worksheet(sheet_title_dopusl)
    except WorksheetNotFound:
        worksheet_dopusl = spreadsheet.add_worksheet(title=sheet_title_dopusl, rows=5000, cols=50,
                                                     index=1 if sheet_item.date_period_to_update else 0)
        cells = []
        row = 1
        col = 1
        header = ['Перегонщик', 'Госномер', 'Услуга', 'Элементы', 'Запрос создан', 'Саппорт', 'Запрос отправлен саппорту', 'Решение', 'Запрос обработан', 'Ответ отправлен перегонщику']
        for header_item in header:
            cells.append(Cell(row=row, col=col, value=header_item))
            col += 1
        row += 1
        col = 1

        worksheet_dopusl.update_cells(cells, value_input_option='USER_ENTERED')
        format_cell_range(worksheet_dopusl, 'A1:J1', fmt_gray_bold_center)
        set_frozen(worksheet_dopusl, rows=1)

    try:
        worksheet_reqs = spreadsheet.worksheet(sheet_title_reqs)
    except WorksheetNotFound:
        worksheet_reqs = spreadsheet.add_worksheet(title=sheet_title_reqs, rows=5000, cols=50,
                                                   index=1 if sheet_item.date_period_to_update else 0)
        cells = []
        row = 1
        col = 1
        header = ['Перегонщик', 'Госномер', 'Запрос', 'Тип', 'Запрос создан', 'Саппорт', 'Запрос отправлен саппорту', 'Решение', 'Запрос обработан', 'Ответ отправлен перегонщику']
        for header_item in header:
            cells.append(Cell(row=row, col=col, value=header_item))
            col += 1
        row += 1
        col = 1

        worksheet_reqs.update_cells(cells, value_input_option='USER_ENTERED')
        format_cell_range(worksheet_reqs, 'A1:J1', fmt_gray_bold_center)
        set_frozen(worksheet_reqs, rows=1)

    try:
        worksheet_penalty = spreadsheet.worksheet(sheet_title_penalty)
    except WorksheetNotFound:
        worksheet_penalty = spreadsheet.add_worksheet(title=sheet_title_penalty, rows=500, cols=50,
                                                      index=1 if sheet_item.date_period_to_update else 0)
        cells = []
        row = 1
        col = 1
        header = ['Дата назначения', 'Саппорт', 'Категория штрафа', 'Тип штрафа', 'Кому назначен']
        for header_item in header:
            cells.append(Cell(row=row, col=col, value=header_item))
            col += 1
        row += 1
        col = 1

        worksheet_penalty.update_cells(cells, value_input_option='USER_ENTERED')
        format_cell_range(worksheet_penalty, 'A1:E1', fmt_gray_bold_center)
        set_frozen(worksheet_penalty, rows=1)

    datetime_start_text = date_start.strftime("%Y-%m-%d 10:00:00")
    datetime_end_text = (date_end + datetime.timedelta(days=1)).strftime("%Y-%m-%d 09:59:59")

    report_data_smenas = db.db_spreadsheets.get_report_data_supports_smenas(date_start, date_end)
    if report_data_smenas:
        fios_list = worksheet_smenas.col_values(2)
        row = len(fios_list) + 1
        worksheet_smenas.batch_clear([f'A2:D{row}'])

        all_rows_list = []
        cells = []

        for row_data in report_data_smenas:
            all_rows_list.append(row_data)

        update_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
        cells.append(Cell.from_address('G1', f'Обновлено {update_time}'))

        worksheet_smenas.append_rows(all_rows_list, value_input_option='USER_ENTERED', table_range='A2')
        worksheet_smenas.update_cells(cells, value_input_option='USER_ENTERED')
        worksheet_smenas.columns_auto_resize(1, 4)

    report_data_dopusl = db.db_spreadsheets.get_report_data_supports_dopusl(datetime_start_text, datetime_end_text)
    if report_data_dopusl:
        fios_list = worksheet_dopusl.col_values(2)
        row = len(fios_list) + 1
        worksheet_dopusl.batch_clear([f'A2:J{row}'])

        all_rows_list = []
        cells = []

        for row_data in report_data_dopusl:
            all_rows_list.append(row_data)

        update_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
        cells.append(Cell.from_address('M1', f'Обновлено {update_time}'))

        worksheet_dopusl.append_rows(all_rows_list, value_input_option='USER_ENTERED', table_range='A2')
        worksheet_dopusl.update_cells(cells, value_input_option='USER_ENTERED')
        worksheet_dopusl.columns_auto_resize(0, 9)

    report_data_reqs = db.db_spreadsheets.get_report_data_supports_reqs(datetime_start_text, datetime_end_text)
    if report_data_reqs:
        fios_list = worksheet_reqs.col_values(2)
        row = len(fios_list) + 1
        worksheet_reqs.batch_clear([f'A2:J{row}'])

        all_rows_list = []
        cells = []

        for row_data in report_data_reqs:
            all_rows_list.append(row_data)

        update_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
        cells.append(Cell.from_address('M1', f'Обновлено {update_time}'))

        worksheet_reqs.append_rows(all_rows_list, value_input_option='USER_ENTERED', table_range='A2')
        worksheet_reqs.update_cells(cells, value_input_option='USER_ENTERED')
        worksheet_reqs.columns_auto_resize(0, 9)

    report_data_penalty = db.db_spreadsheets.get_report_data_supports_penalty(date_start, date_end)
    if report_data_penalty:
        fios_list = worksheet_penalty.col_values(2)
        row = len(fios_list) + 1
        worksheet_penalty.batch_clear([f'A2:E{row}'])

        all_rows_list = []
        cells = []

        for row_data in report_data_penalty:
            all_rows_list.append(row_data)

        update_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
        cells.append(Cell.from_address('H1', f'Обновлено {update_time}'))

        worksheet_penalty.append_rows(all_rows_list, value_input_option='USER_ENTERED', table_range='A2')
        worksheet_penalty.update_cells(cells, value_input_option='USER_ENTERED')
        worksheet_penalty.columns_auto_resize(0, 4)

    return True


def update_spreadsheet_auto_avg_kol_by_category(sheet_item: Spreadsheet) -> bool:
    """Обновление таблицы auto_avg_kol_by_category"""
    spreadsheet = cloud_instance.open_by_key(sheet_item.id_drive)
    sheet_title = 'Среднее кол-во авто'

    try:
        worksheet = spreadsheet.worksheet(sheet_title)
    except WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=sheet_title, rows=1000, cols=50,
                                              index=1 if sheet_item.date_period_to_update else 0)

    workers_rows_list = []
    washes_rows_list = []
    cells = []

    date_start = datetime.date(2022, 11, 1)
    date_end = datetime.date.today()

    kol_periods = get_kol_periods_between_two_dates(date_start, date_end)
    if not kol_periods:
        LOGGER.error('Этого не может быть, промежуток должен быть: %s %s', date_start, date_end)
        return False

    weekdays_dict = get_weekdays_count(date_start, date_end)
    workers_tuple, washes_tuple = db.db_spreadsheets.get_report_data_auto_avg_kol(date_start, weekdays_dict)

    # Testing
    # fake = Faker()
    # workers_tuple = (
    #     (random.randint(1,7), fake.name(), random.randint(1,25), random.randint(1,20)),
    # )

    row = 1
    col = 1
    workers_rows_list_cat_1 = []
    workers_rows_list_cat_2 = []
    workers_rows_list_cat_3 = []
    for id_category in range(1, 4):
        for worker_item in workers_tuple:
            district, fio, avg_kol, kol_smenas = worker_item
            kol_avg_smenas_in_period = round(kol_smenas / kol_periods)
            if id_category == 1:
                if avg_kol >= 16:
                    workers_rows_list_cat_1.append((district, fio, avg_kol, kol_avg_smenas_in_period))
            elif id_category == 2:
                if 11 <= avg_kol <= 15:
                    workers_rows_list_cat_2.append((district, fio, avg_kol, kol_avg_smenas_in_period))
            elif id_category == 3:
                if avg_kol <= 10:
                    workers_rows_list_cat_3.append((district, fio, avg_kol, kol_avg_smenas_in_period))

    if workers_rows_list_cat_1:
        workers_rows_list_cat_1 = sorted(workers_rows_list_cat_1, key=lambda tup: tup[2], reverse=True)
    if workers_rows_list_cat_2:
        workers_rows_list_cat_2 = sorted(workers_rows_list_cat_2, key=lambda tup: tup[2], reverse=True)
    if workers_rows_list_cat_3:
        workers_rows_list_cat_3 = sorted(workers_rows_list_cat_3, key=lambda tup: tup[2], reverse=True)

    # TODO вообще-то кол-во районов нужно брать из БД, но опять же, результат нужен уже вчера
    for cur_district in range(1, 8):
        workers_rows_list.append([f'Район {cur_district}'])

        for id_category in range(1, 4):
            workers_rows_list.append([f'Категория {id_category}'])
            workers_rows_list.append(['ФИО', 'Ср. кол авто', 'Ср.выходов за период'])
            if id_category == 1 and workers_rows_list_cat_1:
                for worker_cat_item in workers_rows_list_cat_1:
                    if worker_cat_item[0] == cur_district:
                        workers_rows_list.append(worker_cat_item[1:])
            elif id_category == 2 and workers_rows_list_cat_2:
                for worker_cat_item in workers_rows_list_cat_2:
                    if worker_cat_item[0] == cur_district:
                        workers_rows_list.append(worker_cat_item[1:])
            elif id_category == 3 and workers_rows_list_cat_3:
                for worker_cat_item in workers_rows_list_cat_3:
                    if worker_cat_item[0] == cur_district:
                        workers_rows_list.append(worker_cat_item[1:])
            workers_rows_list.append([])
        workers_rows_list.append([])

    row = 1
    col = 8
    header_washes = ['Район', 'Адрес мойки', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс', 'Сред. за смену', 'Сумм. за неделю']
    for header_item in header_washes:
        cells.append(Cell(row=row, col=col, value=header_item))
        col += 1
    row = 2
    for row_data in washes_tuple:
        district, wash_name, mon, tue, wed, thu, fri, sat, sun = row_data
        wash_sum = mon + tue + wed + thu + fri + sat + sun
        wash_avg = round(wash_sum / 7)
        washes_rows_list.append((district, wash_name, mon, tue, wed, thu, fri, sat, sun, wash_avg, wash_sum))
        row += 1
    washes_rows_list = sorted(washes_rows_list, key=lambda tup: tup[-1], reverse=True)

    update_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    cells.append(Cell.from_address('T1', f'Обновлено {update_time}'))

    worksheet.batch_clear(['A1:T1000'])
    if workers_rows_list:
        worksheet.append_rows(workers_rows_list, value_input_option='USER_ENTERED', table_range='A1')
    if washes_rows_list:
        worksheet.append_rows(washes_rows_list, value_input_option='USER_ENTERED', table_range='H2')
    worksheet.update_cells(cells, value_input_option='USER_ENTERED')
    worksheet.columns_auto_resize(0, 18)

    return True


def get_period_dates(custom_date: datetime.date = None):
    """Крайние даты рабочих периодов (3 в месяц) и соответствующее им название листа ГГГГ-ММ"""
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
    # TODO он тут однобокий, не для всех методов подходит
    sheet_title = f'{date_start.strftime("%d.%m.%Y")}-{date_end.strftime("%d.%m.%Y")}'
    return (date_start, date_end, sheet_title)


def get_kol_periods_between_two_dates(start_date: datetime.date, end_date: datetime.date) -> int:
    """Сколько рабочих периодов (3 в месяц) прошло между датами"""
    if start_date > end_date:
        return None

    # сначала считаем количество полных прошедших месяцев, и раз это полные месяцы, то значит сразу умножаем на 3
    # (по 3 периода в каждом полном месяце). Затем смотрим на день конечной даты, в каком она периоде текущего месяца,
    # и прибавляем соответственно
    delta = relativedelta.relativedelta(end_date, start_date)
    left_months = delta.months + (12 * delta.years)
    kol_periods = left_months * 3

    if 1 <= end_date.day <= 10:
        kol_periods += 1
    elif 11 <= end_date.day <= 20:
        kol_periods += 2
    elif end_date.day > 20:
        kol_periods += 3

    return kol_periods


def get_month_period_dates(custom_date: datetime.date = None):
    """Крайние даты месяца и соответствующее им название листа ГГГГ-ММ"""
    period_date = custom_date if custom_date else datetime.date.today()
    date_start = period_date.replace(day=1)
    date_end = datetime.date(period_date.year, period_date.month, calendar.monthrange(period_date.year, period_date.month)[1])
    sheet_title = period_date.strftime("%Y-%m")
    return (date_start, date_end, sheet_title)


def date_range_list(start_date: datetime.date, end_date: datetime.date):
    """Список дат между датами"""
    date_list = []
    curr_date = start_date
    while curr_date <= end_date:
        date_list.append(curr_date)
        curr_date += datetime.timedelta(days=1)
    return date_list


def get_weekdays_count(date_start: datetime.date, date_end: datetime.date) -> dict:
    """Количество дней недели между датами"""
    week = {}
    for i in range((date_end - date_start).days + 1):
        day = (date_start + datetime.timedelta(days=i)).weekday()
        week[day] = week[day] + 1 if day in week else 1
    return dict(sorted(week.items()))


def get_id_cloud_folder_reports() -> str:
    """id папки в облаке для хранения отчётов"""
    pref_item = db.db_prefs.get_pref('cloud_folder_reports')
    if not pref_item:
        LOGGER.error('pref cloud_folder_reports_schedules NOT EXIST')
        return None
    return pref_item.textval


def ecn(col: int) -> str:
    """Номер столбца в его буквенное обозначение в Excel. col=1 это A
    Args:
        col (int): номер колонки (от 1);
    Returns:
        str: буквенное обозначение колонки
    """
    letters = ''
    while col:
        mod = (col - 1) % 26
        letters += chr(mod + 65)
        col = (col - 1) // 26
    return ''.join(reversed(letters))


def merge_cells(spreadsheet: gspread.spreadsheet.Spreadsheet, sheet_name: str, start_row: int, start_col: int, end_row: int, end_col: int) -> bool:
    """Объединение ячеек"""
    sheet_id = spreadsheet.worksheet(sheet_name)._properties['sheetId']  # pylint: disable=protected-access
    body = {
        "requests": [
            {
                "mergeCells": {
                    "mergeType": "MERGE_ALL",
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": start_row - 1,
                        "endRowIndex": end_row - 1,
                        "startColumnIndex": start_col - 1,
                        "endColumnIndex": end_col - 1
                    }
                }
            }
        ]
    }
    return spreadsheet.batch_update(body)


# TODO таблицы контрагентов на паузе, потом надо освежить
def parse_contragents_list_sheet():
    sheet_id = db.db_prefs.get_pref('tmp_contrag_sources_sheetid').textval
    spreadsheet = cloud_instance.open_by_key(sheet_id)
    worksheet = spreadsheet.get_worksheet(0)
    worksheet_data = worksheet.get_all_values()

    etalon_header = [
        'Контрагент',
        '№ Договора',
        'Город',
        'Документы (ссылка)',
        'Номер телефона',
        'ЛПР',
        'Почта',
        'Адрес',
        'Базовая мойка',
        'Фургон',
        'Шаттл',
        'Пылесос багажника',
        'Пылесос салона',
        'Химчистка',
        'Обезжирка',
        'Уборка клея',
        'Полировка',
        'Химчистка потолка',
        'Чернение',
        '3-х фазная мойка',
        'Подписка',
        'Бензовоз',
        'Незамерзающая жидкость'
    ]

    sheet_header = worksheet_data[1]

    if sheet_header != etalon_header:
        LOGGER.error('Нарушена структура таблицы Контрагенты - табель объектов')
        return

    del worksheet_data[:2]
    for row_data in worksheet_data:
        if not db.db_contragents.get_contragent_by_ndog(row_data[1]):
            ctr_name = row_data[0]
            ndog = row_data[1]
            city_name = row_data[2]
            docs_hyperlink = row_data[3]
            phone = row_data[4]
            fio = row_data[5]
            email = row_data[6]
            city_name = 'Питер' if city_name.lower().replace(' ', '') in ('питер', 'санкт-петербург') else city_name
            city_item = db.db_classifiers.find_classifier_object(City, name=city_name)
            id_city = city_item.id if city_item else None

            try:
                db.db_contragents.create_contragent(ctr_name, ndog, id_city, docs_hyperlink, phone, fio, email)
                LOGGER.info(f'Создан контрагент {ctr_name}')
            except Exception as ex:
                LOGGER.error(ex)

        if not db.db_contragents.get_contragent_wash_by_address(row_data[7]):
            try:  # заодно проверим, действительно ли в ячейки цен введены числа, а не слова
                contragent_item = db.db_contragents.get_contragent_by_ndog(row_data[1])
                address = row_data[7]
                cost_bm_kop = int(row_data[8]) * 100 if row_data[8].strip() else None
                cost_furgon_kop = int(row_data[9]) * 100 if row_data[9].strip() else None
                cost_shuttle_kop = int(row_data[10]) * 100 if row_data[10].strip() else None
                cost_pb_kop = int(row_data[11]) * 100 if row_data[11].strip() else None
                cost_ps_kop = int(row_data[12]) * 100 if row_data[12].strip() else None
                cost_chem_kop = int(row_data[13]) * 100 if row_data[13].strip() else None
                cost_zhir_kop = int(row_data[14]) * 100 if row_data[14].strip() else None
                cost_glue_kop = int(row_data[15]) * 100 if row_data[15].strip() else None
                cost_polir_kop = int(row_data[16]) * 100 if row_data[16].strip() else None
                cost_chempot_kop = int(row_data[17]) * 100 if row_data[17].strip() else None
                cost_chern_kop = int(row_data[18]) * 100 if row_data[18].strip() else None
                cost_fazwash_kop = int(row_data[19]) * 100 if row_data[19].strip() else None
                cost_podpisk_kop = int(row_data[20]) * 100 if row_data[20].strip() else None
                cost_benzov_kop = int(row_data[21]) * 100 if row_data[21].strip() else None
                cost_nzmrz_kop = int(row_data[22]) * 100 if row_data[22].strip() else None

                db.db_contragents.create_contragent_wash(contragent_item.id, address, cost_bm_kop, cost_furgon_kop, cost_shuttle_kop, cost_pb_kop, cost_ps_kop, cost_chem_kop,
                                                         cost_zhir_kop, cost_glue_kop, cost_polir_kop, cost_chempot_kop, cost_chern_kop, cost_fazwash_kop, cost_podpisk_kop, cost_benzov_kop, cost_nzmrz_kop)
                LOGGER.info(f'Создана мойка контрагента с адресом {address}')
            except Exception as ex:
                LOGGER.error(ex)


def update_contragents_opl_reestr_sheet():
    sheet_id = db.db_prefs.get_pref('tmp_contrag_vypl_sheetid').textval
    spreadsheet = cloud_instance.open_by_key(sheet_id)
    worksheet = spreadsheet.get_worksheet(0)

    sheet_header = worksheet.row_values(2)
    etalon_header = ['Контрагент', 'Город', 'Адрес', '№ ДОГОВОРА', 'ПЕРИОД ОКАЗАНИЯ УСЛУГ', 'Базовая мойка (ЭКОНОМ) \n(кол-во)', 'Базовая мойка (ЭКОНОМ) Сумма выполненных услуг', 'Фургон\n(кол-во)', 'Фургон\n(сумма)', 'Шаттл\n(кол-во)', 'Шаттл\n(сумма)', 'Пылесос багажника\n(кол-во)', 'Пылесос багажника (сумма)', 'Пылесос салона\n(кол-во)', 'Пылесос салона\n(сумма)', 'Химчистка\n(кол-во)', 'Химчистка\n(сумма)', 'Обезжирка\n(кол-во)', 'Обезжирка\n(сумма)',
                     'Уборка клея\n(кол-во)', 'Уборка клея\n(сумма)', 'Полировка\n(кол-во)', 'Полировка(сумма)', 'Химчистка потолка(кол-во)', 'Химчистка потолка(сумма)', 'Чернение(кол-во)', 'Чернение(сумма)', '3-х фазная мойка(кол-во)', '3-х фазная мойка(сумма)', 'Подписка(кол-во)', 'Подписка(сумма)', 'Бензовоз(кол-во)', 'Бензовоз(сумма)', 'Незамерзающая жидкость(кол-во)', 'Незамерзающая жидкость(сумма)', 'Итоговая сумма', 'Статус сверки', 'Статус оплаты', '№ АКТА']
    if sheet_header != etalon_header:
        LOGGER.error('Нарушена структура таблицы Контрагенты - реестр выплат')
        return

    cells = []

    report_data = db.db_spreadsheets.get_contragents_opl_reestr_report_data()
    if report_data:
        addresses_list = worksheet.col_values(3)
        row = len(addresses_list) + 1
        row_start = row

        # в этой таблице только добавлять к имеющимся, очищать не стоит
        # worksheet.batch_clear([f'A3:AM{row}'])
        # row = 3

        all_rows_list = []
        opl_reestr_items_list = []

        for row_data in report_data:
            # TODO говнокод, так как нечего давать задания которые нужно сдать вчера
            id_contragent_wash, id_period, contrag_name, city_name, wash_name, dog_num, period_okaz, econ_kol, cost_bm_kop, furgon_kol, cost_furgon_kop, shuttle_kol, cost_shuttle_kop, pb_kol, cost_pb_kop, ps_kol, cost_ps_kop, chem_kol, cost_chem_kop, zhir_kol, cost_zhir_kop, glue_kol, cost_glue_kop, polir_kol, cost_polir_kop, chempot_kol, cost_chempot_kop, chern_kol, cost_chern_kop, fazwash_kol, cost_fazwash_kop, podpisk_kol, cost_podpisk_kop, benzov_kol, cost_benzov_kop, nzmrz_kol, cost_nzmrz_kop, itogo_sum, sver_status, opl_status, act_num = row_data

            all_rows_list.append([contrag_name, city_name, wash_name, dog_num, period_okaz, econ_kol, None, furgon_kol, None, shuttle_kol, None, pb_kol, None, ps_kol, None, chem_kol, None, zhir_kol, None,
                                 glue_kol, None, polir_kol, None, chempot_kol, None, chern_kol, None, fazwash_kol, None, podpisk_kol, None, benzov_kol, None, nzmrz_kol, None, itogo_sum, sver_status, opl_status, act_num])

            cells.append(Cell.from_address(
                f'G{row}', f'=IFERROR(1/(1/(F{row}*{cost_bm_kop/100})))'.replace('.', ',') if cost_bm_kop else ''))
            cells.append(Cell.from_address(
                f'I{row}', f'=IFERROR(1/(1/(H{row}*{cost_furgon_kop/100})))'.replace('.', ',') if cost_furgon_kop else ''))
            cells.append(Cell.from_address(
                f'K{row}', f'=IFERROR(1/(1/(J{row}*{cost_shuttle_kop/100})))'.replace('.', ',') if cost_shuttle_kop else ''))
            cells.append(Cell.from_address(
                f'M{row}', f'=IFERROR(1/(1/(L{row}*{cost_pb_kop/100})))'.replace('.', ',') if cost_pb_kop else ''))
            cells.append(Cell.from_address(
                f'O{row}', f'=IFERROR(1/(1/(N{row}*{cost_ps_kop/100})))'.replace('.', ',') if cost_ps_kop else ''))
            cells.append(Cell.from_address(
                f'Q{row}', f'=IFERROR(1/(1/(P{row}*{cost_chem_kop/100})))'.replace('.', ',') if cost_chem_kop else ''))
            cells.append(Cell.from_address(
                f'S{row}', f'=IFERROR(1/(1/(R{row}*{cost_zhir_kop/100})))'.replace('.', ',') if cost_zhir_kop else ''))
            cells.append(Cell.from_address(
                f'U{row}', f'=IFERROR(1/(1/(T{row}*{cost_glue_kop/100})))'.replace('.', ',') if cost_glue_kop else ''))
            cells.append(Cell.from_address(
                f'W{row}', f'=IFERROR(1/(1/(V{row}*{cost_polir_kop/100})))'.replace('.', ',') if cost_polir_kop else ''))
            cells.append(Cell.from_address(
                f'Y{row}', f'=IFERROR(1/(1/(X{row}*{cost_chempot_kop/100})))'.replace('.', ',') if cost_chempot_kop else ''))
            cells.append(Cell.from_address(
                f'AA{row}', f'=IFERROR(1/(1/(Z{row}*{cost_chern_kop/100})))'.replace('.', ',') if cost_chern_kop else ''))
            cells.append(Cell.from_address(
                f'AC{row}', f'=IFERROR(1/(1/(AB{row}*{cost_fazwash_kop/100})))'.replace('.', ',') if cost_fazwash_kop else ''))
            cells.append(Cell.from_address(
                f'AE{row}', f'=IFERROR(1/(1/(AD{row}*{cost_podpisk_kop/100})))'.replace('.', ',') if cost_podpisk_kop else ''))
            cells.append(Cell.from_address(
                f'AG{row}', f'=IFERROR(1/(1/(AF{row}*{cost_benzov_kop/100})))'.replace('.', ',') if cost_benzov_kop else ''))
            cells.append(Cell.from_address(
                f'AI{row}', f'=IFERROR(1/(1/(AH{row}*{cost_nzmrz_kop/100})))'.replace('.', ',') if cost_nzmrz_kop else ''))
            cells.append(Cell.from_address(
                f'AJ{row}', f'=IFERROR(1/(1/(G{row}+I{row}+K{row}+M{row}+O{row}+Q{row}+S{row}+U{row}+W{row}+Y{row}+AA{row}+AC{row}+AE{row}+AG{row}+AI{row})))'))

            opl_reestr_items_list.append((id_contragent_wash, id_period))
            row += 1

        update_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
        cells.append(Cell.from_address('AO3', f'Обновлено {update_time}'))

        worksheet.append_rows(all_rows_list, value_input_option='USER_ENTERED', table_range=f'A{row_start}')
        worksheet.update_cells(cells, value_input_option='USER_ENTERED')

        db.db_spreadsheets.mark_opl_reestr_uploaded(opl_reestr_items_list)

    return True
