"""contragents

Revision ID: df3ef2396559
Revises: a12cc1c66484
Create Date: 2022-06-09 15:10:08.696701

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'df3ef2396559'
down_revision = 'a12cc1c66484'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('contragents',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('ctr_name', sa.String(length=255), nullable=False, comment='Наименование контрагента'),
                    sa.Column('ndog', sa.String(length=100), nullable=False, comment='Номер договора'),
                    sa.Column('id_city', sa.Integer(), nullable=False),
                    sa.Column('docs_hyperlink', sa.String(length=100), nullable=False, comment='Ссылка на документы'),
                    sa.Column('phone', sa.String(length=20), nullable=False),
                    sa.Column('fio', sa.String(length=255), nullable=False, comment='ЛПР'),
                    sa.Column('email', sa.String(length=100), nullable=False),
                    sa.Column('date_create', sa.DateTime(), nullable=False),
                    sa.Column('active', sa.Boolean(), nullable=False),
                    sa.ForeignKeyConstraint(['id_city'], ['n_city.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )

    op.create_table('contragent_washes',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('id_contragent', sa.BigInteger(), nullable=False),
                    sa.Column('address', sa.String(length=255), nullable=False),
                    sa.Column('cost_bm_kop', sa.Integer(), nullable=True, comment='Здесь и далее цены в копейках'),
                    sa.Column('cost_furgon_kop', sa.Integer(), nullable=True),
                    sa.Column('cost_shuttle_kop', sa.Integer(), nullable=True),
                    sa.Column('cost_pb_kop', sa.Integer(), nullable=True),
                    sa.Column('cost_ps_kop', sa.Integer(), nullable=True),
                    sa.Column('cost_chem_kop', sa.Integer(), nullable=True),
                    sa.Column('cost_zhir_kop', sa.Integer(), nullable=True),
                    sa.Column('cost_glue_kop', sa.Integer(), nullable=True),
                    sa.Column('cost_polir_kop', sa.Integer(), nullable=True),
                    sa.Column('cost_chempot_kop', sa.Integer(), nullable=True),
                    sa.Column('cost_chern_kop', sa.Integer(), nullable=True),
                    sa.Column('cost_fazwash_kop', sa.Integer(), nullable=True),
                    sa.Column('cost_podpisk_kop', sa.Integer(), nullable=True),
                    sa.Column('cost_benzov_kop', sa.Integer(), nullable=True),
                    sa.Column('cost_nzmrz_kop', sa.Integer(), nullable=True),
                    sa.Column('date_create', sa.DateTime(), nullable=False),
                    sa.Column('active', sa.Boolean(), nullable=False),
                    sa.ForeignKeyConstraint(['id_contragent'], ['contragents.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )


def downgrade():
    op.drop_table('contragent_washes')
    op.drop_table('contragents')
