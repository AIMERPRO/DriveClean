"""smenaserv autoclass nullable

Revision ID: a92941ea117e
Revises: 6a1334dfea1c
Create Date: 2022-04-14 18:13:34.545557

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'a92941ea117e'
down_revision = '6a1334dfea1c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('smenaservices', sa.Column('dispatch_photostatus', sa.Boolean(), nullable=True))
    op.alter_column('smenaservices', 'id_auto_class',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=True)


def downgrade():
    op.alter_column('smenaservices', 'id_auto_class',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=False)
    op.drop_column('smenaservices', 'dispatch_photostatus')
