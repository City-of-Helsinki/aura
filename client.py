import time
import datetime
import requests
import mongoengine
import logging

#import requests_cache
#requests_cache.configure('cache')

from models import *
import settings

connect(settings.MONGO_DB)

def refresh_plows():
    print "connecting"
    r = requests.get(settings.URL, auth=settings.AUTH)
    if r.status_code != 200:
        raise Exception("HTTP request failed with HTTP%d" % r.status_code)
    plow_list = r.json
    print "got info for %d plows" % len(plow_list)
    for plow in plow_list:
        pl = Plow.objects(id=plow['id'])
        if pl:
            pl = pl[0]
        else:
            pl = Plow(id=plow['id'], points=[])

        new_points = 0
        for point in plow['points']:
            ts = point['timestamp']
            # Parse ISO 8601 timestamp
            ts = datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")
            point_info = {}
            point_info['coords'] = (point['x'], point['y'])
            point_info['events'] = point['events'].split(',')
            point_info['timestamp'] = ts
            for idx, p in enumerate(pl.points):
                # If the timestamp already exists, skip it.
                if p.timestamp == ts:
                    break
                if ts < p.timestamp:
                    pl.points.insert(idx, Point(**point_info))
                    new_points += 1
                    break
            else:
                pl.points.append(Point(**point_info))
                new_points += 1
        print "plow %d: %d new points" % (plow['id'], new_points)
        if new_points:
            pl.last_loc = pl.points[-1]
            pl.first_loc = pl.points[0]
            pl.save()

if __name__ == '__main__':
    logging.basicConfig()
    logger = logging.getLogger(__file__)
    logger.setLevel(logging.INFO)
    logger.info("test!")
    refresh_plows()
