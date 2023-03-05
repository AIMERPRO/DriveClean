"""head support

Revision ID: e235851d61d4
Revises: 71dfa84b2c3c
Create Date: 2022-11-27 15:16:21.882203

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'e235851d61d4'
down_revision = '71dfa84b2c3c'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('INSERT INTO prefs (name) VALUES ("id_head_support")')


def downgrade():
    op.execute('DELETE FROM prefs WHERE name = "id_head_support"')
