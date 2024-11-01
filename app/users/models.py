import datetime

from sqlalchemy import Column, String, BigInteger, Text, TIMESTAMP, ForeignKey, Boolean, Integer
from sqlalchemy.orm import relationship

from app.base import Base


class User(Base):
    __tablename__ = 'users'
    tg_id = Column(Integer, primary_key=True)
    name = Column(String(255))
    role = Column(String(255))
    phone = Column(String(255))
    notes = relationship('Note', back_populates='user')

