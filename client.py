import time
import datetime
import requests
import logging

#import requests_cache
#requests_cache.configure('cache')

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

from sqlmodels import *
import settings

engine = create_engine(settings.DATABASE_URL)
session = sessionmaker(bind=engine)()

event_types = {}
for ev in session.query(EventType):
    event_types[ev.id] = ev

def refresh_plow(info):
    plow_id = int(info['id'])
    plow = session.query(Plow).filter_by(id=plow_id).first()
    if not plow:
        plow = Plow(id=plow_id)
        session.add(plow)

    last_point = session.query(Point).filter_by(plow=plow).order_by(desc('"index"')).first()
    if last_point:
        point_idx = last_point.index + 1
    else:
        point_idx = 0

    new_points = 0
    last_timestamp = plow.last_timestamp
    for point in info['points']:
        ts = point['timestamp']
        # Parse ISO 8601 timestamp
        ts = datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")
        if not last_point or ts > last_point.timestamp:
            pnt = Point(plow=plow, index=point_idx, timestamp=ts)
            pnt.lat = point['y']
            pnt.lon = point['x']
            session.add(pnt)

            for ev_type in point['events'].split(','):
                if ev_type not in event_types:
                    print("Adding new event type %s" % ev_type)
                    ev = EventType(id=ev_type)
                    session.add(ev)
                    event_types[ev_type] = ev
                else:
                    ev = event_types[ev_type]
                pnt.events.append(ev)

            point_idx += 1
            new_points += 1
            last_timestamp = pnt.timestamp
            last_point = pnt

    if plow.last_timestamp != last_timestamp:
        session.query(Plow).filter_by(id=plow.id).update({'last_timestamp': last_timestamp})

    session.commit()
    print "plow %d: %d new points (last ts %s)" % (info['id'], new_points, last_timestamp)


def refresh_plows():
    print "connecting"
    r = requests.get(settings.URL, auth=settings.AUTH, verify=False)
    if r.status_code != 200:
        raise Exception("HTTP request failed with HTTP%d" % r.status_code)
    plow_list = r.json()
    print "got info for %d plows" % len(plow_list)
    for info in plow_list:
        refresh_plow(info)

if __name__ == '__main__':
    logging.basicConfig()
    logger = logging.getLogger(__file__)
    logger.setLevel(logging.INFO)
    refresh_plows()
