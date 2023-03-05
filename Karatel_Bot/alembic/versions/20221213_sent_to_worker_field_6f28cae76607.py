"""sent to worker field

Revision ID: 6f28cae76607
Revises: 96e8277f7cba
Create Date: 2022-12-13 16:26:37.590825

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6f28cae76607'
down_revision = '96e8277f7cba'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('outcheck', sa.Column('sent_to_driveclean_worker', sa.Boolean(), nullable=False))
    op.add_column('washcheck', sa.Column('sent_to_driveclean_worker', sa.Boolean(), nullable=False))

    op.execute('UPDATE outcheck SET sent_to_driveclean_worker=1 WHERE complete=1')
    op.execute('UPDATE washcheck SET sent_to_driveclean_worker=1 WHERE complete=1')

    op.execute('INSERT INTO prefs (name) VALUES ("cloud_folder_photos_checked_cars")')


def downgrade() -> None:
    op.drop_column('washcheck', 'sent_to_driveclean_worker')
    op.drop_column('outcheck', 'sent_to_driveclean_worker')

    op.execute('DELETE FROM prefs WHERE name="cloud_folder_photos_checked_cars"')
