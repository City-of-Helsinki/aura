from sqlalchemy import ForeignKey, Column, Integer, \
        String, DateTime, Index, Float, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

Base = declarative_base()

class Plow(Base):
    __tablename__ = 'plows'

    id = Column(Integer, primary_key=True, index=True)
    last_timestamp = Column(DateTime, index=True, nullable=True)

class EventType(Base):
    __tablename__ = 'event_types'

    id = Column(String, primary_key=True, index=True)
    name_fi = Column(String, nullable=True)
    name_en = Column(String, nullable=True)

point_event_type = Table('point_event', Base.metadata,
    Column('point_id', Integer, ForeignKey('points.id'), index=True),
    Column('event_type_id', String, ForeignKey('event_types.id'))
)

class Point(Base):
    __tablename__ = 'points'

    id = Column(Integer, primary_key=True)

    plow_id = Column(Integer, ForeignKey('plows.id'), index=True)
    plow = relationship('Plow', backref=backref('points'))
    index = Column(Integer)

    timestamp = Column(DateTime, index=True)
    lat = Column(Float)
    lon = Column(Float)
    events = relationship('EventType', secondary=point_event_type, backref='points')

    __table_args__ = (Index('ix_points_plow_index', 'plow_id', 'index'),)
