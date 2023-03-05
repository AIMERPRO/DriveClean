"""add autoclass shuttle

Revision ID: a760a422e155
Revises: bdd310912397
Create Date: 2022-05-13 13:39:14.180981

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a760a422e155'
down_revision = 'bdd310912397'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('INSERT INTO n_auto_class VALUES (5, "Шаттл")')


def downgrade():
    op.execute('DELETE FROM n_auto_class WHERE id = 5')
