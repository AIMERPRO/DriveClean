"""Всякие сервисные модели для самого бота"""
import datetime

from sqlalchemy import (BigInteger, Boolean, Column, Date, DateTime,
                        ForeignKey, Integer, String, Text)

from models.base import Base

# pylint: disable=missing-class-docstring,too-few-public-methods

WEEKDAYS = [
    'Понедельник',
    'Вторник',
    'Среда',
    'Четверг',
    'Пятница',
    'Суббота',
    'Воскресенье',
]

WEEKDAYS_WHEN = [
    'В понедельник',
    'Во вторник',
    'В среду',
    'В четверг',
    'В пятницу',
    'В субботу',
    'В воскресенье',
]

WEEKDAYS_NUMBERS = {
    1: 'пн.',
    2: 'вт.',
    3: 'ср.',
    4: 'чт.',
    5: 'пт.',
    6: 'сб.',
    7: 'вс.',
}

MEDIA_TYPES = {
    'photo_last_parked_car': 1,
    'screenshot_car_leftovers': 2,
    'screenshot_example': 3,
    'screenshot_district_serviceapp': 4,
    'video_kapot_confirmation': 5,
    'forgotten_stuff': 6,
    'carstatus': 7,
    'app_help': 8,
    'restricted_area': 9,
    'rpn_temperature_list': 10,
    'rpn_work_process': 11,
    'dopusl_dirty': 12,
    'dopusl_clean': 13,
    'smenaservice_dirty': 14,
    'smenaservice_clean': 15,
    'dopusl_serviceapp': 16,
}


class State(Base):
    __tablename__ = 'states'
    __table_args__ = {"comment": "Стадии меню у юзеров"}

    id_user = Column(BigInteger, primary_key=True)
    state = Column(String(255), nullable=False, comment="Номер стадии")


class Tempval(Base):
    __tablename__ = 'tempvals'
    __table_args__ = {"comment": "Временные переменные"}

    id_user = Column(BigInteger, primary_key=True)
    state = Column(String(100), primary_key=True, nullable=False,
                   comment="К какому шагу меню относится данная переменная")
    intval = Column(BigInteger)
    textval = Column(Text)
    protect = Column(Boolean, nullable=False, default=False, comment="Не будет удалено методом clear_user_tempvals()")
    date_create = Column(DateTime, nullable=False, default=datetime.datetime.now)


class Pref(Base):
    __tablename__ = 'prefs'
    __table_args__ = {"comment": "Константы и постоянные переменные"}

    name = Column(String(50), primary_key=True)
    intval = Column(BigInteger)
    textval = Column(Text)
    dateval = Column(Date)
    datetimeval = Column(DateTime)


class Resource(Base):
    __tablename__ = 'resources'
    __table_args__ = {"comment": "Файлы ресурсов и их ID"}

    name = Column(String(50), primary_key=True)
    path = Column(String(255), nullable=False, comment="Путь к файлу на сервере")
    file_id = Column(String(255), comment="TG ID")
    date_update = Column(DateTime, nullable=False, default=datetime.datetime.now)


class MediaType(Base):
    __tablename__ = 'n_media_types'
    __table_args__ = {"comment": "Типы медиа"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


class Media(Base):
    __tablename__ = 'media'
    __table_args__ = {"comment": "Медиа"}

    id = Column(BigInteger, primary_key=True)
    id_user = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    id_smena = Column(BigInteger, ForeignKey('smena.id'))
    id_smenaservice = Column(BigInteger, ForeignKey('smenaservices.id'))
    id_req_tphelp = Column(BigInteger, ForeignKey('reqs_tphelp.id'))
    id_req_rpn = Column(BigInteger, ForeignKey('reqs_rpn.id'))
    id_req_kapot = Column(BigInteger, ForeignKey('reqs_kapot.id'))
    id_req_dopusl = Column(BigInteger, ForeignKey('reqs_dopusl.id'))
    id_media_type = Column(Integer, ForeignKey('n_media_types.id'), nullable=False)
    file_id = Column(String(255), nullable=False)
    date_create = Column(DateTime, nullable=False, default=datetime.datetime.now)
    sent_to_chat = Column(
        Boolean, comment='опционально, если null то отправка в чаты не используется для этого типа медиа')


class ServiceChat(Base):
    __tablename__ = 'service_chats'
    __table_args__ = {"comment": "ID сервисных групп и каналов"}

    name = Column(String(50), primary_key=True)
    id_city = Column(Integer, ForeignKey('n_city.id'), comment="необязательно, для разбивки чатов по городам")
    chat_id = Column(String(255), comment="id чата в TG")
    hyperlink = Column(String(255), comment="ссылка на чат")
