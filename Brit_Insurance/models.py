from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Numeric

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Item(Base):
    __tablename__ = "item"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    value = Column(Numeric, default=0.0)
    token = Column(String)


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    # Need to encrypt this column for data at REST or use OAuth2
    password = Column(String)


class UserSession(Base):
    __tablename__ = "user_session"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    state = Column(Boolean, default=True)
    token = Column(String)
