"""pref zima_blizko

Revision ID: 34ca6218cbf7
Revises: 6a004435c93a
Create Date: 2022-05-25 10:14:17.654600

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '34ca6218cbf7'
down_revision = '6a004435c93a'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('INSERT INTO prefs (name, intval) VALUES ("zima_blizko", 0)')


def downgrade():
    op.execute('DELETE FROM prefs WHERE name = "zima_blizko"')
