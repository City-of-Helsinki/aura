#!/usr/bin/env python

from sqlalchemy import create_engine, ForeignKey, Column, Integer, \
        String, DateTime, Index, Float
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Plow(Base):
    __tablename__ = 'plows'

    id = Column(Integer, primary_key=True, index=True)

class Point(Base):
    __tablename__ = 'points'

    id = Column(Integer, primary_key=True)

    plow_id = Column(Integer, ForeignKey('plows.id'), index=True)
    plow = relationship('Plow', backref=backref('points', order_by=id))
    idx = Column(Integer)

    timestamp = Column(DateTime, index=True)
    lat = Column(Float)
    lon = Column(Float)

    __table_args__ = (Index('ix_points_plow_idx', 'plow_id', 'idx'),)

engine = create_engine('sqlite:///test.db')

Base.metadata.create_all(engine)

session = sessionmaker(bind=engine)()

from models import Plow as MongoPlow

import settings
import mongoengine

mongoengine.connect(settings.MONGO_DB)

count = MongoPlow.objects.count()
print("%d plows" % count)

for plow_idx, mp in enumerate(MongoPlow.objects.all()):
    plow = session.query(Plow).filter_by(id=mp.id).first()
    if not plow:
        plow = Plow(id=mp.id)
        session.add(plow)
    points = plow.points
    p_count = len(points)
    if p_count > 0 and p_count != len(mp.points):
        print("Plow %d, points mismatch: %d vs. %d" % (plow.id, p_count, len(mp_points)))
        del plow.points

    if p_count != len(mp.points):
        for idx, mpoint in enumerate(mp.points):
            pnt = Point(plow=plow, idx=idx, timestamp=mpoint.timestamp)
            pnt.lon = mpoint.coords[0]
            pnt.lat = mpoint.coords[1]
            session.add(pnt)
    session.commit()
    if plow_idx % 10 == 0:
        print(plow_idx)
