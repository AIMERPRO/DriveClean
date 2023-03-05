"""car leftovers

Revision ID: c4d08cddab96
Revises: 34ca6218cbf7
Create Date: 2022-05-26 10:03:10.910346

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4d08cddab96'
down_revision = '34ca6218cbf7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('car_leftovers',
    sa.Column('id_city', sa.Integer(), nullable=False),
    sa.Column('id_smena_date', sa.BigInteger(), nullable=False),
    sa.Column('kol_leftover', sa.Integer(), nullable=False),
    sa.Column('id_brigadir', sa.BigInteger(), nullable=False),
    sa.Column('date_create', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['id_brigadir'], ['users.id'], ),
    sa.ForeignKeyConstraint(['id_city'], ['n_city.id'], ),
    sa.ForeignKeyConstraint(['id_smena_date'], ['smena_dates.id'], ),
    sa.PrimaryKeyConstraint('id_city', 'id_smena_date')
    )


def downgrade():
    op.drop_table('car_leftovers')
