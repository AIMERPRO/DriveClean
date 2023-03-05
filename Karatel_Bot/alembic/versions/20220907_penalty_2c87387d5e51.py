"""penalty

Revision ID: 2c87387d5e51
Revises: f4c090355594
Create Date: 2022-09-07 11:26:28.998392

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '2c87387d5e51'
down_revision = 'f4c090355594'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('n_washcheck_elements', sa.Column('penalty_rub', sa.Integer(),
                  nullable=False, comment='Штраф за невыполненный элемент'))

    op.execute('UPDATE n_washcheck_elements SET penalty_rub=250 WHERE id=1')
    op.execute('UPDATE n_washcheck_elements SET penalty_rub=250 WHERE id=2')
    op.execute('UPDATE n_washcheck_elements SET penalty_rub=100 WHERE id=12')
    op.execute('UPDATE n_washcheck_elements SET penalty_rub=100 WHERE id=13')
    op.execute('UPDATE n_washcheck_elements SET penalty_rub=100 WHERE id=4')
    op.execute('UPDATE n_washcheck_elements SET penalty_rub=50 WHERE id=6')
    op.execute('UPDATE n_washcheck_elements SET penalty_rub=50 WHERE id=7')
    op.execute('UPDATE n_washcheck_elements SET penalty_rub=50 WHERE id=8')
    op.execute('UPDATE n_washcheck_elements SET penalty_rub=50 WHERE id=9')
    op.execute('UPDATE n_washcheck_elements SET penalty_rub=50 WHERE id=10')
    op.execute('UPDATE n_washcheck_elements SET penalty_rub=50 WHERE id=11')


def downgrade() -> None:
    op.drop_column('n_washcheck_elements', 'penalty_rub')
