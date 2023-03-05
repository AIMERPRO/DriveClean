"""supports report

Revision ID: 5fa8835c02df
Revises: 3e5ae2c5aa2c
Create Date: 2022-07-22 15:33:25.827055

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5fa8835c02df'
down_revision = '3e5ae2c5aa2c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('reqs_dopusl', sa.Column('sent_to_support_datetime', sa.DateTime(), nullable=True))
    op.add_column('reqs_dopusl', sa.Column('processed_by_support_datetime', sa.DateTime(), nullable=True))
    op.add_column('reqs_dopusl', sa.Column('response_sent_to_worker_datetime', sa.DateTime(), nullable=True))

    op.execute('INSERT INTO n_spreadsheet_types VALUES (5, "Саппорты")')


def downgrade():
    op.drop_column('reqs_dopusl', 'response_sent_to_worker_datetime')
    op.drop_column('reqs_dopusl', 'processed_by_support_datetime')
    op.drop_column('reqs_dopusl', 'sent_to_support_datetime')

    op.execute('DELETE FROM n_spreadsheet_types WHERE id=5')
