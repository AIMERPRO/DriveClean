"""resources

Revision ID: fda77e8e323a
Revises: 0eb0a92ed9fe
Create Date: 2022-05-10 21:25:18.318470

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fda77e8e323a'
down_revision = '0eb0a92ed9fe'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('resources',
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('path', sa.String(length=255), nullable=False),
    sa.Column('file_id', sa.String(length=255), nullable=True),
    sa.Column('date_update', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('name')
    )

    op.execute('INSERT INTO resources (name, path, date_update) VALUES ("screenshot_yandex_leftover_1", "resources/screenshot/yandex_leftover_1.jpg", NOW())')
    op.execute('INSERT INTO resources (name, path, date_update) VALUES ("screenshot_yandex_leftover_2", "resources/screenshot/yandex_leftover_2.jpg", NOW())')
    op.execute('INSERT INTO resources (name, path, date_update) VALUES ("map_districts_all", "resources/screenshot/map_districts_all.jpg", NOW())')
    op.execute('INSERT INTO resources (name, path, date_update) VALUES ("map_districts_one", "resources/screenshot/map_districts_one.jpg", NOW())')


def downgrade():
    op.drop_table('resources')
