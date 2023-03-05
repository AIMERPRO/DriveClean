"""Конфигурационный файл"""

IS_TEST = True

# bot token (from @BotFather)
TOKEN = ''

DB_USER = ''
DB_PASSWORD = ''
DB_NAME = ''
DB_HOST = 'localhost'
DB_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'

DB_NAME_NEWONEBOT = ''
DB_NAME_KARATEL = ''
