"""reqs rpn

Revision ID: f6a3f4a38106
Revises: 77abbb7324a8
Create Date: 2022-05-05 21:55:07.481843

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f6a3f4a38106'
down_revision = '77abbb7324a8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('n_reqs_rpn_refuse_reasons',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )

    op.execute('INSERT INTO n_reqs_rpn_refuse_reasons VALUES (1, "Отсутствует халат")')
    op.execute('INSERT INTO n_reqs_rpn_refuse_reasons VALUES (2, "Отсутствуют или повреждены перчатки")')
    op.execute('INSERT INTO n_reqs_rpn_refuse_reasons VALUES (3, "Отсутствует или не до конца надета маска")')
    op.execute('INSERT INTO n_reqs_rpn_refuse_reasons VALUES (99, "Другое")')

    op.create_table('rpn',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('id_smena_date', sa.BigInteger(), nullable=False),
    sa.Column('id_wash', sa.Integer(), nullable=False),
    sa.Column('file_id_temperature_list', sa.String(length=255), nullable=True),
    sa.Column('id_user', sa.BigInteger(), nullable=False),
    sa.Column('date_create', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['id_smena_date'], ['smena_dates.id'], ),
    sa.ForeignKeyConstraint(['id_user'], ['users.id'], ),
    sa.ForeignKeyConstraint(['id_wash'], ['washes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    op.create_table('reqs_rpn',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('id_user', sa.BigInteger(), nullable=False),
    sa.Column('id_rpn', sa.BigInteger(), nullable=False),
    sa.Column('gosnomer', sa.String(length=20), nullable=True),
    sa.Column('ready', sa.Boolean(), nullable=False),
    sa.Column('sent_to_support', sa.Boolean(), nullable=False),
    sa.Column('id_support', sa.BigInteger(), nullable=True),
    sa.Column('processed_by_support', sa.Boolean(), nullable=False),
    sa.Column('decision', sa.Boolean(), nullable=True),
    sa.Column('id_refuse_reason', sa.Integer(), nullable=True),
    sa.Column('custom_refuse_reason', sa.Text(), nullable=True),
    sa.Column('response_sent_to_worker', sa.Boolean(), nullable=False),
    sa.Column('date_create', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['id_refuse_reason'], ['n_reqs_rpn_refuse_reasons.id'], ),
    sa.ForeignKeyConstraint(['id_rpn'], ['rpn.id'], ),
    sa.ForeignKeyConstraint(['id_support'], ['users.id'], ),
    sa.ForeignKeyConstraint(['id_user'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    op.add_column('media', sa.Column('id_rpn', sa.BigInteger(), nullable=True))
    op.add_column('media', sa.Column('id_req_rpn', sa.BigInteger(), nullable=True))
    op.create_foreign_key('media_ibfk_5', 'media', 'rpn', ['id_rpn'], ['id'])
    op.create_foreign_key('media_ibfk_6', 'media', 'reqs_rpn', ['id_req_rpn'], ['id'])

    op.execute('INSERT INTO n_media_types VALUES (10, "РПН - температурный лист")')
    op.execute('INSERT INTO n_media_types VALUES (11, "РПН - рабочий процесс")')


def downgrade():
    op.drop_constraint('media_ibfk_5', 'media', type_='foreignkey')
    op.drop_constraint('media_ibfk_6', 'media', type_='foreignkey')
    op.drop_column('media', 'id_rpn')
    op.drop_table('reqs_rpn')
    op.drop_table('rpn')
    op.drop_table('n_reqs_rpn_refuse_reasons')

    op.execute('DELETE FROM n_media_types WHERE id IN (10,11)')
