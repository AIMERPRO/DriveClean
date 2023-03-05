"""media and endsmena classifiers

Revision ID: 3abd7f8dbf36
Revises: a92941ea117e
Create Date: 2022-04-17 20:17:36.575914

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3abd7f8dbf36'
down_revision = 'a92941ea117e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('n_early_smena_end_reasons',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )

    op.execute('INSERT INTO n_early_smena_end_reasons VALUES (1, "Нет автомобилей на районе")')
    op.execute('INSERT INTO n_early_smena_end_reasons VALUES (99, "Другое")')

    op.create_table('n_leftover_cars_kol',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )

    op.execute('INSERT INTO n_leftover_cars_kol VALUES (1, "1-5")')
    op.execute('INSERT INTO n_leftover_cars_kol VALUES (2, "6-10")')
    op.execute('INSERT INTO n_leftover_cars_kol VALUES (3, "11-20")')
    op.execute('INSERT INTO n_leftover_cars_kol VALUES (4, "21+")')

    op.create_table('n_media_types',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )

    op.execute('INSERT INTO n_media_types VALUES (1, "Фото - последняя припаркованная машина")')
    op.execute('INSERT INTO n_media_types VALUES (2, "Скриншот - кол-во оставшихся автомобилей на карте")')
    op.execute('INSERT INTO n_media_types VALUES (3, "Скриншот - как на примере")')
    op.execute('INSERT INTO n_media_types VALUES (4, "Скриншот - района с сервисного приложения")')
    op.execute('INSERT INTO n_media_types VALUES (5, "Видео - отчёт о закрытом капоте")')   

    op.create_table('media',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('id_user', sa.BigInteger(), nullable=False),
    sa.Column('id_smena', sa.BigInteger(), nullable=True),
    sa.Column('id_media_type', sa.Integer(), nullable=False),
    sa.Column('file_id', sa.String(length=255), nullable=False),
    sa.Column('date_create', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['id_media_type'], ['n_media_types.id'], ),
    sa.ForeignKeyConstraint(['id_smena'], ['smena.id'], ),
    sa.ForeignKeyConstraint(['id_user'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    op.add_column('smena', sa.Column('id_early_smena_end_reason', sa.Integer(), nullable=True))
    op.add_column('smena', sa.Column('custom_early_smena_end_reason', sa.Text(), nullable=True))
    op.add_column('smena', sa.Column('id_leftover_cars_kol', sa.Integer(), nullable=True))
    op.add_column('smena', sa.Column('abandoned', sa.Boolean(), nullable=False))
    op.create_foreign_key('smena_ibfk_3', 'smena', 'n_leftover_cars_kol', ['id_leftover_cars_kol'], ['id'])
    op.create_foreign_key('smena_ibfk_4', 'smena', 'n_early_smena_end_reasons', ['id_early_smena_end_reason'], ['id'])


def downgrade():
    op.drop_constraint('smena_ibfk_3', 'smena', type_='foreignkey')
    op.drop_constraint('smena_ibfk_4', 'smena', type_='foreignkey')
    op.drop_column('smena', 'abandoned')
    op.drop_column('smena', 'id_leftover_cars_kol')
    op.drop_column('smena', 'custom_early_smena_end_reason')
    op.drop_column('smena', 'id_early_smena_end_reason')
    op.drop_table('media')
    op.drop_table('n_media_types')
    op.drop_table('n_leftover_cars_kol')
    op.drop_table('n_early_smena_end_reasons')
