"""contragents periods and prefs fields

Revision ID: 201ad0b0cdbc
Revises: df3ef2396559
Create Date: 2022-06-10 13:21:09.066420

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '201ad0b0cdbc'
down_revision = 'df3ef2396559'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('contragents_opl_periods',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('date_start', sa.Date(), nullable=False),
                    sa.Column('date_end', sa.Date(), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )

    # начальный период
    op.execute('INSERT INTO contragents_opl_periods (date_start, date_end) VALUES ("2022-05-16", "2022-05-31")')

    op.create_table('contragents_opl_reestr',
                    sa.Column('id_contragent', sa.BigInteger(), nullable=False),
                    sa.Column('id_contragent_wash', sa.BigInteger(), nullable=False),
                    sa.Column('id_period', sa.BigInteger(), nullable=False),
                    sa.Column('uploaded_to_sheet', sa.Boolean(), nullable=False,
                              comment='Загружено в таблицу Реестр выплат'),
                    sa.Column('locked', sa.Boolean(), nullable=False,
                              comment='Из строки таблицы Реестр выплат сформирован акт на оплату, дальнейшее обновление и изменение цифр нежелательно'),
                    sa.Column('date_create', sa.DateTime(), nullable=False),
                    sa.ForeignKeyConstraint(['id_contragent'], ['contragents.id'], ),
                    sa.ForeignKeyConstraint(['id_contragent_wash'], ['contragent_washes.id'], ),
                    sa.ForeignKeyConstraint(['id_period'], ['contragents_opl_periods.id'], ),
                    sa.PrimaryKeyConstraint('id_contragent_wash', 'id_period')
                    )

    op.add_column('prefs', sa.Column('dateval', sa.Date(), nullable=True))
    op.add_column('prefs', sa.Column('datetimeval', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('prefs', 'datetimeval')
    op.drop_column('prefs', 'dateval')
    op.drop_table('contragents_opl_reestr')
    op.drop_table('contragents_opl_periods')
