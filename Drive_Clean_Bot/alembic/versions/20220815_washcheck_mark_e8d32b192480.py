"""washcheck mark

Revision ID: e8d32b192480
Revises: 5fa8835c02df
Create Date: 2022-08-15 20:56:11.620846

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e8d32b192480'
down_revision = '5fa8835c02df'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('washes', sa.Column('used_in_karatel_washcheck', sa.Boolean(), nullable=False))


def downgrade():
    op.drop_column('washes', 'used_in_karatel_washcheck')
