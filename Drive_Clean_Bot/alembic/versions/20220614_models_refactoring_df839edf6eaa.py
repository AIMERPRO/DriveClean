"""models refactoring

Revision ID: df839edf6eaa
Revises: 201ad0b0cdbc
Create Date: 2022-06-14 12:35:43.509937

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'df839edf6eaa'
down_revision = '201ad0b0cdbc'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table_comment(
        'brigadirs_districts',
        'На какой район какой бригадир назначен',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'car_leftovers',
        'Остатки авто',
        existing_comment=None,
        schema=None
    )

    op.alter_column('contragent_washes', 'cost_bm_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment='Бесконтактная мойка',
                    existing_comment='Здесь и далее цены в копейках',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_furgon_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment='Фургон',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_shuttle_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment='Шаттл',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_pb_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment='Пылесос багажника',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_ps_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment='Пылесос салона',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_chem_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment='Химчистка',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_zhir_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment='Обезжиривание',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_glue_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment='Удаление клея',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_polir_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment='Полировка',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_chempot_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment='Химчистка потолка',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_chern_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment='Чернение',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_fazwash_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment='Трёхфазная мойка',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_podpisk_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment='По подписке',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_benzov_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment='Бензовоз',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_nzmrz_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment='Незамерзайка',
                    existing_nullable=True)

    op.create_table_comment(
        'contragent_washes',
        'Мойки контрагентов (все цены в копейках)',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'contragents',
        'Контрагенты',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'contragents_opl_periods',
        'Расчётные периоды у контрагентов',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'contragents_opl_reestr',
        'Реестр выплат по контрагентам (для формирования выгрузки в spreadsheet)',
        existing_comment=None,
        schema=None
    )

    op.drop_column('contragents_opl_reestr', 'locked')

    op.create_table_comment(
        'districts',
        'Районы',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'dopsmena',
        'Доп. смены',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'media',
        'Медиа',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'n_auto_class',
        'Классы авто',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'n_auto_sr_type',
        'Типы срочности',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'n_carsharings',
        'Названия каршерингов',
        existing_comment=None,
        schema=None
    )

    op.alter_column('n_city', 'icon',
                    existing_type=mysql.VARCHAR(length=1),
                    comment='Иконка (эмодзи) для обозначения города в текстовых отчётах',
                    existing_nullable=True)

    op.create_table_comment(
        'n_city',
        'Города',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'n_dopusl_purity',
        'Запрос на чистые или грязные элементы',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'n_dopusl_refuse_reasons',
        'Причины отказа в доп. услуге',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'n_dopusl_types',
        'Типы доп. услуг',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'n_early_smena_end_reasons',
        'Виды причин раннего окончания смены',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'n_leftover_cars_kol',
        'Количества остатков авто',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'n_media_types',
        'Типы медиа',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'n_reqs_kapot_refuse_reasons',
        'Причины отказа в отчёте капота',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'n_reqs_rpn_refuse_reasons',
        'Причины отказа в отчёте РПН',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'n_role',
        'Роли юзеров',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'n_spreadsheet_types',
        'Типы отчётных таблиц',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'n_tphelp_types',
        'Типы обращения в ТП',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'n_wash_usl_type',
        'Типы услуги мойки',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'otmazki',
        'Запросы на отгулы',
        existing_comment=None,
        schema=None
    )

    op.alter_column('penalty', 'id_author',
                    existing_type=mysql.BIGINT(display_width=20),
                    comment='Кто назначил штраф',
                    existing_nullable=False)

    op.create_table_comment(
        'penalty',
        'Штрафы',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'penalty_category',
        'Категории штрафов',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'penalty_type',
        'Конкретная причина штрафа',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'prefs',
        'Константы и постоянные переменные',
        existing_comment=None,
        schema=None
    )

    op.alter_column('reqs_dopusl', 'id_req_dirty',
                    existing_type=mysql.BIGINT(display_width=20),
                    comment='ID из этой же таблицы на запрос по грязным элементам',
                    existing_nullable=True)

    op.alter_column('reqs_dopusl', 'kol_elem',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment='Если химчистка, то количество элементов',
                    existing_nullable=True)

    op.alter_column('reqs_dopusl', 'ready',
                    existing_type=mysql.TINYINT(display_width=1),
                    comment='Готов к отправке саппорту',
                    existing_nullable=False)

    op.alter_column('reqs_dopusl', 'sent_to_support',
                    existing_type=mysql.TINYINT(display_width=1),
                    comment='Отправлено саппорту',
                    existing_nullable=False)

    op.alter_column('reqs_dopusl', 'id_support',
                    existing_type=mysql.BIGINT(display_width=20),
                    comment='Какому саппорту отправлено',
                    existing_nullable=True)

    op.alter_column('reqs_dopusl', 'processed_by_support',
                    existing_type=mysql.TINYINT(display_width=1),
                    comment='Обработано саппортом',
                    existing_nullable=False)

    op.alter_column('reqs_dopusl', 'decision',
                    existing_type=mysql.TINYINT(display_width=1),
                    comment='Решение саппорта',
                    existing_nullable=True)

    op.create_table_comment(
        'reqs_dopusl',
        'Запросы на доп. услугу',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'reqs_kapot',
        'Отчёты по капоту',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'reqs_rpn',
        'Отчёты РПН',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'reqs_tphelp',
        'Обращения в ТП',
        existing_comment=None,
        schema=None
    )

    op.alter_column('resources', 'path',
                    existing_type=mysql.VARCHAR(length=255),
                    comment='Путь к файлу на сервере',
                    existing_nullable=False)

    op.alter_column('resources', 'file_id',
                    existing_type=mysql.VARCHAR(length=255),
                    comment='TG ID',
                    existing_nullable=True)

    op.create_table_comment(
        'resources',
        'Файлы ресурсов и их ID',
        existing_comment=None,
        schema=None
    )

    op.alter_column('schedules', 'week_template',
                    existing_type=mysql.VARCHAR(length=7),
                    comment='7 цифр на каждый день недели',
                    existing_nullable=False)

    op.create_table_comment(
        'schedules',
        'Графики работников',
        existing_comment=None,
        schema=None
    )

    op.alter_column('smena', 'id_leftover_cars_kol',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment='Остаток авто на смене',
                    existing_nullable=True)

    op.alter_column('smena', 'abandoned',
                    existing_type=mysql.TINYINT(display_width=1),
                    comment='Брошеная смена - закрыта автоматом',
                    existing_nullable=False)

    op.alter_column('smena', 'nostrict',
                    existing_type=mysql.TINYINT(display_width=1),
                    comment='Для саппортов - не нужно выполнять обязательные действия при закрытии смены',
                    existing_nullable=False)

    op.create_table_comment(
        'smena',
        'Смены (ночные)',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'smena_dates',
        'Даты смен (они ночные, и переваливают за полночь. Чтобы точно знать, к какой дате какая смена относится)',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'smena_notify',
        'Уведомления работникам с предложением начать смену',
        existing_comment=None,
        schema=None
    )

    op.alter_column('smenaservices', 'daily',
                    existing_type=mysql.TINYINT(display_width=1),
                    comment='Дневная услуга, без привязки к таблице smena',
                    existing_nullable=False)

    op.alter_column('smenaservices', 'dispatch_photostatus',
                    existing_type=mysql.TINYINT(display_width=1),
                    comment='Выгружены ли фото в диспетчерскую (Ситидрайв)',
                    existing_nullable=True)

    op.alter_column('smenaservices', 'omyv_percent',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment='Процент от канистры залитой незамерзайки',
                    existing_nullable=True)

    op.alter_column('smenaservices', 'sent_to_karatel_mysql',
                    existing_type=mysql.TINYINT(display_width=1),
                    comment='Отправлено в удалённую БД карателей',
                    existing_nullable=False)

    op.create_table_comment(
        'smenaservices',
        'Услуги по ночным сменам, или обособленные дневные',
        existing_comment=None,
        schema=None
    )

    op.alter_column('spreadsheets', 'date_period_to_update',
                    existing_type=sa.DATE(),
                    comment='Любая дата между началом и концом нужного периода для обновления',
                    existing_nullable=True)

    op.create_table_comment(
        'spreadsheets',
        'Отчётные таблицы',
        existing_comment=None,
        schema=None
    )

    op.alter_column('states', 'state',
                    existing_type=mysql.VARCHAR(length=255),
                    comment='Номер стадии',
                    existing_nullable=False)

    op.create_table_comment(
        'states',
        'Стадии меню у юзеров',
        existing_comment=None,
        schema=None
    )

    op.alter_column('tempvals', 'state',
                    existing_type=mysql.VARCHAR(length=100),
                    comment='К какому шагу меню относится данная переменная',
                    existing_nullable=False)

    op.alter_column('tempvals', 'protect',
                    existing_type=mysql.TINYINT(display_width=1),
                    comment='Не будет удалено методом clear_user_tempvals()',
                    existing_nullable=False)

    op.create_table_comment(
        'tempvals',
        'Временные переменные',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'users',
        'Юзеры; reg=0 and active=1: прошёл регистрацию, но ещё не подтверждён; reg=1 and active=0: уволен (или отменена админом регистрация), может пройти регистрацию заново; ',
        existing_comment=None,
        schema=None
    )

    op.create_table_comment(
        'washes',
        'Мойки',
        existing_comment=None,
        schema=None
    )


def downgrade():
    op.drop_table_comment(
        'washes',
        existing_comment='Мойки',
        schema=None
    )

    op.drop_table_comment(
        'users',
        existing_comment='Юзеры; reg=0 and active=1: прошёл регистрацию, но ещё не подтверждён; reg=1 and active=0: уволен (или отменена админом регистрация), может пройти регистрацию заново; ',
        schema=None
    )

    op.drop_table_comment(
        'tempvals',
        existing_comment='Временные переменные',
        schema=None
    )

    op.alter_column('tempvals', 'protect',
                    existing_type=mysql.TINYINT(display_width=1),
                    comment=None,
                    existing_comment='Не будет удалено методом clear_user_tempvals()',
                    existing_nullable=False)

    op.alter_column('tempvals', 'state',
                    existing_type=mysql.VARCHAR(length=100),
                    comment=None,
                    existing_comment='К какому шагу меню относится данная переменная',
                    existing_nullable=False)

    op.drop_table_comment(
        'states',
        existing_comment='Стадии меню у юзеров',
        schema=None
    )

    op.alter_column('states', 'state',
                    existing_type=mysql.VARCHAR(length=255),
                    comment=None,
                    existing_comment='Номер стадии',
                    existing_nullable=False)

    op.drop_table_comment(
        'spreadsheets',
        existing_comment='Отчётные таблицы',
        schema=None
    )

    op.alter_column('spreadsheets', 'date_period_to_update',
                    existing_type=sa.DATE(),
                    comment=None,
                    existing_comment='Любая дата между началом и концом нужного периода для обновления',
                    existing_nullable=True)

    op.drop_table_comment(
        'smenaservices',
        existing_comment='Услуги по ночным сменам, или обособленные дневные',
        schema=None
    )

    op.alter_column('smenaservices', 'sent_to_karatel_mysql',
                    existing_type=mysql.TINYINT(display_width=1),
                    comment=None,
                    existing_comment='Отправлено в удалённую БД карателей',
                    existing_nullable=False)

    op.alter_column('smenaservices', 'omyv_percent',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment=None,
                    existing_comment='Процент от канистры залитой незамерзайки',
                    existing_nullable=True)

    op.alter_column('smenaservices', 'dispatch_photostatus',
                    existing_type=mysql.TINYINT(display_width=1),
                    comment=None,
                    existing_comment='Выгружены ли фото в диспетчерскую (Ситидрайв)',
                    existing_nullable=True)

    op.alter_column('smenaservices', 'daily',
                    existing_type=mysql.TINYINT(display_width=1),
                    comment=None,
                    existing_comment='Дневная услуга, без привязки к таблице smena',
                    existing_nullable=False)

    op.drop_table_comment(
        'smena_notify',
        existing_comment='Уведомления работникам с предложением начать смену',
        schema=None
    )

    op.drop_table_comment(
        'smena_dates',
        existing_comment='Даты смен (они ночные, и переваливают за полночь. Чтобы точно знать, к какой дате какая смена относится)',
        schema=None
    )

    op.drop_table_comment(
        'smena',
        existing_comment='Смены (ночные)',
        schema=None
    )

    op.alter_column('smena', 'nostrict',
                    existing_type=mysql.TINYINT(display_width=1),
                    comment=None,
                    existing_comment='Для саппортов - не нужно выполнять обязательные действия при закрытии смены',
                    existing_nullable=False)

    op.alter_column('smena', 'abandoned',
                    existing_type=mysql.TINYINT(display_width=1),
                    comment=None,
                    existing_comment='Брошеная смена - закрыта автоматом',
                    existing_nullable=False)

    op.alter_column('smena', 'id_leftover_cars_kol',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment=None,
                    existing_comment='Остаток авто на смене',
                    existing_nullable=True)

    op.drop_table_comment(
        'schedules',
        existing_comment='Графики работников',
        schema=None
    )

    op.alter_column('schedules', 'week_template',
                    existing_type=mysql.VARCHAR(length=7),
                    comment=None,
                    existing_comment='7 цифр на каждый день недели',
                    existing_nullable=False)

    op.drop_table_comment(
        'resources',
        existing_comment='Файлы ресурсов и их ID',
        schema=None
    )

    op.alter_column('resources', 'file_id',
                    existing_type=mysql.VARCHAR(length=255),
                    comment=None,
                    existing_comment='TG ID',
                    existing_nullable=True)

    op.alter_column('resources', 'path',
                    existing_type=mysql.VARCHAR(length=255),
                    comment=None,
                    existing_comment='Путь к файлу на сервере',
                    existing_nullable=False)

    op.drop_table_comment(
        'reqs_tphelp',
        existing_comment='Обращения в ТП',
        schema=None
    )

    op.drop_table_comment(
        'reqs_rpn',
        existing_comment='Отчёты РПН',
        schema=None
    )

    op.drop_table_comment(
        'reqs_kapot',
        existing_comment='Отчёты по капоту',
        schema=None
    )

    op.drop_table_comment(
        'reqs_dopusl',
        existing_comment='Запросы на доп. услугу',
        schema=None
    )

    op.alter_column('reqs_dopusl', 'decision',
                    existing_type=mysql.TINYINT(display_width=1),
                    comment=None,
                    existing_comment='Решение саппорта',
                    existing_nullable=True)

    op.alter_column('reqs_dopusl', 'processed_by_support',
                    existing_type=mysql.TINYINT(display_width=1),
                    comment=None,
                    existing_comment='Обработано саппортом',
                    existing_nullable=False)

    op.alter_column('reqs_dopusl', 'id_support',
                    existing_type=mysql.BIGINT(display_width=20),
                    comment=None,
                    existing_comment='Какому саппорту отправлено',
                    existing_nullable=True)

    op.alter_column('reqs_dopusl', 'sent_to_support',
                    existing_type=mysql.TINYINT(display_width=1),
                    comment=None,
                    existing_comment='Отправлено саппорту',
                    existing_nullable=False)

    op.alter_column('reqs_dopusl', 'ready',
                    existing_type=mysql.TINYINT(display_width=1),
                    comment=None,
                    existing_comment='Готов к отправке саппорту',
                    existing_nullable=False)

    op.alter_column('reqs_dopusl', 'kol_elem',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment=None,
                    existing_comment='Если химчистка, то количество элементов',
                    existing_nullable=True)

    op.alter_column('reqs_dopusl', 'id_req_dirty',
                    existing_type=mysql.BIGINT(display_width=20),
                    comment=None,
                    existing_comment='ID из этой же таблицы на запрос по грязным элементам',
                    existing_nullable=True)

    op.drop_table_comment(
        'prefs',
        existing_comment='Константы и постоянные переменные',
        schema=None
    )

    op.drop_table_comment(
        'penalty_type',
        existing_comment='Конкретная причина штрафа',
        schema=None
    )

    op.drop_table_comment(
        'penalty_category',
        existing_comment='Категории штрафов',
        schema=None
    )

    op.drop_table_comment(
        'penalty',
        existing_comment='Штрафы',
        schema=None
    )

    op.alter_column('penalty', 'id_author',
                    existing_type=mysql.BIGINT(display_width=20),
                    comment=None,
                    existing_comment='Кто назначил штраф',
                    existing_nullable=False)

    op.drop_table_comment(
        'otmazki',
        existing_comment='Запросы на отгулы',
        schema=None
    )

    op.drop_table_comment(
        'n_wash_usl_type',
        existing_comment='Типы услуги мойки',
        schema=None
    )

    op.drop_table_comment(
        'n_tphelp_types',
        existing_comment='Типы обращения в ТП',
        schema=None
    )

    op.drop_table_comment(
        'n_spreadsheet_types',
        existing_comment='Типы отчётных таблиц',
        schema=None
    )

    op.drop_table_comment(
        'n_role',
        existing_comment='Роли юзеров',
        schema=None
    )

    op.drop_table_comment(
        'n_reqs_rpn_refuse_reasons',
        existing_comment='Причины отказа в отчёте РПН',
        schema=None
    )

    op.drop_table_comment(
        'n_reqs_kapot_refuse_reasons',
        existing_comment='Причины отказа в отчёте капота',
        schema=None
    )

    op.drop_table_comment(
        'n_media_types',
        existing_comment='Типы медиа',
        schema=None
    )

    op.drop_table_comment(
        'n_leftover_cars_kol',
        existing_comment='Количества остатков авто',
        schema=None
    )

    op.drop_table_comment(
        'n_early_smena_end_reasons',
        existing_comment='Виды причин раннего окончания смены',
        schema=None
    )

    op.drop_table_comment(
        'n_dopusl_types',
        existing_comment='Типы доп. услуг',
        schema=None
    )

    op.drop_table_comment(
        'n_dopusl_refuse_reasons',
        existing_comment='Причины отказа в доп. услуге',
        schema=None
    )

    op.drop_table_comment(
        'n_dopusl_purity',
        existing_comment='Запрос на чистые или грязные элементы',
        schema=None
    )

    op.drop_table_comment(
        'n_city',
        existing_comment='Города',
        schema=None
    )

    op.alter_column('n_city', 'icon',
                    existing_type=mysql.VARCHAR(length=1),
                    comment=None,
                    existing_comment='Иконка (эмодзи) для обозначения города в текстовых отчётах',
                    existing_nullable=True)

    op.drop_table_comment(
        'n_carsharings',
        existing_comment='Названия каршерингов',
        schema=None
    )

    op.drop_table_comment(
        'n_auto_sr_type',
        existing_comment='Типы срочности',
        schema=None
    )

    op.drop_table_comment(
        'n_auto_class',
        existing_comment='Классы авто',
        schema=None
    )

    op.drop_table_comment(
        'media',
        existing_comment='Медиа',
        schema=None
    )

    op.drop_table_comment(
        'dopsmena',
        existing_comment='Доп. смены',
        schema=None
    )

    op.drop_table_comment(
        'districts',
        existing_comment='Районы',
        schema=None
    )

    op.add_column('contragents_opl_reestr', sa.Column('locked', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False,
                  comment='Из строки таблицы Реестр выплат сформирован акт на оплату, дальнейшее обновление и изменение цифр нежелательно'))

    op.drop_table_comment(
        'contragents_opl_reestr',
        existing_comment='Реестр выплат по контрагентам (для формирования выгрузки в spreadsheet)',
        schema=None
    )

    op.drop_table_comment(
        'contragents_opl_periods',
        existing_comment='Расчётные периоды у контрагентов',
        schema=None
    )

    op.drop_table_comment(
        'contragents',
        existing_comment='Контрагенты',
        schema=None
    )

    op.drop_table_comment(
        'contragent_washes',
        existing_comment='Мойки контрагентов (все цены в копейках)',
        schema=None
    )

    op.alter_column('contragent_washes', 'cost_nzmrz_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment=None,
                    existing_comment='Незамерзайка',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_benzov_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment=None,
                    existing_comment='Бензовоз',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_podpisk_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment=None,
                    existing_comment='По подписке',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_fazwash_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment=None,
                    existing_comment='Трёхфазная мойка',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_chern_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment=None,
                    existing_comment='Чернение',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_chempot_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment=None,
                    existing_comment='Химчистка потолка',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_polir_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment=None,
                    existing_comment='Полировка',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_glue_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment=None,
                    existing_comment='Удаление клея',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_zhir_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment=None,
                    existing_comment='Обезжиривание',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_chem_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment=None,
                    existing_comment='Химчистка',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_ps_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment=None,
                    existing_comment='Пылесос салона',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_pb_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment=None,
                    existing_comment='Пылесос багажника',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_shuttle_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment=None,
                    existing_comment='Шаттл',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_furgon_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment=None,
                    existing_comment='Фургон',
                    existing_nullable=True)

    op.alter_column('contragent_washes', 'cost_bm_kop',
                    existing_type=mysql.INTEGER(display_width=11),
                    comment='Здесь и далее цены в копейках',
                    existing_comment='Бесконтактная мойка',
                    existing_nullable=True)

    op.drop_table_comment(
        'car_leftovers',
        existing_comment='Остатки авто',
        schema=None
    )

    op.drop_table_comment(
        'brigadirs_districts',
        existing_comment='На какой район какой бригадир назначен',
        schema=None
    )
