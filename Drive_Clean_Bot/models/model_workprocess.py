"""Модели по рабочим процессам"""
import datetime

from sqlalchemy import (BigInteger, Boolean, Column, Date, DateTime,
                        ForeignKey, Integer, String, Text)

from models.base import Base

# pylint: disable=missing-class-docstring,too-few-public-methods


PENALTY_CATEGORIES = {
    'photo_before_after': 1,
    'photo_rpn': 2,
    'kapot': 3,
    'pererashod': 4,
    'progul': 50,
    'opozd': 51,
}


class LeftoverCarsKol(Base):
    __tablename__ = 'n_leftover_cars_kol'
    __table_args__ = {"comment": "Количества остатков авто"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


class CarLeftover(Base):
    __tablename__ = 'car_leftovers'
    __table_args__ = {"comment": "Остатки авто"}

    id_city = Column(Integer, ForeignKey('n_city.id'), primary_key=True)
    id_smena_date = Column(BigInteger, ForeignKey('smena_dates.id'), primary_key=True)
    kol_leftover = Column(Integer, nullable=False)
    id_brigadir = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    date_create = Column(DateTime, nullable=False, default=datetime.datetime.now)


class PenaltyCategory(Base):
    __tablename__ = 'penalty_category'
    __table_args__ = {"comment": "Категории штрафов"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


class PenaltyType(Base):
    __tablename__ = 'penalty_type'
    __table_args__ = {"comment": "Конкретная причина штрафа"}

    id = Column(Integer, primary_key=True)
    id_penalty_category = Column(Integer, ForeignKey('penalty_category.id'), nullable=False)
    name = Column(String(100), nullable=False, unique=True)


class Penalty(Base):
    __tablename__ = 'penalty'
    __table_args__ = {"comment": "Штрафы"}

    id = Column(BigInteger, primary_key=True)
    id_user = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    id_smena_date = Column(BigInteger, ForeignKey('smena_dates.id'))
    id_smenaservice = Column(BigInteger, ForeignKey('smenaservices.id'))
    id_penalty_category = Column(Integer, ForeignKey('penalty_category.id'), nullable=False)
    id_penalty_type = Column(Integer, ForeignKey('penalty_type.id'))
    id_author = Column(BigInteger, ForeignKey('users.id'), comment="Кто назначил штраф")
    date_nazn = Column(DateTime, nullable=False, default=datetime.datetime.now)


class BrigadirOnDistrict(Base):
    __tablename__ = 'brigadirs_districts'
    __table_args__ = {"comment": "На какой район какой бригадир назначен"}

    id_brigadir = Column(BigInteger, ForeignKey('users.id'), primary_key=True)
    id_city = Column(Integer, ForeignKey('n_city.id'), primary_key=True)
    district = Column(Integer, primary_key=True)
    active = Column(Boolean, nullable=False, default=True)
    date_change = Column(Date, nullable=False, default=datetime.datetime.now)


class Otmazki(Base):
    __tablename__ = 'otmazki'
    __table_args__ = {"comment": "Запросы на отгулы"}

    id_user = Column(BigInteger, ForeignKey('users.id'), primary_key=True)
    date_smena = Column(Date, default=datetime.datetime.now, primary_key=True)
    # TODO на все поля TEXT (да и вообще на все текстовые, заполняемые юзерами)
    # в самом боте желательно сделать проверку на большую длину
    reason_description = Column(Text)
    approoved = Column(Boolean)
    date_create = Column(DateTime, nullable=False, default=datetime.datetime.now)


class Schedule(Base):
    __tablename__ = 'schedules'
    __table_args__ = {"comment": "Графики работников"}

    id = Column(BigInteger, primary_key=True)
    id_user = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    week_template = Column(String(7), nullable=False, comment="7 цифр на каждый день недели")
    date_start = Column(Date, nullable=False, default=datetime.datetime.now)
    date_end = Column(Date)
    approoved = Column(Boolean, nullable=False, default=False)
    active = Column(Boolean, nullable=False, default=False)
