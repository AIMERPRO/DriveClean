"""raw DB"""

import logging

import config
import pymysql

LOGGER = logging.getLogger('applog')


def open_connection():
    """Открытие соединения к базе"""
    return pymysql.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        passwd=config.DB_PASSWORD,
        db=config.DB_NAME,
        use_unicode=1,
        charset='utf8mb4'
    )


def open_connection_newonebot():
    """Открытие соединения к базе бота новичков"""
    return pymysql.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        passwd=config.DB_PASSWORD,
        db=config.DB_NAME_NEWONEBOT,
        use_unicode=1,
        charset='utf8mb4'
    )


def open_connection_karatelbot():
    """Открытие соединения к базе бота карателей"""
    return pymysql.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        passwd=config.DB_PASSWORD,
        db=config.DB_NAME_KARATEL,
        use_unicode=1,
        charset='utf8mb4'
    )


def close_connection(connection):
    """Закрытие соединения"""
    connection.close()
