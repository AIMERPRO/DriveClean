"""outcheck

Revision ID: a59937a80768
Revises: a0209e9238a4
Create Date: 2022-08-16 16:03:20.296950

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a59937a80768'
down_revision = 'a0209e9238a4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('outcheck',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('id_user', sa.BigInteger(), nullable=False, comment='ID карателя'),
                    sa.Column('gosnomer', sa.String(length=20), nullable=False),
                    sa.Column('complete', sa.Boolean(), nullable=False),
                    sa.Column('datetime_create', sa.DateTime(), nullable=False),
                    sa.ForeignKeyConstraint(['id_user'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    comment='Выездные проверки'
                    )

    op.create_table('outcheck_checklist',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('id_outcheck', sa.BigInteger(), nullable=False),
                    sa.Column('id_element', sa.Integer(), nullable=False),
                    sa.Column('result', sa.Boolean(), nullable=False),
                    sa.Column('datetime_create', sa.DateTime(), nullable=False),
                    sa.ForeignKeyConstraint(['id_element'], ['n_washcheck_elements.id'], ),
                    sa.ForeignKeyConstraint(['id_outcheck'], ['outcheck.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    comment='Чеклист по выездным проверкам'
                    )

    op.add_column('media', sa.Column('id_outcheck', sa.BigInteger(), nullable=True))
    op.add_column('media', sa.Column('id_washcheck_element', sa.Integer(), nullable=True))
    op.create_foreign_key('media_ibfk_5', 'media', 'outcheck', ['id_outcheck'], ['id'])
    op.create_foreign_key('media_ibfk_6', 'media', 'n_washcheck_elements', ['id_washcheck_element'], ['id'])

    op.execute('INSERT INTO n_media_types VALUES (2, "Элементы по выездной проверке")')


def downgrade() -> None:
    op.drop_constraint('media_ibfk_5', 'media', type_='foreignkey')
    op.drop_constraint('media_ibfk_6', 'media', type_='foreignkey')
    op.drop_column('media', 'id_washcheck_element')
    op.drop_column('media', 'id_outcheck')
    op.drop_table('outcheck_checklist')
    op.drop_table('outcheck')
    op.execute('DELETE FROM n_media_types WHERE id=2')
