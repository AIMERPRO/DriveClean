"""tphelp

Revision ID: 77abbb7324a8
Revises: 77ee57602a8a
Create Date: 2022-04-26 20:32:39.524263

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '77abbb7324a8'
down_revision = '77ee57602a8a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('n_tphelp_types',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )

    op.execute('INSERT INTO n_tphelp_types VALUES (1, "Уведомить о забытых вещах")')
    op.execute('INSERT INTO n_tphelp_types VALUES (2, "Уведомить о состоянии автомобиля")')
    op.execute('INSERT INTO n_tphelp_types VALUES (3, "Помощь с сервисным приложением")')
    op.execute('INSERT INTO n_tphelp_types VALUES (4, "Уведомить об авто на закрытой территории")')

    op.create_table('reqs_tphelp',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('id_user', sa.BigInteger(), nullable=False),
    sa.Column('id_tphelp_type', sa.Integer(), nullable=False),
    sa.Column('gosnomer', sa.String(length=20), nullable=True),
    sa.Column('commentary', sa.Text(), nullable=True),
    sa.Column('ready', sa.Boolean(), nullable=False),
    sa.Column('sent_to_support', sa.Boolean(), nullable=False),
    sa.Column('id_support', sa.BigInteger(), nullable=True),
    sa.Column('processed_by_support', sa.Boolean(), nullable=False),
    sa.Column('commentary_from_support', sa.Text(), nullable=True),
    sa.Column('response_sent_to_worker', sa.Boolean(), nullable=False),
    sa.Column('date_create', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['id_support'], ['users.id'], ),
    sa.ForeignKeyConstraint(['id_tphelp_type'], ['n_tphelp_types.id'], ),
    sa.ForeignKeyConstraint(['id_user'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    op.add_column('media', sa.Column('id_req_tphelp', sa.BigInteger(), nullable=True))
    op.create_foreign_key('media_ibfk_4', 'media', 'reqs_tphelp', ['id_req_tphelp'], ['id'])

    op.execute('INSERT INTO n_media_types VALUES (6, "Обращение в ТП - забытые вещи")')
    op.execute('INSERT INTO n_media_types VALUES (7, "Обращение в ТП - состояние авто")')
    op.execute('INSERT INTO n_media_types VALUES (8, "Обращение в ТП - приложение")')
    op.execute('INSERT INTO n_media_types VALUES (9, "Обращение в ТП - закрытая территория")')


def downgrade():
    op.drop_constraint('media_ibfk_4', 'media', type_='foreignkey')
    op.drop_column('media', 'id_req_tphelp')
    op.drop_table('reqs_tphelp')
    op.drop_table('n_tphelp_types')
    op.execute('DELETE FROM n_media_types WHERE id IN (6,7,8,9)')
