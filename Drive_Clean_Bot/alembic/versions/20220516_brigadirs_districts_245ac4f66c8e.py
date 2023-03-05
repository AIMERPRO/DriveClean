"""brigadirs districts

Revision ID: 245ac4f66c8e
Revises: a760a422e155
Create Date: 2022-05-16 18:04:34.025145

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '245ac4f66c8e'
down_revision = 'a760a422e155'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('brigadirs_districts',
    sa.Column('id_brigadir', sa.BigInteger(), nullable=False),
    sa.Column('id_city', sa.Integer(), nullable=False),
    sa.Column('district', sa.Integer(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('date_change', sa.Date(), nullable=False),
    sa.ForeignKeyConstraint(['id_brigadir'], ['users.id'], ),
    sa.ForeignKeyConstraint(['id_city'], ['n_city.id'], ),
    sa.PrimaryKeyConstraint('id_brigadir', 'id_city', 'district')
    )


def downgrade():
    op.drop_table('brigadirs_districts')
