"""reqs datetimes

Revision ID: 2aaa502af656
Revises: 73cf4885d4c6
Create Date: 2022-09-10 18:47:12.403083

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '2aaa502af656'
down_revision = '73cf4885d4c6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('reqs_kapot', sa.Column('sent_to_support_datetime', sa.DateTime(), nullable=True))
    op.add_column('reqs_kapot', sa.Column('processed_by_support_datetime', sa.DateTime(), nullable=True))
    op.add_column('reqs_kapot', sa.Column('response_sent_to_worker_datetime', sa.DateTime(), nullable=True))
    op.add_column('reqs_rpn', sa.Column('sent_to_support_datetime', sa.DateTime(), nullable=True))
    op.add_column('reqs_rpn', sa.Column('processed_by_support_datetime', sa.DateTime(), nullable=True))
    op.add_column('reqs_rpn', sa.Column('response_sent_to_worker_datetime', sa.DateTime(), nullable=True))
    op.add_column('reqs_tphelp', sa.Column('sent_to_support_datetime', sa.DateTime(), nullable=True))
    op.add_column('reqs_tphelp', sa.Column('processed_by_support_datetime', sa.DateTime(), nullable=True))
    op.add_column('reqs_tphelp', sa.Column('response_sent_to_worker_datetime', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('reqs_tphelp', 'response_sent_to_worker_datetime')
    op.drop_column('reqs_tphelp', 'processed_by_support_datetime')
    op.drop_column('reqs_tphelp', 'sent_to_support_datetime')
    op.drop_column('reqs_rpn', 'response_sent_to_worker_datetime')
    op.drop_column('reqs_rpn', 'processed_by_support_datetime')
    op.drop_column('reqs_rpn', 'sent_to_support_datetime')
    op.drop_column('reqs_kapot', 'response_sent_to_worker_datetime')
    op.drop_column('reqs_kapot', 'processed_by_support_datetime')
    op.drop_column('reqs_kapot', 'sent_to_support_datetime')
