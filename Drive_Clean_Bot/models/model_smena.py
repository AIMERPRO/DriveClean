"""Модели всего что связано со сменами"""
import datetime

from sqlalchemy import (BigInteger, Boolean, Column, Date, DateTime,
                        ForeignKey, Integer, String, Text)

from models.base import Base

# pylint: disable=missing-class-docstring,too-few-public-methods

CARSHARINGS = {
    'yandexdrive': 1,
    'citydrive': 2,
}

AUTO_CLASSES = {
    'econom': 1,
    'business': 2,
    'premium': 3,
    'furgon': 4,
    'shuttle': 5,
    'skoda_rapid': 6,
}

AUTO_SR_TYPES = {
    'plan': 1,
    'sroch': 2,
}

WASH_USL_TYPES = {
    'beskont': 1,
    'complex': 2,
}

EARLY_SMENA_END_REASONS = {
    'few_cars': 1,
    'other': 99,
}


class Carsharing(Base):
    __tablename__ = 'n_carsharings'
    __table_args__ = {"comment": "Названия каршерингов"}

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)


class AutoClass(Base):
    __tablename__ = 'n_auto_class'
    __table_args__ = {"comment": "Классы авто"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


class AutoSrType(Base):
    __tablename__ = 'n_auto_sr_type'
    __table_args__ = {"comment": "Типы срочности"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


class WashUslType(Base):
    __tablename__ = 'n_wash_usl_type'
    __table_args__ = {"comment": "Типы услуги мойки"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


class EarlySmenaEndReason(Base):
    __tablename__ = 'n_early_smena_end_reasons'
    __table_args__ = {"comment": "Виды причин раннего окончания смены"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


class DopSmena(Base):
    __tablename__ = 'dopsmena'
    __table_args__ = {"comment": "Доп. смены"}

    id_user = Column(BigInteger, ForeignKey('users.id'), primary_key=True)
    date_smena = Column(Date, default=datetime.datetime.now, primary_key=True)
    approoved = Column(Boolean)
    auto_assigned = Column(Boolean, nullable=False, default=False, comment="1 - назначено опросом после конца прошлой смены")
    date_create = Column(DateTime, nullable=False, default=datetime.datetime.now)


class SmenaDate(Base):
    __tablename__ = 'smena_dates'
    __table_args__ = {
        "comment": "Даты смен (они ночные, и переваливают за полночь. Чтобы точно знать, к какой дате какая смена относится)"}

    id = Column(BigInteger, primary_key=True)
    date_smena = Column(Date, nullable=False)
    finished = Column(Boolean, nullable=False, default=False)


class SmenaNotify(Base):
    __tablename__ = 'smena_notify'
    __table_args__ = {"comment": "Уведомления работникам с предложением начать смену"}

    id_smena_date = Column(BigInteger, ForeignKey('smena_dates.id'), primary_key=True)
    id_user = Column(BigInteger, ForeignKey('users.id'), primary_key=True)
    datetime_notify = Column(DateTime, nullable=False, default=datetime.datetime.now)
    response = Column(Boolean, nullable=False, default=False)
    datetime_response = Column(DateTime)


class Smena(Base):
    __tablename__ = 'smena'
    __table_args__ = {"comment": "Смены (ночные)"}

    id = Column(BigInteger, primary_key=True)
    id_smena_date = Column(BigInteger, ForeignKey('smena_dates.id'), nullable=False)
    id_user = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    datetime_start = Column(DateTime, nullable=False, default=datetime.datetime.now)
    datetime_end = Column(DateTime)
    id_early_smena_end_reason = Column(Integer, ForeignKey('n_early_smena_end_reasons.id'))
    custom_early_smena_end_reason = Column(Text)
    id_leftover_cars_kol = Column(Integer, ForeignKey('n_leftover_cars_kol.id'), comment="Остаток авто на смене")
    abandoned = Column(Boolean, nullable=False, default=False, comment="Брошеная смена - закрыта автоматом")
    nostrict = Column(Boolean, nullable=False, default=False,
                      comment="Для саппортов - не нужно выполнять обязательные действия при закрытии смены")
    finished = Column(Boolean, nullable=False, default=False)


class SmenaService(Base):
    __tablename__ = 'smenaservices'
    __table_args__ = {"comment": "Услуги по ночным сменам, или обособленные дневные"}

    id = Column(BigInteger, primary_key=True)
    id_user = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    id_smena = Column(BigInteger, ForeignKey('smena.id'))
    daily = Column(Boolean, nullable=False, default=False, comment="Дневная услуга, без привязки к таблице smena")
    id_wash = Column(Integer, ForeignKey('washes.id'), nullable=False)
    gosnomer = Column(String(20), nullable=False)
    id_carsharing = Column(Integer, ForeignKey('n_carsharings.id'), nullable=False)
    dispatch_photostatus = Column(Boolean, comment="Выгружены ли фото в диспетчерскую (Ситидрайв)")
    id_auto_class = Column(Integer, ForeignKey('n_auto_class.id'))
    id_auto_sr_type = Column(Integer, ForeignKey('n_auto_sr_type.id'), nullable=False)
    id_wash_usl_type = Column(Integer, ForeignKey('n_wash_usl_type.id'), nullable=False)
    omyv_percent = Column(Integer, default=0, comment="Процент от канистры залитой незамерзайки")
    date_create = Column(DateTime, nullable=False, default=datetime.datetime.now)


class Wash(Base):
    __tablename__ = 'washes'
    __table_args__ = {"comment": "Мойки"}

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    id_city = Column(Integer, ForeignKey('n_city.id'), nullable=False)
    district = Column(Integer)
    active = Column(Boolean, nullable=False, default=True)
    used_in_karatel_washcheck = Column(Boolean, nullable=False, default=False)


class WorkersCount(Base):
    __tablename__ = 'workers_count'
    __table_args__ = {"comment": "Расчётное количество работников (согласно графикам) на каждую дату смены"}

    date_smena = Column(Date, default=datetime.datetime.now, primary_key=True)
    id_city = Column(Integer, ForeignKey('n_city.id'), primary_key=True)
    kol = Column(Integer, nullable=False)
    date_update = Column(DateTime, nullable=False, default=datetime.datetime.now)
