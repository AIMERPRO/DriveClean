"""media

Revision ID: fdd7b45ddb10
Revises: ac2f973b2fc6
Create Date: 2022-08-14 16:35:20.739355

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'fdd7b45ddb10'
down_revision = 'ac2f973b2fc6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('n_media_formats',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=20), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('name'),
                    comment='Форматы медиа (фото, видео)'
                    )

    op.execute('INSERT INTO n_media_formats VALUES (1, "Фото")')
    op.execute('INSERT INTO n_media_formats VALUES (2, "Видео")')

    op.create_table('n_media_types',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=50), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('name'),
                    comment='Типы медиа (к какой ситуации относятся)'
                    )

    op.execute('INSERT INTO n_media_types VALUES (1, "Проверка чистоты авто")')

    op.create_table('media',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('id_user', sa.BigInteger(), nullable=False),
                    sa.Column('id_carcheck', sa.BigInteger(), nullable=True),
                    sa.Column('id_media_format', sa.Integer(), nullable=False),
                    sa.Column('id_media_type', sa.Integer(), nullable=False),
                    sa.Column('file_id', sa.String(length=255), nullable=False),
                    sa.Column('date_create', sa.DateTime(), nullable=False),
                    sa.ForeignKeyConstraint(['id_carcheck'], ['carcheck.id'], ),
                    sa.ForeignKeyConstraint(['id_media_format'], ['n_media_formats.id'], ),
                    sa.ForeignKeyConstraint(['id_media_type'], ['n_media_types.id'], ),
                    sa.ForeignKeyConstraint(['id_user'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    comment='Медиа'
                    )

    op.add_column('carcheck', sa.Column('complete', sa.Boolean(), nullable=False))
    op.add_column('carcheck', sa.Column('sent_media_to_channel', sa.Boolean(), nullable=False))

    op.execute('INSERT INTO service_chats (name) VALUES ("channel_karatelphoto")')


def downgrade() -> None:
    op.drop_column('carcheck', 'sent_media_to_channel')
    op.drop_column('carcheck', 'complete')
    op.drop_table('media')
    op.drop_table('n_media_types')
    op.drop_table('n_media_formats')

    op.execute('DELETE FROM service_chats WHERE name="channel_karatelphoto"')
