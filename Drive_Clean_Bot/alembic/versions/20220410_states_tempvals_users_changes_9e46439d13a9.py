"""states tempvals users changes

Revision ID: 9e46439d13a9
Revises: 856406fcaae4
Create Date: 2022-04-10 14:28:32.840754

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9e46439d13a9'
down_revision = '856406fcaae4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('states',
    sa.Column('id_user', sa.BigInteger(), nullable=False),
    sa.Column('state', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id_user')
    )
    op.drop_constraint('tempvals_ibfk_1', 'tempvals', type_='foreignkey')
    op.add_column('users', sa.Column('reg', sa.Boolean(), nullable=False))
    op.execute('INSERT INTO n_role VALUES (5, "Ожидание регистрации")')


def downgrade():
    op.drop_column('users', 'reg')
    op.create_foreign_key('tempvals_ibfk_1', 'tempvals', 'users', ['id_user'], ['id'])
    op.drop_table('states')
    op.execute('DELETE FROM n_role WHERE id = 5')
