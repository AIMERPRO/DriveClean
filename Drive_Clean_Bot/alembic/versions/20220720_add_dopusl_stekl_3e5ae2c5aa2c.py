"""add dopusl stekl

Revision ID: 3e5ae2c5aa2c
Revises: f286b01f678e
Create Date: 2022-07-20 22:16:40.782018

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3e5ae2c5aa2c'
down_revision = 'f286b01f678e'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('INSERT INTO n_dopusl_types VALUES (5, "Протирка стёкол")')


def downgrade():
    op.execute('DELETE FROM n_dopusl_types WHERE id=5')
