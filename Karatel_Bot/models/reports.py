"""Модели отчётов и таблиц"""
import datetime

from sqlalchemy import (BigInteger, Boolean, Column, Date, DateTime,
                        ForeignKey, Integer, String)

from models.base import Base

# pylint: disable=missing-class-docstring,too-few-public-methods

SPREADSHEET_TYPES = {
    'checklist_avg': 1,
    'check_report': 2,
}

SPREADSHEET_TYPES_CAPTIONS = {
    1: 'Средний балл по проверкам',
    2: 'Проверка/Штрафы',
}


class SpreadsheetType(Base):
    __tablename__ = 'n_spreadsheet_types'
    __table_args__ = {"comment": "Типы отчётных таблиц"}

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)


class Spreadsheet(Base):
    __tablename__ = 'spreadsheets'
    __table_args__ = {"comment": "Отчётные таблицы"}

    id = Column(BigInteger, primary_key=True)
    id_type = Column(Integer, ForeignKey('n_spreadsheet_types.id'), nullable=False)
    id_city = Column(Integer, ForeignKey('n_city.id'))
    period = Column(String(100))
    id_drive = Column(String(255), nullable=False)
    date_create = Column(DateTime, nullable=False, default=datetime.datetime.now)
    need_update = Column(Boolean, nullable=False, default=False)
    date_period_to_update = Column(Date, comment="Любая дата между началом и концом нужного периода для обновления")
    need_full_redraw = Column(Boolean, nullable=False, default=False)
    date_update = Column(DateTime)
