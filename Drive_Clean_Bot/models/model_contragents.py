"""Модели контрагентов"""
import datetime

from sqlalchemy import (BigInteger, Boolean, Column, Date, DateTime,
                        ForeignKey, Integer, String)

from models.base import Base

# pylint: disable=missing-class-docstring,too-few-public-methods


class Contragent(Base):
    __tablename__ = 'contragents'
    __table_args__ = {"comment": "Контрагенты"}

    id = Column(BigInteger, primary_key=True)
    ctr_name = Column(String(255), nullable=False, comment="Наименование контрагента")
    ndog = Column(String(100), nullable=False, comment="Номер договора")
    id_city = Column(Integer, ForeignKey('n_city.id'), nullable=False)
    docs_hyperlink = Column(String(100), nullable=False, comment="Ссылка на документы")
    phone = Column(String(20), nullable=False)
    fio = Column(String(255), nullable=False, comment="ЛПР")
    email = Column(String(100), nullable=False)
    date_create = Column(DateTime, nullable=False, default=datetime.datetime.now)
    active = Column(Boolean, nullable=False, default=True)


class ContragentWash(Base):
    __tablename__ = 'contragent_washes'
    __table_args__ = {"comment": "Мойки контрагентов (все цены в копейках)"}

    # TODO поля с ценами потом оформить в отдельную таблицу с периодами их действия.
    # Здесь для тестов (типа, у начальства обычно всё временное потом постоянное)

    id = Column(BigInteger, primary_key=True)
    id_contragent = Column(BigInteger, ForeignKey('contragents.id'), nullable=False)
    address = Column(String(255), nullable=False)
    cost_bm_kop = Column(Integer, comment="Бесконтактная мойка")
    cost_furgon_kop = Column(Integer, comment="Фургон")
    cost_shuttle_kop = Column(Integer, comment="Шаттл")
    cost_pb_kop = Column(Integer, comment="Пылесос багажника")
    cost_ps_kop = Column(Integer, comment="Пылесос салона")
    cost_chem_kop = Column(Integer, comment="Химчистка")
    cost_zhir_kop = Column(Integer, comment="Обезжиривание")
    cost_glue_kop = Column(Integer, comment="Удаление клея")
    cost_polir_kop = Column(Integer, comment="Полировка")
    cost_chempot_kop = Column(Integer, comment="Химчистка потолка")
    cost_chern_kop = Column(Integer, comment="Чернение")
    cost_fazwash_kop = Column(Integer, comment="Трёхфазная мойка")
    cost_podpisk_kop = Column(Integer, comment="По подписке")
    cost_benzov_kop = Column(Integer, comment="Бензовоз")
    cost_nzmrz_kop = Column(Integer, comment="Незамерзайка")
    date_create = Column(DateTime, nullable=False, default=datetime.datetime.now)
    active = Column(Boolean, nullable=False, default=True)


class ContragentOplPeriod(Base):
    __tablename__ = 'contragents_opl_periods'
    __table_args__ = {"comment": "Расчётные периоды у контрагентов"}

    id = Column(BigInteger, primary_key=True)
    date_start = Column(Date, nullable=False)
    date_end = Column(Date, nullable=False)


class ContragentOplReestr(Base):
    __tablename__ = 'contragents_opl_reestr'
    __table_args__ = {"comment": "Реестр выплат по контрагентам (для формирования выгрузки в spreadsheet)"}

    id_contragent = Column(BigInteger, ForeignKey('contragents.id'), nullable=False)
    id_contragent_wash = Column(BigInteger, ForeignKey('contragent_washes.id'), primary_key=True)
    id_period = Column(BigInteger, ForeignKey('contragents_opl_periods.id'), primary_key=True)
    uploaded_to_sheet = Column(Boolean, nullable=False, default=False, comment="Загружено в таблицу Реестр выплат")
    date_create = Column(DateTime, nullable=False, default=datetime.datetime.now)
