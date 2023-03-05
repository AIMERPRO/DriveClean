
import calendar
import datetime
import logging

import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from gspread.cell import Cell
from gspread.exceptions import WorksheetNotFound
from gspread_formatting import (CellFormat, Color, NumberFormat, TextFormat,
                                format_cell_range, format_cell_ranges,
                                set_frozen)

import db
from models.reports import (SPREADSHEET_TYPES, SPREADSHEET_TYPES_CAPTIONS,
                            Spreadsheet)

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
mime_type = 'application/vnd.google-apps.spreadsheet'


def rgb_to_googlecolor(red: int, green: int, blue: int) -> Color:
    return Color(round(red/255, 2), round(green/255, 2), round(blue/255, 2))


fmt_currency = CellFormat(
    numberFormat=NumberFormat(type='NUMBER', pattern='_-* # ##0.00 ₽_-;-* # ##0.00 ₽_-;_-* "-"?? ₽_-;_-@_-')
)

fmt_lightgreen_bold_center = CellFormat(
    backgroundColor=rgb_to_googlecolor(182, 215, 168),
    textFormat=TextFormat(bold=True),
    horizontalAlignment='CENTER'
)

fmt_verylightgreen_bold_center = CellFormat(
    backgroundColor=rgb_to_googlecolor(217, 234, 211),
    textFormat=TextFormat(bold=True),
    horizontalAlignment='CENTER'
)

fmt_lightyellow_bold_center = CellFormat(
    backgroundColor=rgb_to_googlecolor(255, 242, 204),
    textFormat=TextFormat(bold=True),
    horizontalAlignment='CENTER'
)

fmt_lightpink_bold_center = CellFormat(
    backgroundColor=rgb_to_googlecolor(244, 204, 204),
    textFormat=TextFormat(bold=True),
    horizontalAlignment='CENTER'
)


def create_blank_spreadsheet_by_type(id_type, city=None, period=None):
    if id_type == SPREADSHEET_TYPES['checklist_avg']:
        return create_blank_spreadsheet_checklist_avg()
    elif id_type == SPREADSHEET_TYPES['check_report']:
        return create_blank_spreadsheet_check_report()


def create_blank_spreadsheet(spreadsheet_name, id_folder):
    file_metadata = {
        'name': spreadsheet_name,
        'mimeType': mime_type,
        'parents': [id_folder]
    }
    new_sheet = drive_api.files().create(body=file_metadata).execute()  # pylint: disable=maybe-no-member
    return new_sheet["id"]


def create_blank_spreadsheet_checklist_avg():
    pref_item = db.prefs.get_pref('cloud_folder_reports')
    if not pref_item:
        LOGGER.error('pref cloud_folder_reports NOT EXIST')
        return False
    id_folder = pref_item.textval
    spreadsheet_name = f'{SPREADSHEET_TYPES_CAPTIONS[SPREADSHEET_TYPES["checklist_avg"]]}'

    id_drive = create_blank_spreadsheet(spreadsheet_name, id_folder)
    db.spreadsheets.create_spreadsheet(SPREADSHEET_TYPES["checklist_avg"], id_drive)
    return True


def create_blank_spreadsheet_check_report():
    pref_item = db.prefs.get_pref('cloud_folder_reports')
    if not pref_item:
        LOGGER.error('pref cloud_folder_reports NOT EXIST')
        return False
    id_folder = pref_item.textval
    spreadsheet_name = f'{SPREADSHEET_TYPES_CAPTIONS[SPREADSHEET_TYPES["check_report"]]}'

    id_drive = create_blank_spreadsheet(spreadsheet_name, id_folder)
    db.spreadsheets.create_spreadsheet(SPREADSHEET_TYPES["check_report"], id_drive)
    return True


def update_spreadsheet(sheet_item):
    if sheet_item.id_type == SPREADSHEET_TYPES['checklist_avg']:
        return update_spreadsheet_checklist_avg(sheet_item)
    elif sheet_item.id_type == SPREADSHEET_TYPES['check_report']:
        return update_spreadsheet_check_report(sheet_item)


def update_spreadsheet_checklist_avg(sheet_item: Spreadsheet):
    spreadsheet = cloud_instance.open_by_key(sheet_item.id_drive)
    date_start, date_end, sheet_title = get_month_period_dates(sheet_item.date_period_to_update)

    try:
        worksheet = spreadsheet.worksheet(sheet_title)
    except WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=sheet_title, rows=1000, cols=30,
                                              index=1 if sheet_item.date_period_to_update else 0)
        cells = []
        row = 1
        col = 1
        header = ['Мойка', 'Выездная проверка', 'Стац. проверка', 'Опросник перегонщиков', 'Общая средняя оценка']
        for header_item in header:
            cells.append(Cell(row=row, col=col, value=header_item))
            col += 1
        row += 1
        col = 1

        worksheet.update_cells(cells, value_input_option='USER_ENTERED')
        format_cell_range(worksheet, 'A1:E1', fmt_lightgreen_bold_center)
        set_frozen(worksheet, rows=1)

    report_data = db.spreadsheets.get_report_data_checklist_avg(date_start, date_end)
    if report_data:
        washes_list = worksheet.col_values(1)
        row = len(washes_list)+1
        worksheet.batch_clear([f'A2:E{row}'])

        all_rows_list = []
        cells = []

        row = 2
        for row_data in report_data:
            all_rows_list.append(row_data)
            cells.append(Cell.from_address(f'E{row}', f'=ROUND((B{row}+C{row})/2)'))
            row += 1

        update_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
        cells.append(Cell.from_address('H1', f'Обновлено {update_time}'))

        worksheet.append_rows(all_rows_list, value_input_option='USER_ENTERED', table_range='A2')
        worksheet.update_cells(cells, value_input_option='USER_ENTERED')
    return True


def update_spreadsheet_check_report(sheet_item: Spreadsheet):
    if db.spreadsheets.is_exist_unsent_washcheck():
        spreadsheet = cloud_instance.open_by_key(sheet_item.id_drive)
        sheet_title_washcheck = 'Проверка моек'
        sheet_title_washcheck_penalty = 'Система штрафов мойка'

        try:
            worksheet_washcheck = spreadsheet.worksheet(sheet_title_washcheck)
        except WorksheetNotFound:
            worksheet_washcheck = spreadsheet.add_worksheet(title=sheet_title_washcheck, rows=1000, cols=20, index=0)
            cells = []
            row = 1
            col = 1
            header = ['Время проверки', 'Дата смены', 'ФИО проверяющего', 'Адрес мойки', 'Номер авто', 'Кузов вода/пена', 'Пороги',
                      'Зеркала заднего вида', 'Багажник', 'Сиденья', 'Коврики и пространство под ногами', 'Баллы']
            for header_item in header:
                cells.append(Cell(row=row, col=col, value=header_item))
                col += 1
            row += 1
            col = 1

            worksheet_washcheck.update_cells(cells, value_input_option='USER_ENTERED')
            format_cell_range(worksheet_washcheck, 'A1:L1', fmt_verylightgreen_bold_center)
            set_frozen(worksheet_washcheck, rows=1)

        try:
            worksheet_washcheck_penalty = spreadsheet.worksheet(sheet_title_washcheck_penalty)
        except WorksheetNotFound:
            worksheet_washcheck_penalty = spreadsheet.add_worksheet(
                title=sheet_title_washcheck_penalty, rows=1000, cols=20, index=0)
            cells = []
            cells_formatted = []
            row = 1
            col = 1
            header = ['Время проверки', 'Дата смены', 'ФИО проверяющего', 'Адрес мойки', 'Номер авто', 'Исполнитель', 'Кузов вода/пена/сушка', 'Пороги',
                      'Зеркала заднего вида', 'Багажник', 'Сиденья', 'Коврики и пространство под ногами', 'ОБЩАЯ СУММА']
            for header_item in header:
                cells.append(Cell(row=row, col=col, value=header_item))
                col += 1
            row += 1
            col = 1

            worksheet_washcheck_penalty.update_cells(cells, value_input_option='USER_ENTERED')

            cells_formatted.append(('A1:F1', fmt_lightyellow_bold_center))
            cells_formatted.append(('G1:L1', fmt_verylightgreen_bold_center))
            cells_formatted.append(('M1:M1', fmt_lightpink_bold_center))
            cells_formatted.append(('G:M', fmt_currency))

            format_cell_ranges(worksheet_washcheck_penalty, cells_formatted)
            set_frozen(worksheet_washcheck_penalty, rows=1)

        report_data_washcheck, report_data_washcheck_penalty = db.spreadsheets.get_report_data_check_report_washcheck()
        if report_data_washcheck or report_data_washcheck_penalty:
            update_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
            ids_lst = []

            if report_data_washcheck:
                washes_list = worksheet_washcheck.col_values(5)
                row = len(washes_list)+1
                row_start = row

                all_rows_list = []
                cells = []

                for row_data in report_data_washcheck:
                    ids_lst.append(row_data[0])
                    all_rows_list.append(row_data[1:])
                    cells.append(Cell.from_address(
                        f'L{row}', f'=IF(F{row}="выполнен",10,0)+IF(G{row}="выполнен",10,0)+IF(H{row}="выполнен",10,0)+IF(I{row}="выполнен",0,0)+IF(J{row}="выполнен",10,0)+IF(K{row}="выполнен",10,0)'))
                    row += 1

                cells.append(Cell.from_address('O1', f'Обновлено {update_time}'))

                worksheet_washcheck.append_rows(
                    all_rows_list, value_input_option='USER_ENTERED', table_range=f'A{row_start}')
                worksheet_washcheck.update_cells(cells, value_input_option='USER_ENTERED')

            if report_data_washcheck_penalty:
                washes_list = worksheet_washcheck_penalty.col_values(4)
                row = len(washes_list)+1
                row_start = row

                all_rows_list = []
                cells = []

                for row_data in report_data_washcheck_penalty:
                    all_rows_list.append(row_data)
                    cells.append(Cell.from_address(f'M{row}', f'=SUM(G{row}:L{row})'))
                    row += 1

                cells.append(Cell.from_address('P1', f'Обновлено {update_time}'))

                worksheet_washcheck_penalty.append_rows(
                    all_rows_list, value_input_option='USER_ENTERED', table_range=f'A{row_start}')
                worksheet_washcheck_penalty.update_cells(cells, value_input_option='USER_ENTERED')

            db.spreadsheets.mark_washcheck_sent_to_sheet(ids_lst)

    if db.spreadsheets.is_exist_unsent_outcheck():
        spreadsheet = cloud_instance.open_by_key(sheet_item.id_drive)
        sheet_title_outcheck = 'Отчёт каратели'
        sheet_title_outcheck_penalty = 'Система штрафов выездная проверка'

        try:
            worksheet_outcheck = spreadsheet.worksheet(sheet_title_outcheck)
        except WorksheetNotFound:
            worksheet_outcheck = spreadsheet.add_worksheet(title=sheet_title_outcheck, rows=1000, cols=20, index=0)
            cells = []
            row = 1
            col = 1
            header = ['Время проверки', 'Дата смены', 'ФИО карателя', 'Номер авто', 'Баллы', 'Мойка', 'Исполнитель']
            for header_item in header:
                cells.append(Cell(row=row, col=col, value=header_item))
                col += 1
            row += 1
            col = 1

            worksheet_outcheck.update_cells(cells, value_input_option='USER_ENTERED')
            format_cell_range(worksheet_outcheck, 'A1:G1', fmt_verylightgreen_bold_center)
            set_frozen(worksheet_outcheck, rows=1)

        try:
            worksheet_outcheck_penalty = spreadsheet.worksheet(sheet_title_outcheck_penalty)
        except WorksheetNotFound:
            worksheet_outcheck_penalty = spreadsheet.add_worksheet(
                title=sheet_title_outcheck_penalty, rows=1000, cols=20, index=0)
            cells = []
            cells_formatted = []
            row = 1
            col = 1
            header = ['Время проверки', 'Дата смены', 'ФИО проверяющего', 'Номер авто', 'Исполнитель', 'Кузов вода/пена/сушка', 'Пороги',
                      'Зеркала заднего вида', 'Багажник', 'Сиденья', 'Коврики и пространство под ногами', 'ОБЩАЯ СУММА']
            for header_item in header:
                cells.append(Cell(row=row, col=col, value=header_item))
                col += 1
            row += 1
            col = 1

            worksheet_outcheck_penalty.update_cells(cells, value_input_option='USER_ENTERED')

            cells_formatted.append(('A1:E1', fmt_lightyellow_bold_center))
            cells_formatted.append(('F1:K1', fmt_verylightgreen_bold_center))
            cells_formatted.append(('L1:L1', fmt_lightpink_bold_center))
            cells_formatted.append(('F:L', fmt_currency))

            format_cell_ranges(worksheet_outcheck_penalty, cells_formatted)
            set_frozen(worksheet_outcheck_penalty, rows=1)

        report_data_outcheck, report_data_outcheck_penalty = db.spreadsheets.get_report_data_check_report_outcheck()
        if report_data_outcheck or report_data_outcheck_penalty:
            update_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
            ids_lst = []

            if report_data_outcheck:
                gosnomers_list = worksheet_outcheck.col_values(4)
                row = len(gosnomers_list)+1
                row_start = row

                all_rows_list = []
                cells = []

                for row_data in report_data_outcheck:
                    ids_lst.append(row_data[0])
                    all_rows_list.append(row_data[1:])
                    row += 1

                cells.append(Cell.from_address('J1', f'Обновлено {update_time}'))

                worksheet_outcheck.append_rows(
                    all_rows_list, value_input_option='USER_ENTERED', table_range=f'A{row_start}')
                worksheet_outcheck.update_cells(cells, value_input_option='USER_ENTERED')

            if report_data_outcheck_penalty:
                gosnomers_list = worksheet_outcheck_penalty.col_values(4)
                row = len(gosnomers_list)+1
                row_start = row

                all_rows_list = []
                cells = []

                for row_data in report_data_outcheck_penalty:
                    all_rows_list.append(row_data)
                    cells.append(Cell.from_address(f'L{row}', f'=SUM(F{row}:K{row})'))
                    row += 1

                cells.append(Cell.from_address('P1', f'Обновлено {update_time}'))

                worksheet_outcheck_penalty.append_rows(
                    all_rows_list, value_input_option='USER_ENTERED', table_range=f'A{row_start}')
                worksheet_outcheck_penalty.update_cells(cells, value_input_option='USER_ENTERED')

            db.spreadsheets.mark_outcheck_sent_to_sheet(ids_lst)

    return True


def get_month_period_dates(custom_date=None):
    period_date = custom_date if custom_date else datetime.date.today()
    date_start = period_date.replace(day=1)
    date_end = datetime.date(period_date.year, period_date.month,
                             calendar.monthrange(period_date.year, period_date.month)[1])
    sheet_title = period_date.strftime("%Y-%m")
    return (date_start, date_end, sheet_title)
