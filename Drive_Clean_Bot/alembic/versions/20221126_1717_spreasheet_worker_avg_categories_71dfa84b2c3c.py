"""spreasheet worker avg categories

Revision ID: 71dfa84b2c3c
Revises: 9816c932398e
Create Date: 2022-11-26 17:17:01.793353

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '71dfa84b2c3c'
down_revision = '9816c932398e'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('INSERT INTO n_spreadsheet_types VALUES (7, "Среднее кол-во авто у перегонщика по категориям")')


def downgrade():
    op.execute('DELETE FROM spreadsheets WHERE id_type = 7')
    op.execute('DELETE FROM n_spreadsheet_types WHERE id = 7')
