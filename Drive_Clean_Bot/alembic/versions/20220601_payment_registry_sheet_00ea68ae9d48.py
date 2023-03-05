"""payment registry sheet

Revision ID: 00ea68ae9d48
Revises: c9bda73e0881
Create Date: 2022-06-01 10:25:43.676519

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '00ea68ae9d48'
down_revision = 'c9bda73e0881'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('UPDATE n_spreadsheet_types SET name="Отчёт Konsol" WHERE id=3')
    op.execute('INSERT INTO n_spreadsheet_types VALUES (4, "Реестр выплат")')


def downgrade():
    op.execute('DELETE FROM n_spreadsheet_types WHERE id=4')
    op.execute('UPDATE n_spreadsheet_types SET name="Реестр выплат" WHERE id=3')
