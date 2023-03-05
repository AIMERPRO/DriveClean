"""media smenaservice

Revision ID: 821b80b2859c
Revises: 00ea68ae9d48
Create Date: 2022-06-01 22:35:38.949297

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '821b80b2859c'
down_revision = '00ea68ae9d48'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('media', sa.Column('id_smenaservice', sa.BigInteger(), nullable=True))
    op.add_column('media', sa.Column('sent_to_chat', sa.Boolean(), nullable=True,
                  comment='опционально, если null то отправка в чаты не используется для этого типа медиа'))
    op.create_foreign_key('media_ibfk_9', 'media', 'smenaservices', ['id_smenaservice'], ['id'])

    op.execute('INSERT INTO n_media_types VALUES (14, "Ввод авто - грязные")')
    op.execute('INSERT INTO n_media_types VALUES (15, "Ввод авто - чистые")')


def downgrade():
    op.drop_constraint('media_ibfk_9', 'media', type_='foreignkey')
    op.drop_column('media', 'sent_to_chat')
    op.drop_column('media', 'id_smenaservice')

    op.execute('DELETE FROM n_media_types WHERE id IN (14,15)')
