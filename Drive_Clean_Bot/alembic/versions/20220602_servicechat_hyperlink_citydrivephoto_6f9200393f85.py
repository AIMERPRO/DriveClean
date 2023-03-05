"""servicechat hyperlink citydrivephoto

Revision ID: 6f9200393f85
Revises: d48c1109e609
Create Date: 2022-06-02 20:01:44.373724

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6f9200393f85'
down_revision = 'd48c1109e609'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('service_chats', sa.Column('hyperlink', sa.String(
        length=255), nullable=True, comment='ссылка на чат'))
    op.create_table_comment(
        'service_chats',
        'ID сервисных групп и каналов',
        existing_comment='ID сервисных чатов и каналов',
        schema=None
    )
    op.execute('INSERT INTO service_chats (name) VALUES ("citydrive_photo")')


def downgrade():
    op.create_table_comment(
        'service_chats',
        'ID сервисных чатов и каналов',
        existing_comment='ID сервисных групп и каналов',
        schema=None
    )
    op.drop_column('service_chats', 'hyperlink')
    op.execute('DELETE FROM service_chats WHERE name = "citydrive_photo"')
