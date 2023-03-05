"""workers count

Revision ID: 26b022cabe57
Revises: e587ee4bbef2
Create Date: 2022-06-19 18:09:19.986874

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '26b022cabe57'
down_revision = 'e587ee4bbef2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('workers_count',
                    sa.Column('date_smena', sa.Date(), nullable=False),
                    sa.Column('id_city', sa.Integer(), nullable=False),
                    sa.Column('kol', sa.Integer(), nullable=False),
                    sa.Column('date_update', sa.DateTime(), nullable=False),
                    sa.ForeignKeyConstraint(['id_city'], ['n_city.id'], ),
                    sa.PrimaryKeyConstraint('date_smena', 'id_city'),
                    comment='Расчётное количество работников (согласно графикам) на каждую дату смены'
                    )


def downgrade():
    op.drop_table('workers_count')
