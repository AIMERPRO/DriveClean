"""dopsmena otmazki

Revision ID: 5d97c8ead630
Revises: 245ac4f66c8e
Create Date: 2022-05-17 19:54:44.380462

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5d97c8ead630'
down_revision = '245ac4f66c8e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('dopsmena',
    sa.Column('id_user', sa.BigInteger(), nullable=False),
    sa.Column('date_smena', sa.Date(), nullable=False),
    sa.Column('approoved', sa.Boolean(), nullable=True),
    sa.Column('date_create', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['id_user'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id_user', 'date_smena')
    )
    
    op.create_table('otmazki',
    sa.Column('id_user', sa.BigInteger(), nullable=False),
    sa.Column('date_smena', sa.Date(), nullable=False),
    sa.Column('reason_description', sa.Text(), nullable=True),
    sa.Column('approoved', sa.Boolean(), nullable=True),
    sa.Column('date_create', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['id_user'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id_user', 'date_smena')
    )


def downgrade():
    op.drop_table('otmazki')
    op.drop_table('dopsmena')
