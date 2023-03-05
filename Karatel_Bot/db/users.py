"""Регистрация юзеров"""
from models.users import ROLES, User

from db.connection import Session


def get_user(id_user: int) -> User:
    """Объект юзера в БД"""
    session = Session()
    user = session.query(User).get(id_user)
    session.close()
    return user


def add_new_user(id_user: int, id_city: int, fam: str, im: str, nick: str) -> bool:
    """Добавление нового юзера"""
    session = Session()

    user = session.query(User).get(id_user)
    if user:
        user.id_city = id_city
        user.id_role = ROLES['pending']
        user.fam = fam
        user.im = im
        user.nick = nick
        user.reg = 0
        user.date_uvol = None
        user.active = 1
    else:
        user = User(
            id=id_user,
            id_city=id_city,
            id_role=ROLES['pending'],
            fam=fam,
            im=im,
            nick=nick,
        )

    session.add(user)
    session.commit()
    session.close()
    return True


def get_admins():
    """Все админы"""
    session = Session()
    values_tuple = session.query(User).filter(User.id_role == ROLES['admin'], User.active == 1).all()
    session.close()
    return values_tuple
