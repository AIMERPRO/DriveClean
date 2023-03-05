"""pref rpn exclude

Revision ID: 40886687260f
Revises: f2576e91cf18
Create Date: 2022-09-01 21:14:18.856095

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '40886687260f'
down_revision = 'f2576e91cf18'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('INSERT INTO prefs (name) VALUES ("id_support_exclude_rpn")')


def downgrade():
    op.execute('DELETE FROM prefs WHERE name = "id_support_exclude_rpn"')
