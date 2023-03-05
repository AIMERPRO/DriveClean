"""rpn only reqs

Revision ID: a12cc1c66484
Revises: 6f9200393f85
Create Date: 2022-06-03 20:13:44.264200

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'a12cc1c66484'
down_revision = '6f9200393f85'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('media_ibfk_5', 'media', type_='foreignkey')
    op.drop_column('media', 'id_rpn')
    op.drop_constraint('reqs_rpn_ibfk_2', 'reqs_rpn', type_='foreignkey')
    op.drop_column('reqs_rpn', 'id_rpn')
    op.drop_table('rpn')

    op.execute('DELETE FROM media WHERE id_req_rpn IS NOT NULL')
    # добавляем id мойки и привязку к нему. Данные за 2 дня без этого id всё равно бесполезны
    op.execute('DELETE FROM reqs_rpn')

    op.add_column('reqs_rpn', sa.Column('id_wash', sa.Integer(), nullable=False))
    op.create_foreign_key('reqs_rpn_ibfk_5', 'reqs_rpn', 'washes', ['id_wash'], ['id'])


def downgrade():
    op.drop_constraint('reqs_rpn_ibfk_5', 'reqs_rpn', type_='foreignkey')
    op.drop_column('reqs_rpn', 'id_wash')

    op.create_table('rpn',
                    sa.Column('id', mysql.BIGINT(display_width=20), autoincrement=True, nullable=False),
                    sa.Column('id_smena_date', mysql.BIGINT(display_width=20), autoincrement=False, nullable=False),
                    sa.Column('id_wash', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
                    sa.Column('file_id_temperature_list', mysql.VARCHAR(length=255), nullable=True),
                    sa.Column('id_user', mysql.BIGINT(display_width=20), autoincrement=False, nullable=False),
                    sa.Column('date_create', mysql.DATETIME(), nullable=False),
                    sa.ForeignKeyConstraint(['id_smena_date'], ['smena_dates.id'], name='rpn_ibfk_1'),
                    sa.ForeignKeyConstraint(['id_user'], ['users.id'], name='rpn_ibfk_2'),
                    sa.ForeignKeyConstraint(['id_wash'], ['washes.id'], name='rpn_ibfk_3'),
                    sa.PrimaryKeyConstraint('id'),
                    mysql_default_charset='utf8mb4',
                    mysql_engine='InnoDB'
                    )
    op.add_column('media', sa.Column('id_rpn', mysql.BIGINT(display_width=20), autoincrement=False, nullable=True))
    op.create_foreign_key('media_ibfk_5', 'media', 'rpn', ['id_rpn'], ['id'])
    op.add_column('reqs_rpn', sa.Column('id_rpn', mysql.BIGINT(display_width=20), autoincrement=False, nullable=False))
    op.create_foreign_key('reqs_rpn_ibfk_2', 'reqs_rpn', 'rpn', ['id_rpn'], ['id'])
