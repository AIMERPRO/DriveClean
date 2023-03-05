"""smenadate smenanotify

Revision ID: 6a1334dfea1c
Revises: 3ffe7db92d90
Create Date: 2022-04-14 15:16:04.797343

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6a1334dfea1c'
down_revision = '3ffe7db92d90'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('smena_dates',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('date_smena', sa.Date(), nullable=False),
    sa.Column('finished', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )

    op.create_table('smena_notify',
    sa.Column('id_smena_date', sa.BigInteger(), nullable=False),
    sa.Column('id_user', sa.BigInteger(), nullable=False),
    sa.Column('datetime_notify', sa.DateTime(), nullable=False),
    sa.Column('response', sa.Boolean(), nullable=False),
    sa.Column('datetime_response', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['id_smena_date'], ['smena_dates.id'], ),
    sa.ForeignKeyConstraint(['id_user'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id_smena_date', 'id_user')
    )
    
    op.add_column('smena', sa.Column('id_smena_date', sa.BigInteger(), nullable=False))
    op.add_column('smena', sa.Column('finished', sa.Boolean(), nullable=False))
    op.create_foreign_key('smena_ibfk_2', 'smena', 'smena_dates', ['id_smena_date'], ['id'])
    op.drop_column('smena', 'date_smena')


def downgrade():
    op.add_column('smena', sa.Column('date_smena', sa.DATE(), nullable=False))
    op.drop_constraint('smena_ibfk_2', 'smena', type_='foreignkey')
    op.drop_column('smena', 'finished')
    op.drop_column('smena', 'id_smena_date')
    op.drop_table('smena_notify')
    op.drop_table('smena_dates')
