"""city active and icon

Revision ID: d48c1109e609
Revises: 821b80b2859c
Create Date: 2022-06-02 14:35:40.444142

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd48c1109e609'
down_revision = '821b80b2859c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('n_city', sa.Column('icon', sa.String(length=1), nullable=True))
    op.add_column('n_city', sa.Column('active', sa.Boolean(), nullable=False))

    op.execute('UPDATE n_city SET icon="🌃" WHERE id=1')
    op.execute('UPDATE n_city SET icon="🌉" WHERE id=2')
    op.execute('UPDATE n_city SET icon="🏔" WHERE id=3')

    # отключаем Казань
    op.execute('UPDATE n_city SET active=1 WHERE id!=3')
    op.execute('UPDATE washes SET active=0 WHERE id_city=3')
    op.execute('DELETE FROM spreadsheets WHERE id_city=3')


def downgrade():
    op.drop_column('n_city', 'active')
    op.drop_column('n_city', 'icon')
