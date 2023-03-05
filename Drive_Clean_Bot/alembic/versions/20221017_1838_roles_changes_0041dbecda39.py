"""roles changes

Revision ID: 0041dbecda39
Revises: d2177c9b8086
Create Date: 2022-10-17 18:38:47.617960

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '0041dbecda39'
down_revision = 'd2177c9b8086'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('INSERT INTO n_role VALUES (40, "Спецпроекты")')
    op.execute('UPDATE users SET id_role = 5 WHERE id_role = 11')
    op.execute('DELETE FROM n_role WHERE id = 11')


def downgrade():
    op.execute('INSERT INTO n_role VALUES (1, "Руководитель")')
    op.execute('UPDATE users SET id_role = 5 WHERE id_role = 40')
    op.execute('DELETE FROM n_role WHERE id = 40')
