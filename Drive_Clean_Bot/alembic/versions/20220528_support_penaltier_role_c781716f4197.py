"""support penaltier role

Revision ID: c781716f4197
Revises: c4d08cddab96
Create Date: 2022-05-28 20:44:25.467783

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c781716f4197'
down_revision = 'c4d08cddab96'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('INSERT INTO n_role VALUES (14, "Техподдержка (штрафы)")')


def downgrade():
    op.execute('DELETE FROM n_role WHERE id=14')
