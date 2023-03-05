"""washcheck

Revision ID: a0209e9238a4
Revises: fdd7b45ddb10
Create Date: 2022-08-16 13:54:48.714805

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a0209e9238a4'
down_revision = 'fdd7b45ddb10'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('n_washcheck_elements',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=200), nullable=False),
                    sa.Column('active', sa.Boolean(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('name'),
                    comment='Элементы чеклиста, по которым выполняются услуги на мойке'
                    )

    op.execute('INSERT INTO n_washcheck_elements VALUES (1, "Кузов", 1)')
    op.execute('INSERT INTO n_washcheck_elements VALUES (2, "Пылесос", 1)')
    op.execute('INSERT INTO n_washcheck_elements VALUES (3, "Стекла", 1)')
    op.execute('INSERT INTO n_washcheck_elements VALUES (4, "Пороги", 1)')
    op.execute('INSERT INTO n_washcheck_elements VALUES (5, "Багажник", 1)')
    op.execute('INSERT INTO n_washcheck_elements VALUES (6, "Пластик - приборная панель", 1)')
    op.execute('INSERT INTO n_washcheck_elements VALUES (7, "Пластик - мультимедиа", 1)')
    op.execute('INSERT INTO n_washcheck_elements VALUES (8, "Пластик - ручка КПП, кожух и пластик вокруг", 1)')
    op.execute('INSERT INTO n_washcheck_elements VALUES (9, "Пластик - дверные карты", 1)')
    op.execute('INSERT INTO n_washcheck_elements VALUES (10, "Пластик - мелочница", 1)')
    op.execute('INSERT INTO n_washcheck_elements VALUES (11, "Пластик - подстаканник", 1)')

    op.create_table('washcheck',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('id_user', sa.BigInteger(), nullable=False,
                              comment='ID карателя, который проверил эту мойку'),
                    sa.Column('id_wash', sa.Integer(), nullable=False),
                    sa.Column('gosnomer', sa.String(length=20), nullable=False),
                    sa.Column('complete', sa.Boolean(), nullable=False),
                    sa.Column('datetime_create', sa.DateTime(), nullable=False),
                    sa.ForeignKeyConstraint(['id_user'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    comment='Проверенные карателем мойки'
                    )

    op.create_table('washcheck_checklist',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('id_washcheck', sa.BigInteger(), nullable=False),
                    sa.Column('id_element', sa.Integer(), nullable=False),
                    sa.Column('result', sa.Boolean(), nullable=False),
                    sa.Column('datetime_create', sa.DateTime(), nullable=False),
                    sa.ForeignKeyConstraint(['id_element'], ['n_washcheck_elements.id'], ),
                    sa.ForeignKeyConstraint(['id_washcheck'], ['washcheck.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    comment='Чеклист по услугам на проверяемых мойках'
                    )


def downgrade() -> None:
    op.drop_table('washcheck_checklist')
    op.drop_table('washcheck')
    op.drop_table('n_washcheck_elements')
