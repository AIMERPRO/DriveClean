"""remove old karatel

Revision ID: f2576e91cf18
Revises: e758383413a7
Create Date: 2022-09-01 19:52:51.544060

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'f2576e91cf18'
down_revision = 'e758383413a7'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('smenaservices', 'sent_to_karatel_mysql')


def downgrade():
    op.add_column('smenaservices', sa.Column('sent_to_karatel_mysql', mysql.TINYINT(display_width=1),
                  autoincrement=False, nullable=False, default=0, comment='Отправлено в удалённую БД карателей'))
