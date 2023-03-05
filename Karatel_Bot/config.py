"""Конфигурационный файл"""

IS_TEST = True

# bot token (from @BotFather)
TOKEN_BOT = '1419508910:AAFTRgcKoloaDnqFu6CWyouR-PATJZoBREM'
TOKEN_DRIVECLEAN_BOT = '1418245231:AAFQ8_nMqxAlOJMM49lf7OlNRv19new54jM'

DB_USER = 'clean_drive_user'
DB_PASSWORD = 'admin'
DB_NAME = 'karatel'
DB_NAME_DRIVECLEAN_BOT = 'cleandrive'
DB_HOST = 'localhost'
DB_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
