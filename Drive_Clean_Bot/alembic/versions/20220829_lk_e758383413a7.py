"""lk

Revision ID: e758383413a7
Revises: e8d32b192480
Create Date: 2022-08-29 19:50:34.087938

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e758383413a7'
down_revision = 'e8d32b192480'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('email', sa.String(length=100), nullable=True))

    op.execute('INSERT INTO n_role VALUES (22, "Учитель")')
    op.execute('UPDATE n_role SET name="Контролёр" WHERE id=20')


def downgrade():
    op.drop_column('users', 'email')
    op.execute('DELETE FROM n_role WHERE id=22')
    op.execute('UPDATE n_role SET name="Бригадир" WHERE id=20')
