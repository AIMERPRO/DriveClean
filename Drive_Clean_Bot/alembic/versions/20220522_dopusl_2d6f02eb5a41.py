"""dopusl

Revision ID: 2d6f02eb5a41
Revises: 6d924f9d05df
Create Date: 2022-05-22 14:52:02.340131

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2d6f02eb5a41'
down_revision = '6d924f9d05df'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('n_dopusl_purity',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )

    op.execute('INSERT INTO n_dopusl_purity VALUES (1, "Грязные элементы")')
    op.execute('INSERT INTO n_dopusl_purity VALUES (2, "Чистые элементы")')

    op.create_table('n_dopusl_refuse_reasons',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )

    op.execute('INSERT INTO n_dopusl_refuse_reasons VALUES (1, "Протрите влажной тряпкой")')
    op.execute('INSERT INTO n_dopusl_refuse_reasons VALUES (2, "Некачественно сделано фото")')
    op.execute('INSERT INTO n_dopusl_refuse_reasons VALUES (99, "Другое")')

    op.create_table('n_dopusl_types',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )

    op.execute('INSERT INTO n_dopusl_types VALUES (1, "Пылесос багажника")')
    op.execute('INSERT INTO n_dopusl_types VALUES (2, "Пылесос салона")')
    op.execute('INSERT INTO n_dopusl_types VALUES (3, "Химчистка")')
    op.execute('INSERT INTO n_dopusl_types VALUES (4, "Удаление битума")')

    op.create_table('reqs_dopusl',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('id_purity', sa.Integer(), nullable=True),
    sa.Column('id_req_dirty', sa.BigInteger(), nullable=True),
    sa.Column('id_user', sa.BigInteger(), nullable=False),
    sa.Column('id_wash', sa.Integer(), nullable=False),
    sa.Column('gosnomer', sa.String(length=20), nullable=True),
    sa.Column('id_dopusl_type', sa.Integer(), nullable=True),
    sa.Column('kol_elem', sa.Integer(), nullable=True),
    sa.Column('ready', sa.Boolean(), nullable=False),
    sa.Column('sent_to_support', sa.Boolean(), nullable=False),
    sa.Column('id_support', sa.BigInteger(), nullable=True),
    sa.Column('processed_by_support', sa.Boolean(), nullable=False),
    sa.Column('decision', sa.Boolean(), nullable=True),
    sa.Column('id_refuse_reason', sa.Integer(), nullable=True),
    sa.Column('custom_refuse_reason', sa.Text(), nullable=True),
    sa.Column('response_sent_to_worker', sa.Boolean(), nullable=False),
    sa.Column('date_create', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['id_dopusl_type'], ['n_dopusl_types.id'], ),
    sa.ForeignKeyConstraint(['id_purity'], ['n_dopusl_purity.id'], ),
    sa.ForeignKeyConstraint(['id_refuse_reason'], ['n_dopusl_refuse_reasons.id'], ),
    sa.ForeignKeyConstraint(['id_support'], ['users.id'], ),
    sa.ForeignKeyConstraint(['id_user'], ['users.id'], ),
    sa.ForeignKeyConstraint(['id_wash'], ['washes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    op.execute('INSERT INTO n_media_types VALUES (12, "Допуслуги - грязные элементы")')
    op.execute('INSERT INTO n_media_types VALUES (13, "Допуслуги - чистые элементы")')

    op.add_column('media', sa.Column('id_req_dopusl', sa.BigInteger(), nullable=True))
    op.create_foreign_key('media_ibfk_8', 'media', 'reqs_dopusl', ['id_req_dopusl'], ['id'])


def downgrade():
    op.drop_constraint('media_ibfk_8', 'media', type_='foreignkey')
    op.drop_column('media', 'id_req_dopusl')
    op.drop_table('reqs_dopusl')
    op.drop_table('n_dopusl_types')
    op.drop_table('n_dopusl_refuse_reasons')
    op.drop_table('n_dopusl_purity')
