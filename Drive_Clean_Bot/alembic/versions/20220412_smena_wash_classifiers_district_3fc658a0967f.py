"""smena wash classifiers district

Revision ID: 3fc658a0967f
Revises: 9e46439d13a9
Create Date: 2022-04-12 20:08:18.204828

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3fc658a0967f'
down_revision = '9e46439d13a9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('n_auto_class',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )

    op.execute('INSERT INTO n_auto_class VALUES (1, "Эконом")')
    op.execute('INSERT INTO n_auto_class VALUES (2, "Бизнес")')
    op.execute('INSERT INTO n_auto_class VALUES (3, "Премиум")')
    op.execute('INSERT INTO n_auto_class VALUES (4, "Фургон")')

    op.create_table('n_auto_sr_type',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )

    op.execute('INSERT INTO n_auto_sr_type VALUES (1, "Плановая")')
    op.execute('INSERT INTO n_auto_sr_type VALUES (2, "Срочная")')

    op.create_table('n_carsharings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )

    op.execute('INSERT INTO n_carsharings VALUES (1, "ЯндексДрайв")')
    op.execute('INSERT INTO n_carsharings VALUES (2, "СитиДрайв")')

    op.create_table('n_wash_usl_type',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )

    op.execute('INSERT INTO n_wash_usl_type VALUES (1, "Бесконтактная")')
    op.execute('INSERT INTO n_wash_usl_type VALUES (2, "Комплексная")')

    op.create_table('districts',
    sa.Column('id_city', sa.Integer(), nullable=False),
    sa.Column('district', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['id_city'], ['n_city.id'], ),
    sa.PrimaryKeyConstraint('id_city', 'district')
    )

    op.execute('INSERT INTO districts VALUES (1, 1)')
    op.execute('INSERT INTO districts VALUES (1, 2)')
    op.execute('INSERT INTO districts VALUES (1, 3)')
    op.execute('INSERT INTO districts VALUES (1, 4)')
    op.execute('INSERT INTO districts VALUES (1, 5)')
    op.execute('INSERT INTO districts VALUES (1, 6)')
    op.execute('INSERT INTO districts VALUES (1, 7)')
    op.execute('INSERT INTO districts VALUES (2, 1)')
    op.execute('INSERT INTO districts VALUES (3, 1)')

    op.create_table('washes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('id_city', sa.Integer(), nullable=False),
    sa.Column('district', sa.Integer(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['id_city'], ['n_city.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )

    op.create_table('smena',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('id_user', sa.BigInteger(), nullable=False),
    sa.Column('date_smena', sa.Date(), nullable=False),
    sa.Column('datetime_start', sa.DateTime(), nullable=False),
    sa.Column('datetime_end', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['id_user'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    op.create_table('smenaservices',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('id_user', sa.BigInteger(), nullable=False),
    sa.Column('id_smena', sa.BigInteger(), nullable=True),
    sa.Column('daily', sa.Boolean(), nullable=False),
    sa.Column('id_wash', sa.Integer(), nullable=False),
    sa.Column('gosnomer', sa.String(length=20), nullable=False),
    sa.Column('id_carsharing', sa.Integer(), nullable=False),
    sa.Column('id_auto_class', sa.Integer(), nullable=False),
    sa.Column('skoda_rapid', sa.Boolean(), nullable=True),
    sa.Column('id_auto_sr_type', sa.Integer(), nullable=False),
    sa.Column('id_wash_usl_type', sa.Integer(), nullable=False),
    sa.Column('omyv_percent', sa.Integer(), nullable=True),
    sa.Column('date_create', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['id_auto_class'], ['n_auto_class.id'], ),
    sa.ForeignKeyConstraint(['id_auto_sr_type'], ['n_auto_sr_type.id'], ),
    sa.ForeignKeyConstraint(['id_carsharing'], ['n_carsharings.id'], ),
    sa.ForeignKeyConstraint(['id_smena'], ['smena.id'], ),
    sa.ForeignKeyConstraint(['id_user'], ['users.id'], ),
    sa.ForeignKeyConstraint(['id_wash'], ['washes.id'], ),
    sa.ForeignKeyConstraint(['id_wash_usl_type'], ['n_wash_usl_type.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('smenaservices')
    op.drop_table('smena')
    op.drop_table('washes')
    op.drop_table('districts')
    op.drop_table('n_wash_usl_type')
    op.drop_table('n_carsharings')
    op.drop_table('n_auto_sr_type')
    op.drop_table('n_auto_class')
