"""smenaservice karatel sql

Revision ID: c9bda73e0881
Revises: c781716f4197
Create Date: 2022-05-29 16:55:12.738520

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c9bda73e0881'
down_revision = 'c781716f4197'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('smenaservices', sa.Column('sent_to_karatel_mysql', sa.Boolean(), nullable=False))


def downgrade():
    op.drop_column('smenaservices', 'sent_to_karatel_mysql')
