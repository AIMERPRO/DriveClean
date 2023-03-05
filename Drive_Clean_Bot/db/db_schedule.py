"""Графики работы"""
import datetime

from sqlalchemy import desc

from db.connection import Session
from models.model_users import ROLES, User
from models.model_workprocess import Schedule


def get_user_schedule(id_user: int) -> Schedule:
    session = Session()
    value = session.query(Schedule).filter(Schedule.id_user == id_user, Schedule.active == 1).first()
    session.close()
    return value


def create_user_schedule(id_user: int, week_template: str) -> int:
    session = Session()
    session.query(Schedule).filter(Schedule.id_user == id_user,
                                   Schedule.approoved == 0).delete(synchronize_session='fetch')
    new_sched = Schedule(
        id_user=id_user,
        week_template=week_template
    )
    session.add(new_sched)
    session.commit()
    new_sched_id = new_sched.id
    session.close()
    return new_sched_id


def get_unapprooved_scheds(id_city):
    session = Session()
    values_tuple = session.query(Schedule).join(User, User.id == Schedule.id_user).filter(
        User.id_city == id_city, Schedule.approoved == 0, User.id_role.notin_((ROLES['support'], ROLES['support_daily'],
                                                                               ROLES['support_penaltier']))).limit(18).all()  # TODO magic number
    session.close()
    return values_tuple


def get_support_scheds():
    session = Session()
    val_tuple = session.query(Schedule).join(User, User.id == Schedule.id_user).filter(
        Schedule.approoved == 0, User.id_role.in_((ROLES['support'], ROLES['support_daily'],
                                                  ROLES['support_penaltier']))).limit(10).all()
    session.close()
    return val_tuple


def confirm_user_schedule(id_sched: int) -> bool:
    session = Session()
    today_date = datetime.date.today()
    yesterday_date = today_date - datetime.timedelta(days=1)
    sched_item = session.query(Schedule).get(id_sched)
    if sched_item:
        # если в течение дня уже менял график, ему его подтвердили, и тут он снова его меняет и снова его подтверждают - то предыдущий сегодняшний график удаляем
        session.query(Schedule).filter(Schedule.id_user == sched_item.id_user, Schedule.date_start ==
                                       today_date, Schedule.approoved == 1).delete(synchronize_session='fetch')

        prev_sched = session.query(Schedule).filter(Schedule.id_user == sched_item.id_user, Schedule.approoved ==
                                                    1, Schedule.active == 1).order_by(desc(Schedule.id)).first()
        if prev_sched:
            prev_sched.date_end = yesterday_date
            prev_sched.active = 0
            session.add(prev_sched)

        sched_item.approoved = 1
        sched_item.active = 1
        session.add(sched_item)

        session.commit()
    session.close()
    return True


def reject_user_schedule(id_sched: int) -> bool:
    session = Session()
    sched_item = session.query(Schedule).get(id_sched)
    if sched_item:
        session.delete(sched_item)
        session.commit()
    session.close()
