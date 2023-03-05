"""servicechats and support daily

Revision ID: 6a004435c93a
Revises: a7ce84b5f5f0
Create Date: 2022-05-24 17:11:33.990676

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6a004435c93a'
down_revision = 'a7ce84b5f5f0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('service_chats',
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('id_city', sa.Integer(), nullable=True, comment='необязательно, для разбивки чатов по городам'),
    sa.Column('chat_id', sa.String(length=255), nullable=True, comment='id чата в TG'),
    sa.ForeignKeyConstraint(['id_city'], ['n_city.id'], ),
    sa.PrimaryKeyConstraint('name'),
    comment='ID сервисных чатов и каналов'
    )

    op.execute('INSERT INTO service_chats (name) VALUES ("major")')
    op.execute('INSERT INTO n_role VALUES (13, "Техподдержка (день)")')


def downgrade():
    op.drop_table('service_chats')
    op.execute('DELETE FROM n_role WHERE id=13')
