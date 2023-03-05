"""remove carcheck

Revision ID: 96e8277f7cba
Revises: 2c87387d5e51
Create Date: 2022-12-13 16:06:25.000945

"""
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision = '96e8277f7cba'
down_revision = '2c87387d5e51'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index('name', table_name='n_carcheck_elements')
    op.drop_index('name', table_name='n_carcheck_category')
    op.drop_constraint('media_ibfk_1', 'media', type_='foreignkey')
    op.drop_table('carcheck_problem_elements')
    op.drop_table('carcheck')
    op.drop_column('media', 'id_carcheck')
    op.drop_table('n_carcheck_elements')
    op.drop_table('n_carcheck_category')
    op.execute('DELETE FROM n_media_types WHERE id=1')


def downgrade() -> None:
    op.add_column('media', sa.Column('id_carcheck', mysql.BIGINT(display_width=20), autoincrement=False, nullable=True))
    op.create_foreign_key('media_ibfk_1', 'media', 'carcheck', ['id_carcheck'], ['id'])
    op.create_table('carcheck',
                    sa.Column('id', mysql.BIGINT(display_width=20), autoincrement=True, nullable=False),
                    sa.Column('id_user', mysql.BIGINT(display_width=20), autoincrement=False,
                              nullable=False, comment='ID карателя, который проверил эту машину'),
                    sa.Column('id_driveclean_smenaservice', mysql.BIGINT(
                        display_width=20), autoincrement=False, nullable=False),
                    sa.Column('gosnomer', mysql.VARCHAR(length=20), nullable=False),
                    sa.Column('datetime_create', mysql.DATETIME(), nullable=False),
                    sa.Column('complete', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
                    sa.Column('sent_media_to_channel', mysql.TINYINT(
                        display_width=1), autoincrement=False, nullable=False),
                    sa.ForeignKeyConstraint(['id_user'], ['users.id'], name='carcheck_ibfk_1'),
                    sa.PrimaryKeyConstraint('id'),
                    comment='Проверенные карателем автомобили',
                    mysql_collate='utf8mb4_general_ci',
                    mysql_comment='Проверенные карателем автомобили',
                    mysql_default_charset='utf8mb4',
                    mysql_engine='InnoDB'
                    )
    op.create_table('carcheck_problem_elements',
                    sa.Column('id', mysql.BIGINT(display_width=20), autoincrement=True, nullable=False),
                    sa.Column('id_carcheck', mysql.BIGINT(display_width=20), autoincrement=False, nullable=False),
                    sa.Column('id_element', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
                    sa.Column('datetime_create', mysql.DATETIME(), nullable=False),
                    sa.ForeignKeyConstraint(['id_carcheck'], ['carcheck.id'], name='carcheck_problem_elements_ibfk_1'),
                    sa.ForeignKeyConstraint(['id_element'], ['n_carcheck_elements.id'],
                                            name='carcheck_problem_elements_ibfk_2'),
                    sa.PrimaryKeyConstraint('id'),
                    comment='Проблемные элементы в проверенных автомобилях',
                    mysql_collate='utf8mb4_general_ci',
                    mysql_comment='Проблемные элементы в проверенных автомобилях',
                    mysql_default_charset='utf8mb4',
                    mysql_engine='InnoDB'
                    )
    op.create_table('n_carcheck_category',
                    sa.Column('id', mysql.INTEGER(display_width=11), autoincrement=True, nullable=False),
                    sa.Column('name', mysql.VARCHAR(length=50), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    comment='Категории чистоты',
                    mysql_collate='utf8mb4_general_ci',
                    mysql_comment='Категории чистоты',
                    mysql_default_charset='utf8mb4',
                    mysql_engine='InnoDB'
                    )
    op.create_index('name', 'n_carcheck_category', ['name'], unique=False)
    op.create_table('n_carcheck_elements',
                    sa.Column('id', mysql.INTEGER(display_width=11), autoincrement=True, nullable=False),
                    sa.Column('id_category', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
                    sa.Column('name', mysql.VARCHAR(length=200), nullable=False),
                    sa.Column('active', mysql.TINYINT(display_width=1), autoincrement=False, nullable=False),
                    sa.ForeignKeyConstraint(['id_category'], ['n_carcheck_category.id'],
                                            name='n_carcheck_elements_ibfk_1'),
                    sa.PrimaryKeyConstraint('id'),
                    comment='Элементы авто по категориям',
                    mysql_collate='utf8mb4_general_ci',
                    mysql_comment='Элементы авто по категориям',
                    mysql_default_charset='utf8mb4',
                    mysql_engine='InnoDB'
                    )
    op.create_index('name', 'n_carcheck_elements', ['name'], unique=False)
