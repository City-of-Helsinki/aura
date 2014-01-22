#!/usr/bin/env python

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlmodels import *

import settings

engine = create_engine(settings.DATABASE_URL)
Base.metadata.create_all(engine)
session = sessionmaker(bind=engine)()

from models import Plow as MongoPlow
import mongoengine

mongoengine.connect(settings.MONGO_DB)

count = MongoPlow.objects.count()
print("%d plows" % count)

def migrate_plow(mp, event_types):
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
        last_timestamp = None
        for idx, mpoint in enumerate(mp.points):
            pnt = Point(plow=plow, index=idx, timestamp=mpoint.timestamp)
            pnt.lon = mpoint.coords[0]
            pnt.lat = mpoint.coords[1]
            last_timestamp = mpoint.timestamp
            session.add(pnt)
            for ev_type in mpoint.events:
                if ev_type not in event_types:
                    print("Adding new event type %s" % ev_type)
                    ev = EventType(id=ev_type)
                    session.add(ev)
                    event_types[ev_type] = ev
                else:
                    ev = event_types[ev_type]
                pnt.events.append(ev)

        plow.last_timestamp = last_timestamp
    session.commit()

event_types = {}
for ev in session.query(EventType):
    event_types[ev.id] = ev

PER_PAGE = 20
mongo_count = MongoPlow.objects.count()
plow_idx = 0
while plow_idx < mongo_count:
    plow_list = MongoPlow.objects.limit(PER_PAGE).skip(plow_idx)
    for plow in plow_list:
        migrate_plow(plow, event_types)
    plow_idx += plow_list.count()
    print(plow_idx)
