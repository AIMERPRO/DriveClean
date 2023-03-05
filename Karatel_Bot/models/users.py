"""Модели юзеров, городов, итд"""
import datetime

from sqlalchemy import (BigInteger, Boolean, Column, DateTime, ForeignKey,
                        Integer, String)
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
    'karatel': 40,
}

REG_RESULTS = {  # для проверки, зареган ли уже юзер другим админом
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


class Role(Base):
    __tablename__ = 'n_role'
    __table_args__ = {"comment": "Роли юзеров"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)

    users = relationship("User")


class User(Base):
    __tablename__ = 'users'
    __table_args__ = {
        "comment": "Юзеры; reg=0 and active=1: прошёл регистрацию, но ещё не подтверждён; reg=1 and active=0: уволен (или отменена админом регистрация), может пройти регистрацию заново; "}

    id = Column(BigInteger, primary_key=True)
    fam = Column(String(100), nullable=False)
    im = Column(String(100), nullable=False)
    nick = Column(String(100))
    id_role = Column(Integer, ForeignKey('n_role.id'), nullable=False)
    id_city = Column(Integer, ForeignKey('n_city.id'), nullable=False)
    date_reg = Column(DateTime, nullable=False, default=datetime.datetime.now)
    date_uvol = Column(DateTime)
    reg = Column(Boolean, nullable=False, default=False)
    active = Column(Boolean, nullable=False, default=True)
