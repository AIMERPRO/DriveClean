"""checklist_avg report

Revision ID: ec8bbabd53b7
Revises: a59937a80768
Create Date: 2022-08-17 22:40:40.672599

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ec8bbabd53b7'
down_revision = 'a59937a80768'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('n_spreadsheet_types',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=100), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('name'),
                    comment='Типы отчётных таблиц'
                    )

    op.execute('INSERT INTO n_spreadsheet_types VALUES (1, "Средний балл по проверкам")')

    op.create_table('spreadsheets',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('id_type', sa.Integer(), nullable=False),
                    sa.Column('id_city', sa.Integer(), nullable=True),
                    sa.Column('period', sa.String(length=100), nullable=True),
                    sa.Column('id_drive', sa.String(length=255), nullable=False),
                    sa.Column('date_create', sa.DateTime(), nullable=False),
                    sa.Column('need_update', sa.Boolean(), nullable=False),
                    sa.Column('date_period_to_update', sa.Date(), nullable=True,
                              comment='Любая дата между началом и концом нужного периода для обновления'),
                    sa.Column('need_full_redraw', sa.Boolean(), nullable=False),
                    sa.Column('date_update', sa.DateTime(), nullable=True),
                    sa.ForeignKeyConstraint(['id_city'], ['n_city.id'], ),
                    sa.ForeignKeyConstraint(['id_type'], ['n_spreadsheet_types.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    comment='Отчётные таблицы'
                    )

    op.add_column('n_washcheck_elements', sa.Column('score', sa.Integer(), nullable=False, comment='Оценка элемента'))

    op.execute('UPDATE n_washcheck_elements SET score=25 WHERE id=1')
    op.execute('UPDATE n_washcheck_elements SET score=15 WHERE id=2')
    op.execute('UPDATE n_washcheck_elements SET score=15 WHERE id=3')
    op.execute('UPDATE n_washcheck_elements SET score=15 WHERE id=4')
    op.execute('UPDATE n_washcheck_elements SET score=10 WHERE id=5')
    op.execute('UPDATE n_washcheck_elements SET score=5 WHERE id=6')
    op.execute('UPDATE n_washcheck_elements SET score=5 WHERE id=7')
    op.execute('UPDATE n_washcheck_elements SET score=5 WHERE id=8')
    op.execute('UPDATE n_washcheck_elements SET score=5 WHERE id=9')
    op.execute('UPDATE n_washcheck_elements SET score=5 WHERE id=10')
    op.execute('UPDATE n_washcheck_elements SET score=5 WHERE id=11')

    op.execute('INSERT INTO prefs (name) VALUES ("cloud_folder_reports")')


def downgrade() -> None:
    op.drop_column('n_washcheck_elements', 'score')
    op.drop_table('spreadsheets')
    op.drop_table('n_spreadsheet_types')

    op.execute('DELETE FROM prefs WHERE name = "cloud_folder_reports"')
