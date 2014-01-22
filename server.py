from datetime import datetime, timedelta
import json
import timelib
import mongoengine
from flask import Flask, request, make_response
from flask.ext import restful
from flask.ext.restful import fields, reqparse, abort
from flask.ext.sqlalchemy import SQLAlchemy

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, joinedload, subqueryload

from sqlmodels import *
import settings


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URL
#app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

api = restful.Api(app)

CORS_HEADERS = [
    ("Access-Control-Allow-Origin", "*"),
    ("Access-Control-Allow-Methods", ', '.join(["GET", "OPTIONS"])),
    ("Access-Control-Allow-Headers", ', '.join(["Content-Type"])),
]

def add_cors_headers(resp):
    for hdr in CORS_HEADERS:
        resp.headers.add_header(hdr[0], hdr[1])
    return resp
app.after_request(add_cors_headers)


@api.representation('application/json')
def output_jsonp(data, code, headers=None):
    json_str = json.dumps(data)
    callback = request.args.get('callback', False)
    if callback:
        content = str(callback) + '(' + json_str + ');'
    else:
        content = json_str
    resp = make_response(content, code)
    resp.headers.extend(headers or {})
    return resp

class ISODateTimeField(fields.Raw):
    """Return a ISO 8601 formatted datetime string"""

    def format(self, value):
        try:
            return datetime.isoformat(value)
        except AttributeError as ae:
            raise fields.MarshallingException(ae)

point_fields = {
    'timestamp': ISODateTimeField,
    'coords': fields.Raw,
    'events': fields.Raw
}

parser = reqparse.RequestParser()
parser.add_argument('history', type=int, help="Number of location history entries to return")
parser.add_argument('since', type=str, help="Return plows since provided time")
parser.add_argument('limit', type=int, help="How many plows to return")
parser.add_argument('temporal_resolution', type=int, help="Temporal resolution of historical plow locations")

class SnowPlow(restful.Resource):
    @restful.marshal_with(point_fields)
    def serialize_point(self, point):
        d = {'coords': [point.lon, point.lat]}
        d['timestamp'] = point.timestamp
        d['events'] = [ev.id for ev in point.events]
        return d

    def serialize(self, plow, points=[]):
        ret = {'id': unicode(plow.id)}
        last_loc = db.session.query(Point).options(subqueryload(Point.events)).filter_by(plow_id=plow.id).order_by(desc('"index"')).first()
        if last_loc:
            last_loc = self.serialize_point(last_loc)
        ret = {'id': unicode(plow.id), 'last_location': last_loc}
        ret['location_history'] = [self.serialize_point(p) for p in points]
        return ret

    def get(self, plow_id):
        args = parser.parse_args()
        history = args['history']

        since = args['since']
        if since:
            try:
                since = datetime.fromtimestamp(timelib.strtotime(since))
            except ValueError, TypeError:
                since = None

        temporal_resolution = args['temporal_resolution']
        if temporal_resolution:
            try:
                temporal_resolution = int(temporal_resolution)
            except ValueError:
                temporal_resolution = None

        plow = db.session.query(Plow).filter_by(id=plow_id).first()
        if not plow:
            abort(404, message="Plow {} does not exist".format(plow_id))

        points = db.session.query(Point).filter_by(plow=plow).order_by('"index"')
        points = points.options(subqueryload(Point.events))
        if since:
            points = points.filter(Point.timestamp >= since)
        elif history > 0:
            points = points[-history:]
        else:
            points = []

        if temporal_resolution is not None:
            out = []
            for p in points:
                if not out:
                    out.append(p)
                    continue
                delta = p.timestamp - out[-1].timestamp
                if delta < timedelta(seconds=temporal_resolution):
                    continue
                out.append(p)
            points = out
        return self.serialize(plow, points)

api.add_resource(SnowPlow, '/api/v1/snowplow/<int:plow_id>')

class SnowPlowList(restful.Resource):
    def get(self):
        plows = db.session.query(Plow).order_by(desc('last_timestamp'))
        plow_res = SnowPlow()
        args = parser.parse_args()

        since = args['since']
        if since:
            try:
                since = datetime.fromtimestamp(timelib.strtotime(since))
            except ValueError, TypeError:
                since = None
        else:
            since = None
        if since:
            plows = plows.filter(Plow.last_timestamp >= since)

        limit = args['limit']
        # Return by default 10 plows
        if not since and not limit:
            limit = 10
        if limit > 0:
            plows = plows[0:limit]
        return [plow_res.serialize(plow) for plow in plows]

api.add_resource(SnowPlowList, '/api/v1/snowplow/')

if __name__ == '__main__':
    app.run(debug=True)
