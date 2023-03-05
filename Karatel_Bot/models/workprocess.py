"""Всё что связано с проверкой чистоты авто"""
import datetime

from sqlalchemy import (BigInteger, Boolean, Column, DateTime, ForeignKey,
                        Integer, String)

from models.base import Base

# pylint: disable=missing-class-docstring,too-few-public-methods


class WashcheckElements(Base):
    __tablename__ = 'n_washcheck_elements'
    __table_args__ = {"comment": "Элементы чеклиста, по которым выполняются услуги на мойке"}

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    score = Column(Integer, nullable=False, default=0, comment="Оценка элемента")
    penalty_rub = Column(Integer, nullable=False, default=0, comment="Штраф за невыполненный элемент")
    active = Column(Boolean, nullable=False, default=True)


class Washcheck(Base):
    __tablename__ = 'washcheck'
    __table_args__ = {"comment": "Проверенные карателем мойки"}

    id = Column(BigInteger, primary_key=True)
    id_user = Column(BigInteger, ForeignKey('users.id'), nullable=False,
                     comment="ID карателя, который проверил эту мойку")
    id_wash = Column(Integer, nullable=False)
    gosnomer = Column(String(20), nullable=False)
    complete = Column(Boolean, nullable=False, default=False)
    datetime_create = Column(DateTime, nullable=False, default=datetime.datetime.now)
    sent_to_sheet = Column(Boolean, nullable=False, default=False)
    sent_to_driveclean_worker = Column(Boolean, nullable=False, default=False)


class WashcheckChecklist(Base):
    __tablename__ = 'washcheck_checklist'
    __table_args__ = {"comment": "Чеклист по услугам на проверяемых мойках"}

    id = Column(BigInteger, primary_key=True)
    id_washcheck = Column(BigInteger, ForeignKey('washcheck.id'), nullable=False)
    id_element = Column(Integer, ForeignKey('n_washcheck_elements.id'), nullable=False)
    result = Column(Boolean, nullable=False, default=False)
    datetime_create = Column(DateTime, nullable=False, default=datetime.datetime.now)


class Outcheck(Base):
    __tablename__ = 'outcheck'
    __table_args__ = {"comment": "Выездные проверки"}

    id = Column(BigInteger, primary_key=True)
    id_user = Column(BigInteger, ForeignKey('users.id'), nullable=False, comment="ID карателя")
    gosnomer = Column(String(20), nullable=False)
    complete = Column(Boolean, nullable=False, default=False)
    datetime_create = Column(DateTime, nullable=False, default=datetime.datetime.now)
    sent_to_sheet = Column(Boolean, nullable=False, default=False)
    sent_to_driveclean_worker = Column(Boolean, nullable=False, default=False)


class OutcheckChecklist(Base):
    __tablename__ = 'outcheck_checklist'
    __table_args__ = {"comment": "Чеклист по выездным проверкам"}

    id = Column(BigInteger, primary_key=True)
    id_outcheck = Column(BigInteger, ForeignKey('outcheck.id'), nullable=False)
    id_element = Column(Integer, ForeignKey('n_washcheck_elements.id'), nullable=False)
    result = Column(Boolean, nullable=False, default=False)
    datetime_create = Column(DateTime, nullable=False, default=datetime.datetime.now)
