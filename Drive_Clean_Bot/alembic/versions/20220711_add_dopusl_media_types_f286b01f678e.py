"""add dopusl media types

Revision ID: f286b01f678e
Revises: 5829b6029c91
Create Date: 2022-07-11 19:31:10.139354

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f286b01f678e'
down_revision = '5829b6029c91'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('INSERT INTO n_media_types VALUES (16, "Допуслуги - скриншоты сервисного приложения")')


def downgrade():
    op.execute('DELETE FROM n_media_types WHERE id=16')
