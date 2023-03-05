"""carcheck elements

Revision ID: ac2f973b2fc6
Revises: caf93f2d0758
Create Date: 2022-08-13 22:41:17.694751

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'ac2f973b2fc6'
down_revision = 'caf93f2d0758'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('n_carcheck_category',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=50), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('name'),
                    comment='Категории чистоты'
                    )

    op.execute('INSERT INTO n_carcheck_category VALUES (1, "Категория 1")')
    op.execute('INSERT INTO n_carcheck_category VALUES (2, "Категория 2")')
    op.execute('INSERT INTO n_carcheck_category VALUES (3, "Категория 3")')

    op.create_table('n_carcheck_elements',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('id_category', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=200), nullable=False),
                    sa.Column('active', sa.Boolean(), nullable=False),
                    sa.ForeignKeyConstraint(['id_category'], ['n_carcheck_category.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('name'),
                    comment='Элементы авто по категориям'
                    )

    op.execute('INSERT INTO n_carcheck_elements VALUES (1, 1, "Верхняя часть торпедо", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (2, 1, "Нижняя часть торпедо", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (3, 1, "Приборная панель", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (4, 1, "Ручка КПП, кожух и пластик вокруг", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (5, 1, "Подстаканники", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (6, 1, "Мелочница", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (7, 1, "Пластик центральной консоли", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (8, 1, "Боковой пластик водителя", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (9, 1, "Текстиль водительского сидения", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (10, 1, "Пластик дверной карты водителя", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (11, 1, "Пластик ножн. арки водителя", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (12, 1, "Пластик и кнопки вокруг мультимедиа", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (13, 1, "Мультимедиа", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (14, 1, "Карман дверной карты водителя", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (15, 1, "Управл. элем. дверн. карты водит.", 1)')

    op.execute('INSERT INTO n_carcheck_elements VALUES (16, 2, "Руль, рычаги управления", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (17, 2, "Пластик пассажирского сидения", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (18, 2, "Пластик ножной арки пассажира", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (19, 2, "Карман дверной карты пассажира", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (20, 2, "Управл. элем. дверн. карты пассаж.", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (21, 2, "Пластик дверной карты пассажира", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (22, 2, "Зеркало заднего вида", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (23, 2, "Бардачок", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (24, 2, "Боковой пласт. заднего правого пассажира", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (25, 2, "Боковой пласт. заднего левого пассажира", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (26, 2, "Боковой пластик со стороны пассажира", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (27, 2, "Пластик дверной карты за водителем", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (28, 2, "Пластик дверной карты за пассажиром", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (29, 2, "Задняя часть пластика подстаканника", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (30, 2, "Задняя левая часть сиденья", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (31, 2, "Задняя правая часть сиденья", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (32, 2, "Пластиковая обивка багажника", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (33, 2, "Приятный запах в салоне", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (34, 2, "Наличие воды-незамерзайки", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (35, 2, "Полка между спид. и рулем сверху и снизу", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (36, 2, "Пластик водительского сидения", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (37, 2, "Текстиль пассажирского сидения", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (38, 2, "Пристёгнутый ремень", 1)')

    op.execute('INSERT INTO n_carcheck_elements VALUES (39, 3, "Лобовое стекло с внешней стороны", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (40, 3, "Заднее стекло с внешней стороны", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (41, 3, "Водит. стекло с внешн. стороны", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (42, 3, "Пассажирск. переднее стекло с внешней стороны", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (43, 3, "Капот", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (44, 3, "Левая передняя часть кузова", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (45, 3, "Левая задняя часть кузова", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (46, 3, "Правая передняя часть кузова", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (47, 3, "Правая задняя часть кузова", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (48, 3, "Задний бампер", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (49, 3, "Крышка багажника", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (50, 3, "Стекло заднего правого пассажира", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (51, 3, "Стекло заднего левого пассажира", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (52, 3, "Пятна на водительском сидении", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (53, 3, "Пятна на пассажирском сидении", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (54, 3, "Пятна на правой части заднего дивана", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (55, 3, "Пятна на левой части заднего дивана", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (56, 3, "Стекла заднего вида", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (57, 3, "Металлические элементы багажника", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (58, 3, "Метталич. элем. водительской двери ", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (59, 3, "Метталич. элем. пассажирской двери ", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (60, 3, "Сушка", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (61, 3, "Метталич. элем. двери за водителем ", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (62, 3, "Метталич. элем. двери за пассажиром ", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (63, 3, "Порог со стороны водителя", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (64, 3, "Порог заднего правого пассажира", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (65, 3, "Порог заднего левого пассажира", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (66, 3, "Порог со стороны пассажира", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (67, 3, "Коврик водительский", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (68, 3, "Коврик за водителем", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (69, 3, "Коврик за пассажиром", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (70, 3, "Пространство под ковриком за водителем", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (71, 3, "Пространство под ковриком за пассажиром", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (72, 3, "Пространство под ковриком пассажира", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (73, 3, "Тканевая обивка багажника", 1)')
    op.execute('INSERT INTO n_carcheck_elements VALUES (74, 3, "Педали", 1)')

    op.create_table('carcheck',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('id_user', sa.BigInteger(), nullable=False,
                              comment='ID карателя, который проверил эту машину'),
                    sa.Column('id_driveclean_smenaservice', sa.BigInteger(), nullable=False),
                    sa.Column('gosnomer', sa.String(length=20), nullable=False),
                    sa.Column('datetime_create', sa.DateTime(), nullable=False),
                    sa.ForeignKeyConstraint(['id_user'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    comment='Проверенные карателем автомобили'
                    )

    op.create_table('carcheck_problem_elements',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('id_carcheck', sa.BigInteger(), nullable=False),
                    sa.Column('id_element', sa.Integer(), nullable=False),
                    sa.Column('datetime_create', sa.DateTime(), nullable=False),
                    sa.ForeignKeyConstraint(['id_carcheck'], ['carcheck.id'], ),
                    sa.ForeignKeyConstraint(['id_element'], ['n_carcheck_elements.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    comment='Проблемные элементы в проверенных автомобилях'
                    )


def downgrade() -> None:
    op.drop_table('carcheck_problem_elements')
    op.drop_table('carcheck')
    op.drop_table('n_carcheck_elements')
    op.drop_table('n_carcheck_category')
