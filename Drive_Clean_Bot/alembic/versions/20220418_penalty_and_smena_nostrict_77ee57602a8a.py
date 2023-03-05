"""penalty and smena nostrict

Revision ID: 77ee57602a8a
Revises: 3abd7f8dbf36
Create Date: 2022-04-18 16:27:40.056209

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '77ee57602a8a'
down_revision = '3abd7f8dbf36'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('penalty_category',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )

    op.execute('INSERT INTO penalty_category VALUES (1, "Фото до/после")')
    op.execute('INSERT INTO penalty_category VALUES (2, "Фото РПН")')
    op.execute('INSERT INTO penalty_category VALUES (3, "Rapid капот")')
    op.execute('INSERT INTO penalty_category VALUES (4, "Перерасход")')

    op.create_table('penalty_type',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('id_penalty_category', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.ForeignKeyConstraint(['id_penalty_category'], ['penalty_category.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )

    op.execute('INSERT INTO penalty_type VALUES (1, 1, "Нарушен регламент")')
    op.execute('INSERT INTO penalty_type VALUES (2, 1, "Смазанные фото")')
    op.execute('INSERT INTO penalty_type VALUES (3, 1, "Мутные фото")')
    op.execute('INSERT INTO penalty_type VALUES (4, 1, "Фото сделано на улице")')
    op.execute('INSERT INTO penalty_type VALUES (5, 1, "Не видно госномера")')

    op.execute('INSERT INTO penalty_type VALUES (6, 2, "Отсутствует/спущена маска")')
    op.execute('INSERT INTO penalty_type VALUES (7, 2, "Отсутствуют/повреждены перчатки")')
    op.execute('INSERT INTO penalty_type VALUES (8, 2, "Отсутствует халат")')
    op.execute('INSERT INTO penalty_type VALUES (9, 2, "Фото не соответствует регламенту")')

    op.execute('INSERT INTO penalty_type VALUES (10, 3, "Не видно номера авто")')
    op.execute('INSERT INTO penalty_type VALUES (11, 3, "Визуально капот не закрыт")')

    op.create_table('penalty',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('id_user', sa.BigInteger(), nullable=False),
    sa.Column('id_smenaservice', sa.BigInteger(), nullable=True),
    sa.Column('id_penalty_category', sa.Integer(), nullable=False),
    sa.Column('id_penalty_type', sa.Integer(), nullable=True),
    sa.Column('id_author', sa.BigInteger(), nullable=False),
    sa.Column('date_nazn', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['id_author'], ['users.id'], ),
    sa.ForeignKeyConstraint(['id_penalty_category'], ['penalty_category.id'], ),
    sa.ForeignKeyConstraint(['id_penalty_type'], ['penalty_type.id'], ),
    sa.ForeignKeyConstraint(['id_smenaservice'], ['smenaservices.id'], ),
    sa.ForeignKeyConstraint(['id_user'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    op.add_column('smena', sa.Column('nostrict', sa.Boolean(), nullable=False))


def downgrade():
    op.drop_column('smena', 'nostrict')
    op.drop_table('penalty')
    op.drop_table('penalty_type')
    op.drop_table('penalty_category')
