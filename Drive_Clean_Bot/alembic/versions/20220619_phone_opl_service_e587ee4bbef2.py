"""phone opl service

Revision ID: e587ee4bbef2
Revises: df839edf6eaa
Create Date: 2022-06-19 12:30:11.934111

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e587ee4bbef2'
down_revision = 'df839edf6eaa'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('phone_opl_service', sa.String(length=20), nullable=True,
                  comment='Телефон юзера в сервисе получения оплаты. Если прочерк - у юзера нету сервиса, оплата ему кэшем'))
    op.execute('UPDATE users SET phone_opl_service = "-" WHERE id_role IN (10,11)')


def downgrade():
    op.drop_column('users', 'phone_opl_service')
