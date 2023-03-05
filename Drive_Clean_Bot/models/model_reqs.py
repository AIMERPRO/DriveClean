"""Модели по запросам в техподдержку"""
import datetime

from sqlalchemy import (BigInteger, Boolean, Column, DateTime, ForeignKey,
                        Integer, String, Text)

from models.base import Base

# pylint: disable=missing-class-docstring,too-few-public-methods

REQS_DOPUSL_PURITY = {
    'dirty': 1,
    'clean': 2,
}

REQS_DOPUSL_TYPES = {
    'pb': 1,
    'ps': 2,
    'chem': 3,
    'bitum': 4,
    'prot_stekol': 5,
}

REQS_DOPUSL_REFUSE_REASONS = {
    'protr': 1,
    'photo': 2,
    'other': 99,
}


TP_HELP_TYPES = {
    'forgotten_stuff': 1,
    'carstatus': 2,
    'app_help': 3,
    'restricted_area': 4,
}


REQS_KAPOT_REFUSE_REASONS = {
    'gosnomer': 1,
    'notclosed': 2,
    'other': 99,
}


REQS_RPN_REFUSE_REASONS = {
    'halat': 1,
    'perch': 2,
    'mask': 3,
    'other': 99,
}


class DopuslTypes(Base):
    __tablename__ = 'n_dopusl_types'
    __table_args__ = {"comment": "Типы доп. услуг"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


class DopuslRefuseReason(Base):
    __tablename__ = 'n_dopusl_refuse_reasons'
    __table_args__ = {"comment": "Причины отказа в доп. услуге"}

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)


class DopuslPurity(Base):
    __tablename__ = 'n_dopusl_purity'
    __table_args__ = {"comment": "Запрос на чистые или грязные элементы"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


class ReqDopusl(Base):
    __tablename__ = 'reqs_dopusl'
    __table_args__ = {"comment": "Запросы на доп. услугу"}

    id = Column(BigInteger, primary_key=True)
    id_purity = Column(Integer, ForeignKey('n_dopusl_purity.id'))
    id_req_dirty = Column(BigInteger, comment="ID из этой же таблицы на запрос по грязным элементам")
    id_user = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    id_wash = Column(Integer, ForeignKey('washes.id'), nullable=False)
    gosnomer = Column(String(20))
    id_dopusl_type = Column(Integer, ForeignKey('n_dopusl_types.id'))
    kol_elem = Column(Integer, comment="Если химчистка, то количество элементов")
    ready = Column(Boolean, nullable=False, default=False, comment="Готов к отправке саппорту")
    sent_to_support = Column(Boolean, nullable=False, default=False, comment="Отправлено саппорту")
    sent_to_support_datetime = Column(DateTime)
    id_support = Column(BigInteger, ForeignKey('users.id'), comment="Какому саппорту отправлено")
    expired = Column(Boolean, nullable=False, default=False)
    processed_by_support = Column(Boolean, nullable=False, default=False, comment="Обработано саппортом")
    processed_by_support_datetime = Column(DateTime)
    decision = Column(Boolean, comment="Решение саппорта")
    id_refuse_reason = Column(Integer, ForeignKey('n_dopusl_refuse_reasons.id'))
    custom_refuse_reason = Column(Text)
    response_sent_to_worker = Column(Boolean, nullable=False, default=False)
    response_sent_to_worker_datetime = Column(DateTime)
    date_create = Column(DateTime, nullable=False, default=datetime.datetime.now)


class TpHelpTypes(Base):
    __tablename__ = 'n_tphelp_types'
    __table_args__ = {"comment": "Типы обращения в ТП"}

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)


class ReqTpHelp(Base):
    __tablename__ = 'reqs_tphelp'
    __table_args__ = {"comment": "Обращения в ТП"}

    id = Column(BigInteger, primary_key=True)
    id_user = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    id_tphelp_type = Column(Integer, ForeignKey('n_tphelp_types.id'), nullable=False)
    gosnomer = Column(String(20))
    commentary = Column(Text)
    ready = Column(Boolean, nullable=False, default=False)
    sent_to_support = Column(Boolean, nullable=False, default=False)
    sent_to_support_datetime = Column(DateTime)
    id_support = Column(BigInteger, ForeignKey('users.id'))
    expired = Column(Boolean, nullable=False, default=False)
    processed_by_support = Column(Boolean, nullable=False, default=False)
    processed_by_support_datetime = Column(DateTime)
    commentary_from_support = Column(Text)
    response_sent_to_worker = Column(Boolean, nullable=False, default=False)
    response_sent_to_worker_datetime = Column(DateTime)
    date_create = Column(DateTime, nullable=False, default=datetime.datetime.now)


class ReqKapotRefuseReason(Base):
    __tablename__ = 'n_reqs_kapot_refuse_reasons'
    __table_args__ = {"comment": "Причины отказа в отчёте капота"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


class ReqKapot(Base):
    __tablename__ = 'reqs_kapot'
    __table_args__ = {"comment": "Отчёты по капоту"}

    id = Column(BigInteger, primary_key=True)
    id_user = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    id_wash = Column(Integer, ForeignKey('washes.id'), nullable=False)
    gosnomer = Column(String(20))
    ready = Column(Boolean, nullable=False, default=False)
    sent_to_support = Column(Boolean, nullable=False, default=False)
    sent_to_support_datetime = Column(DateTime)
    id_support = Column(BigInteger, ForeignKey('users.id'))
    expired = Column(Boolean, nullable=False, default=False)
    processed_by_support = Column(Boolean, nullable=False, default=False)
    processed_by_support_datetime = Column(DateTime)
    decision = Column(Boolean)
    id_refuse_reason = Column(Integer, ForeignKey('n_reqs_kapot_refuse_reasons.id'))
    custom_refuse_reason = Column(Text)
    response_sent_to_worker = Column(Boolean, nullable=False, default=False)
    response_sent_to_worker_datetime = Column(DateTime)
    date_create = Column(DateTime, nullable=False, default=datetime.datetime.now)


class ReqRpnRefuseReason(Base):
    __tablename__ = 'n_reqs_rpn_refuse_reasons'
    __table_args__ = {"comment": "Причины отказа в отчёте РПН"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


class ReqRpn(Base):
    __tablename__ = 'reqs_rpn'
    __table_args__ = {"comment": "Отчёты РПН"}

    id = Column(BigInteger, primary_key=True)
    id_user = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    id_wash = Column(Integer, ForeignKey('washes.id'), nullable=False)
    gosnomer = Column(String(20))
    ready = Column(Boolean, nullable=False, default=False)
    sent_to_support = Column(Boolean, nullable=False, default=False)
    sent_to_support_datetime = Column(DateTime)
    id_support = Column(BigInteger, ForeignKey('users.id'))
    expired = Column(Boolean, nullable=False, default=False)
    processed_by_support = Column(Boolean, nullable=False, default=False)
    processed_by_support_datetime = Column(DateTime)
    decision = Column(Boolean)
    id_refuse_reason = Column(Integer, ForeignKey('n_reqs_rpn_refuse_reasons.id'))
    custom_refuse_reason = Column(Text)
    response_sent_to_worker = Column(Boolean, nullable=False, default=False)
    response_sent_to_worker_datetime = Column(DateTime)
    date_create = Column(DateTime, nullable=False, default=datetime.datetime.now)
