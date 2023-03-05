"""brig_schedules report

Revision ID: 467edd9b80b8
Revises: 0041dbecda39
Create Date: 2022-10-20 18:41:07.636242

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '467edd9b80b8'
down_revision = '0041dbecda39'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('spreadsheets', sa.Column('id_user', sa.BigInteger(), nullable=True,
                  comment='Юзер, которому принадлежит этот отчёт (например график работников бригадира)'))
    op.create_foreign_key('spreadsheets_ibfk_3', 'spreadsheets', 'users', ['id_user'], ['id'])

    op.execute('INSERT INTO n_spreadsheet_types VALUES (6, "График работников по конкретному бригадиру")')


def downgrade():
    op.drop_constraint('spreadsheets_ibfk_3', 'spreadsheets', type_='foreignkey')
    op.drop_column('spreadsheets', 'id_user')

    op.execute('DELETE FROM spreadsheets WHERE id_type = 6')
    op.execute('DELETE FROM n_spreadsheet_types WHERE id = 6')
