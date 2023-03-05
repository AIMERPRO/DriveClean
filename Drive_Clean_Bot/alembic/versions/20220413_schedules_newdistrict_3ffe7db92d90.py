"""schedules

Revision ID: 3ffe7db92d90
Revises: 3fc658a0967f
Create Date: 2022-04-13 14:42:57.003380

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3ffe7db92d90'
down_revision = '3fc658a0967f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('schedules',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('id_user', sa.BigInteger(), nullable=False),
    sa.Column('week_template', sa.String(length=7), nullable=False),
    sa.Column('date_start', sa.Date(), nullable=False),
    sa.Column('date_end', sa.Date(), nullable=True),
    sa.Column('approoved', sa.Boolean(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['id_user'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    op.execute('INSERT INTO districts VALUES (2, 2)')


def downgrade():
    op.drop_table('schedules')
    op.execute('DELETE FROM districts WHERE id_city=2 AND district=2')
