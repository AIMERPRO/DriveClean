"""skoda autoclass

Revision ID: 6d924f9d05df
Revises: 5d97c8ead630
Create Date: 2022-05-20 18:30:01.532247

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '6d924f9d05df'
down_revision = '5d97c8ead630'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('smenaservices', 'skoda_rapid')
    op.execute('INSERT INTO n_auto_class VALUES (6, "Škoda Rapid")')


def downgrade():
    op.add_column('smenaservices', sa.Column('skoda_rapid', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True))
    op.execute('DELETE FROM n_auto_class WHERE id = 6')
