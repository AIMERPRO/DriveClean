"""spr period and names

Revision ID: a7ce84b5f5f0
Revises: 2d6f02eb5a41
Create Date: 2022-05-23 21:45:57.378081

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a7ce84b5f5f0'
down_revision = '2d6f02eb5a41'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('spreadsheets', sa.Column('date_period_to_update', sa.Date(), nullable=True))
    op.execute('UPDATE n_spreadsheet_types SET name="Реестр выплат" WHERE id=3')


def downgrade():
    op.drop_column('spreadsheets', 'date_period_to_update')
    op.execute('UPDATE n_spreadsheet_types SET name="Отчёт Konsol" WHERE id=3')
