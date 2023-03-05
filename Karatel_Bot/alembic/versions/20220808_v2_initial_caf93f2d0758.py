"""v2 initial

Revision ID: caf93f2d0758
Revises: 
Create Date: 2022-08-08 21:08:43.144846

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'caf93f2d0758'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('n_city',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=100), nullable=False),
                    sa.Column('icon', sa.String(length=1), nullable=True,
                              comment='Иконка (эмодзи) для обозначения города в текстовых отчётах'),
                    sa.Column('active', sa.Boolean(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('name'),
                    comment='Города'
                    )

    op.execute('INSERT INTO n_city VALUES (1, "Москва", "🌃", 1)')
    op.execute('INSERT INTO n_city VALUES (2, "Питер", "🌉", 1)')
    op.execute('INSERT INTO n_city VALUES (3, "Казань", "🏔", 0)')

    op.create_table('n_role',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=50), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('name'),
                    comment='Роли юзеров'
                    )

    op.execute('INSERT INTO n_role VALUES (5, "Ожидание регистрации")')
    op.execute('INSERT INTO n_role VALUES (10, "Администратор")')
    op.execute('INSERT INTO n_role VALUES (40, "Каратель")')

    op.create_table('prefs',
                    sa.Column('name', sa.String(length=50), nullable=False),
                    sa.Column('intval', sa.BigInteger(), nullable=True),
                    sa.Column('textval', sa.Text(), nullable=True),
                    sa.Column('dateval', sa.Date(), nullable=True),
                    sa.Column('datetimeval', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('name'),
                    comment='Константы и постоянные переменные'
                    )

    op.create_table('states',
                    sa.Column('id_user', sa.BigInteger(), nullable=False),
                    sa.Column('state', sa.String(length=255), nullable=False, comment='Номер стадии'),
                    sa.PrimaryKeyConstraint('id_user'),
                    comment='Стадии меню у юзеров'
                    )

    op.create_table('tempvals',
                    sa.Column('id_user', sa.BigInteger(), nullable=False),
                    sa.Column('state', sa.String(length=100), nullable=False,
                              comment='К какому шагу меню относится данная переменная'),
                    sa.Column('intval', sa.BigInteger(), nullable=True),
                    sa.Column('textval', sa.Text(), nullable=True),
                    sa.Column('protect', sa.Boolean(), nullable=False,
                              comment='Не будет удалено методом clear_user_tempvals()'),
                    sa.Column('date_create', sa.DateTime(), nullable=False),
                    sa.PrimaryKeyConstraint('id_user', 'state'),
                    comment='Временные переменные'
                    )

    op.create_table('service_chats',
                    sa.Column('name', sa.String(length=50), nullable=False),
                    sa.Column('id_city', sa.Integer(), nullable=True,
                              comment='необязательно, для разбивки чатов по городам'),
                    sa.Column('chat_id', sa.String(length=255), nullable=True, comment='id чата в TG'),
                    sa.Column('hyperlink', sa.String(length=255), nullable=True, comment='ссылка на чат'),
                    sa.ForeignKeyConstraint(['id_city'], ['n_city.id'], ),
                    sa.PrimaryKeyConstraint('name'),
                    comment='ID сервисных групп и каналов'
                    )

    op.create_table('users',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('fam', sa.String(length=100), nullable=False),
                    sa.Column('im', sa.String(length=100), nullable=False),
                    sa.Column('nick', sa.String(length=100), nullable=True),
                    sa.Column('id_role', sa.Integer(), nullable=False),
                    sa.Column('id_city', sa.Integer(), nullable=False),
                    sa.Column('date_reg', sa.DateTime(), nullable=False),
                    sa.Column('date_uvol', sa.DateTime(), nullable=True),
                    sa.Column('reg', sa.Boolean(), nullable=False),
                    sa.Column('active', sa.Boolean(), nullable=False),
                    sa.ForeignKeyConstraint(['id_city'], ['n_city.id'], ),
                    sa.ForeignKeyConstraint(['id_role'], ['n_role.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    comment='Юзеры; reg=0 and active=1: прошёл регистрацию, но ещё не подтверждён; reg=1 and active=0: уволен (или отменена админом регистрация), может пройти регистрацию заново; '
                    )


def downgrade() -> None:
    op.drop_table('users')
    op.drop_table('service_chats')
    op.drop_table('tempvals')
    op.drop_table('states')
    op.drop_table('prefs')
    op.drop_table('n_role')
    op.drop_table('n_city')
