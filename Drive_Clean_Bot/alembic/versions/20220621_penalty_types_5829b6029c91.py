"""penalty types

Revision ID: 5829b6029c91
Revises: 26b022cabe57
Create Date: 2022-06-21 18:03:44.341478

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '5829b6029c91'
down_revision = '26b022cabe57'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('penalty', sa.Column('id_smena_date', sa.BigInteger(), nullable=True))
    op.alter_column('penalty', 'id_author',
                    existing_type=mysql.BIGINT(display_width=20),
                    nullable=True,
                    existing_comment='Кто назначил штраф')
    op.create_foreign_key('penalty_ibfk_6', 'penalty', 'smena_dates', ['id_smena_date'], ['id'])

    op.execute('INSERT INTO penalty_category VALUES (50, "Прогул")')
    op.execute('INSERT INTO penalty_category VALUES (51, "Опоздание")')


def downgrade():
    op.drop_constraint('penalty_ibfk_6', 'penalty', type_='foreignkey')
    op.alter_column('penalty', 'id_author',
                    existing_type=mysql.BIGINT(display_width=20),
                    nullable=False,
                    existing_comment='Кто назначил штраф')
    op.drop_column('penalty', 'id_smena_date')

    op.execute('DELETE FROM penalty_category WHERE id IN (50,51)')
