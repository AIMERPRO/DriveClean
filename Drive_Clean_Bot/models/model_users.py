"""Модели юзеров, городов, итд"""
import datetime

from sqlalchemy import (BigInteger, Boolean, Column, Date, DateTime,
                        ForeignKey, Integer, String)
from sqlalchemy.orm import relationship

from models.base import Base

# pylint: disable=missing-class-docstring,too-few-public-methods

CITIES = {
    'moscow': 1,
    'piter': 2,
    'kazan': 3,
}

ROLES = {
    'pending': 5,
    'admin': 10,
    'support': 12,
    'support_daily': 13,
    'support_penaltier': 14,
    'brigadir': 20,
    'karatel': 21,
    'teacher': 22,
    'worker': 30,
    'specprojects': 40,
}

REG_RESULTS = {  # используется в проверке, не зарегал ли уже этого юзера другой админ
    'success': 1,
    'already_reg': 2,
}


class City(Base):
    __tablename__ = 'n_city'
    __table_args__ = {"comment": "Города"}

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    icon = Column(String(1), comment="Иконка (эмодзи) для обозначения города в текстовых отчётах")
    active = Column(Boolean, nullable=False, default=True)

    users = relationship("User")


class District(Base):
    __tablename__ = 'districts'
    __table_args__ = {"comment": "Районы"}

    id_city = Column(Integer, ForeignKey('n_city.id'), primary_key=True)
    district = Column(Integer, primary_key=True)


class Role(Base):
    __tablename__ = 'n_role'
    __table_args__ = {"comment": "Роли юзеров"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


class User(Base):
    __tablename__ = 'users'
    __table_args__ = {
        "comment": "Юзеры; reg=0 and active=1: прошёл регистрацию, но ещё не подтверждён; reg=1 and active=0: уволен (или отменена админом регистрация), может пройти регистрацию заново; "}

    id = Column(BigInteger, primary_key=True)
    fam = Column(String(100), nullable=False)
    im = Column(String(100), nullable=False)
    ot = Column(String(100))
    nick = Column(String(100))
    email = Column(String(100))
    datar = Column(Date, nullable=False)
    phone = Column(String(20), nullable=False)
    phone_opl_service = Column(
        String(20), comment="Телефон юзера в сервисе получения оплаты. Если прочерк - у юзера нету сервиса, оплата ему кэшем")
    id_role = Column(Integer, ForeignKey('n_role.id'), nullable=False)
    id_city = Column(Integer, ForeignKey('n_city.id'), nullable=False)
    district = Column(Integer)
    date_reg = Column(DateTime, nullable=False, default=datetime.datetime.now)
    date_uvol = Column(DateTime)
    reg = Column(Boolean, nullable=False, default=False)
    active = Column(Boolean, nullable=False, default=True)
