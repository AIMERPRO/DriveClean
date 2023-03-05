"""remove konsol 3 report

Revision ID: 9816c932398e
Revises: 467edd9b80b8
Create Date: 2022-11-21 18:13:17.287063

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '9816c932398e'
down_revision = '467edd9b80b8'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('DELETE FROM spreadsheets WHERE id_type = 3')
    op.execute('DELETE FROM n_spreadsheet_types WHERE id = 3')
    op.execute('DELETE FROM service_chats WHERE name = "citydrive_photo"')


def downgrade():
    op.execute('INSERT INTO n_spreadsheet_types VALUES (3, "Отчёт Konsol")')
    op.execute('INSERT INTO service_chats (name) VALUES ("citydrive_photo")')
