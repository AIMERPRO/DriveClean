"""reqs expire

Revision ID: d2177c9b8086
Revises: 2aaa502af656
Create Date: 2022-10-04 17:58:20.584558

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'd2177c9b8086'
down_revision = '2aaa502af656'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('reqs_dopusl', sa.Column('expired', sa.Boolean(), nullable=False))
    op.add_column('reqs_kapot', sa.Column('expired', sa.Boolean(), nullable=False))
    op.add_column('reqs_rpn', sa.Column('expired', sa.Boolean(), nullable=False))
    op.add_column('reqs_tphelp', sa.Column('expired', sa.Boolean(), nullable=False))


def downgrade():
    op.drop_column('reqs_tphelp', 'expired')
    op.drop_column('reqs_rpn', 'expired')
    op.drop_column('reqs_kapot', 'expired')
    op.drop_column('reqs_dopusl', 'expired')
