"""Всякие сервисные модели для самого бота"""
import datetime

from sqlalchemy import (BigInteger, Boolean, Column, Date, DateTime,
                        ForeignKey, Integer, String, Text)

from models.base import Base

# pylint: disable=missing-class-docstring,too-few-public-methods


MEDIA_FORMATS = {
    'photo': 1,
    'video': 2,
}

MEDIA_TYPES = {
    'outcheck': 2,
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


class MediaFormat(Base):
    __tablename__ = 'n_media_formats'
    __table_args__ = {"comment": "Форматы медиа (фото, видео)"}

    id = Column(Integer, primary_key=True)
    name = Column(String(20), nullable=False, unique=True)


class MediaType(Base):
    __tablename__ = 'n_media_types'
    __table_args__ = {"comment": "Типы медиа (к какой ситуации относятся)"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


class Media(Base):
    __tablename__ = 'media'
    __table_args__ = {"comment": "Медиа"}

    id = Column(BigInteger, primary_key=True)
    id_user = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    id_outcheck = Column(BigInteger, ForeignKey('outcheck.id'))
    id_washcheck_element = Column(Integer, ForeignKey('n_washcheck_elements.id'))
    id_media_format = Column(Integer, ForeignKey('n_media_formats.id'), nullable=False)
    id_media_type = Column(Integer, ForeignKey('n_media_types.id'), nullable=False)
    file_id = Column(String(255), nullable=False)
    date_create = Column(DateTime, nullable=False, default=datetime.datetime.now)
    cloud_file_id = Column(String(35))


class ServiceChat(Base):
    __tablename__ = 'service_chats'
    __table_args__ = {"comment": "ID сервисных групп и каналов"}

    name = Column(String(50), primary_key=True)
    id_city = Column(Integer, ForeignKey('n_city.id'), comment="необязательно, для разбивки чатов по городам")
    chat_id = Column(String(255), comment="id чата в TG")
    hyperlink = Column(String(255), comment="ссылка на чат")
