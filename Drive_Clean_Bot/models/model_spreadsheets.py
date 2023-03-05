"""Модели отчётов и таблиц"""
import datetime

from sqlalchemy import (BigInteger, Boolean, Column, Date, DateTime,
                        ForeignKey, Integer, String)

from models.base import Base

# pylint: disable=missing-class-docstring,too-few-public-methods

SPREADSHEET_TYPES = {
    'schedules': 1,
    'smena_results': 2,
    'payment_registry': 4,
    'supports': 5,
    'brig_schedules': 6,
    'auto_avg_kol_by_category': 7,
}

SPREADSHEET_TYPES_CAPTIONS = {
    1: 'График работников',
    2: 'Отчёт по сменам',
    4: 'Реестр выплат',
    5: 'Саппорты',
    6: 'График работников по бригадиру',
    7: 'Среднее кол-во авто у перегонщика по категориям',
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
    id_user = Column(BigInteger, ForeignKey('users.id'),
                     comment='Юзер, которому принадлежит этот отчёт (например график работников бригадира)')
    period = Column(String(100))
    id_drive = Column(String(255), nullable=False)
    date_create = Column(DateTime, nullable=False, default=datetime.datetime.now)
    need_update = Column(Boolean, nullable=False, default=False)
    date_period_to_update = Column(Date, comment="Любая дата между началом и концом нужного периода для обновления")
    need_full_redraw = Column(Boolean, nullable=False, default=False)
    date_update = Column(DateTime)
