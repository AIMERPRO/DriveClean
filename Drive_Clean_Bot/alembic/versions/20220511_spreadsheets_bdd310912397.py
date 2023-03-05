"""spreadsheets

Revision ID: bdd310912397
Revises: fda77e8e323a
Create Date: 2022-05-11 18:13:21.756264

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bdd310912397'
down_revision = 'fda77e8e323a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('n_spreadsheet_types',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )

    op.execute('INSERT INTO n_spreadsheet_types VALUES (1, "График работников")')
    op.execute('INSERT INTO n_spreadsheet_types VALUES (2, "Отчёт по сменам")')
    op.execute('INSERT INTO n_spreadsheet_types VALUES (3, "Отчёт Konsol")')

    op.create_table('spreadsheets',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('id_type', sa.Integer(), nullable=False),
    sa.Column('id_city', sa.Integer(), nullable=True),
    sa.Column('period', sa.String(length=100), nullable=True),
    sa.Column('id_drive', sa.String(length=255), nullable=False),
    sa.Column('date_create', sa.DateTime(), nullable=False),
    sa.Column('need_update', sa.Boolean(), nullable=False),
    sa.Column('need_full_redraw', sa.Boolean(), nullable=False),
    sa.Column('date_update', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['id_city'], ['n_city.id'], ),
    sa.ForeignKeyConstraint(['id_type'], ['n_spreadsheet_types.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    op.execute('INSERT INTO prefs (name) VALUES ("cloud_folder_reports")')


def downgrade():
    op.drop_table('spreadsheets')
    op.drop_table('n_spreadsheet_types')

    op.execute('DELETE FROM prefs WHERE name = "cloud_folder_reports"')
