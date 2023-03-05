"""reqs kapot

Revision ID: 0eb0a92ed9fe
Revises: f6a3f4a38106
Create Date: 2022-05-06 21:48:28.734940

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0eb0a92ed9fe'
down_revision = 'f6a3f4a38106'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('n_reqs_kapot_refuse_reasons',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )

    op.execute('INSERT INTO n_reqs_kapot_refuse_reasons VALUES (1, "Отсутствует госномер на видео")')
    op.execute('INSERT INTO n_reqs_kapot_refuse_reasons VALUES (2, "Капот не закрыт")')
    op.execute('INSERT INTO n_reqs_kapot_refuse_reasons VALUES (99, "Другое")')

    op.create_table('reqs_kapot',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('id_user', sa.BigInteger(), nullable=False),
    sa.Column('id_wash', sa.Integer(), nullable=False),
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
    sa.ForeignKeyConstraint(['id_refuse_reason'], ['n_reqs_kapot_refuse_reasons.id'], ),
    sa.ForeignKeyConstraint(['id_support'], ['users.id'], ),
    sa.ForeignKeyConstraint(['id_user'], ['users.id'], ),
    sa.ForeignKeyConstraint(['id_wash'], ['washes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    op.add_column('media', sa.Column('id_req_kapot', sa.BigInteger(), nullable=True))
    op.create_foreign_key('media_ibfk_7', 'media', 'reqs_kapot', ['id_req_kapot'], ['id'])


def downgrade():
    op.drop_constraint('media_ibfk_7', 'media', type_='foreignkey')
    op.drop_column('media', 'id_req_kapot')
    op.drop_table('reqs_kapot')
    op.drop_table('n_reqs_kapot_refuse_reasons')
