"""periodic dopsmena

Revision ID: 8e1ecbfa5cbd
Revises: e235851d61d4
Create Date: 2022-12-05 14:37:29.428937

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '8e1ecbfa5cbd'
down_revision = 'e235851d61d4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('dopsmena', sa.Column('auto_assigned', sa.Boolean(), nullable=False, comment='1 - назначено опросом после конца прошлой смены'))


def downgrade():
    op.drop_column('dopsmena', 'auto_assigned')
