"""sent_to_sheet

Revision ID: f4c090355594
Revises: ec8bbabd53b7
Create Date: 2022-08-23 18:25:58.938484

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'f4c090355594'
down_revision = 'ec8bbabd53b7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('outcheck', sa.Column('sent_to_sheet', sa.Boolean(), nullable=False))
    op.add_column('washcheck', sa.Column('sent_to_sheet', sa.Boolean(), nullable=False))

    op.execute('INSERT INTO n_spreadsheet_types VALUES (2, "Проверка/Штрафы")')

    op.execute('INSERT INTO n_washcheck_elements VALUES (12, "Зеркала заднего вида", 1, 20)')
    op.execute('INSERT INTO n_washcheck_elements VALUES (13, "Сиденья", 1, 20)')
    op.execute('INSERT INTO n_washcheck_elements VALUES (14, "Коврики, и пространство под ногами", 1, 20)')
    op.execute('UPDATE n_washcheck_elements SET score=0 WHERE id=5')


def downgrade() -> None:
    op.drop_column('washcheck', 'sent_to_sheet')
    op.drop_column('outcheck', 'sent_to_sheet')
    op.execute('DELETE FROM n_spreadsheet_types WHERE id=2')
    op.execute('DELETE FROM n_washcheck_elements WHERE id IN (12,13,14)')
    op.execute('UPDATE n_washcheck_elements SET score=10 WHERE id=5')
