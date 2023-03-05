"""specprojects table

Revision ID: 73cf4885d4c6
Revises: 40886687260f
Create Date: 2022-09-02 20:21:08.895486

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '73cf4885d4c6'
down_revision = '40886687260f'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('INSERT INTO prefs (name) VALUES ("id_drive_table_specprojects")')


def downgrade():
    op.execute('DELETE FROM prefs WHERE name = "id_drive_table_specprojects"')
