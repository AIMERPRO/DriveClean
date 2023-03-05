"""initial

Revision ID: 856406fcaae4
Revises: 
Create Date: 2022-04-10 09:56:54.567929

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '856406fcaae4'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('n_city',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )

    op.execute('INSERT INTO n_city VALUES (1, "Москва")')
    op.execute('INSERT INTO n_city VALUES (2, "Питер")')
    op.execute('INSERT INTO n_city VALUES (3, "Казань")')

    op.create_table('n_role',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )

    op.execute('INSERT INTO n_role VALUES (10, "Администратор")')
    op.execute('INSERT INTO n_role VALUES (11, "Руководитель")')
    op.execute('INSERT INTO n_role VALUES (12, "Техподдержка")')
    op.execute('INSERT INTO n_role VALUES (20, "Бригадир")')
    op.execute('INSERT INTO n_role VALUES (21, "Проверяющий")')
    op.execute('INSERT INTO n_role VALUES (30, "Перегонщик")')

    op.create_table('prefs',
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('intval', sa.BigInteger(), nullable=True),
    sa.Column('textval', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('name')
    )

    op.create_table('users',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('fam', sa.String(length=100), nullable=False),
    sa.Column('im', sa.String(length=100), nullable=False),
    sa.Column('ot', sa.String(length=100), nullable=True),
    sa.Column('nick', sa.String(length=100), nullable=True),
    sa.Column('datar', sa.Date(), nullable=False),
    sa.Column('phone', sa.String(length=20), nullable=False),
    sa.Column('id_role', sa.Integer(), nullable=False),
    sa.Column('id_city', sa.Integer(), nullable=False),
    sa.Column('district', sa.Integer(), nullable=True),
    sa.Column('date_reg', sa.DateTime(), nullable=False),
    sa.Column('date_uvol', sa.DateTime(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['id_city'], ['n_city.id'], ),
    sa.ForeignKeyConstraint(['id_role'], ['n_role.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    op.create_table('tempvals',
    sa.Column('id_user', sa.BigInteger(), nullable=False),
    sa.Column('state', sa.String(length=100), nullable=False),
    sa.Column('intval', sa.BigInteger(), nullable=True),
    sa.Column('textval', sa.Text(), nullable=True),
    sa.Column('protect', sa.Boolean(), nullable=False),
    sa.Column('date_create', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['id_user'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id_user', 'state')
    )


def downgrade():
    op.drop_table('tempvals')
    op.drop_table('users')
    op.drop_table('prefs')
    op.drop_table('n_role')
    op.drop_table('n_city')
