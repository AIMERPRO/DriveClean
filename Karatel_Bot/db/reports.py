"""Отчёты текстовые"""
from models.service import ServiceChat

from db.connection import Session


def get_service_chat(name: str) -> ServiceChat:
    session = Session()
    value = session.query(ServiceChat).get(name)
    session.close()
    return value
