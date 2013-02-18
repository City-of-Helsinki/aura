from datetime import datetime, timedelta
import json
import mongoengine
from flask import Flask, request, make_response
from flask.ext import restful
from flask.ext.restful import fields, reqparse, abort

from models import *
import settings

app = Flask(__name__)
api = restful.Api(app)

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

class SnowPlow(restful.Resource):
    @restful.marshal_with(point_fields)
    def serialize_point(self, point):
        return point

    def serialize(self, plow, history):
        last_loc = self.serialize_point(plow.last_loc)
        ret = {'id': unicode(plow.id), 'last_loc': last_loc}
        if history and history > 0:
            ret['history'] = [self.serialize_point(p) for p in plow.points[-history:-1]]
        return ret

    def get(self, plow_id):
        args = parser.parse_args()
        history = args['history']
        plows = Plow.objects
        if history > 0:
            plows = plows.fields(slice__points=-history)
        else:
            plows = plows.exclude('points')
        try:
            plow = plows.get(id=plow_id)
        except Plow.DoesNotExist:
            abort(404, message="Plow {} does not exist".format(plow_id))
        return self.serialize(plow, history)

api.add_resource(SnowPlow, '/api/v1/snowplow/<int:plow_id>')

class SnowPlowList(restful.Resource):
    def get(self):
        plow_res = SnowPlow()
        args = parser.parse_args()
        history = args['history']
        plows = Plow.objects.all().order_by('-last_loc__timestamp')
        # Exclude the points field to speed up queries.
        if history > 0:
            plows = plows.fields(slice__points=-history)
        else:
            plows = plows.exclude('points')
        now = datetime.now()
        # List either all the plows from the last 24h or the most recent 10 plows.
        plows_24h = plows.filter(last_loc__timestamp__gte=now - timedelta(days=1))
        if plows_24h.count() < 10:
            plows = plows[0:10]
        else:
            plows = plows_24h
        return [plow_res.serialize(plow, False) for plow in plows]

api.add_resource(SnowPlowList, '/api/v1/snowplow/')

mongoengine.connect(settings.MONGO_DB)

if __name__ == '__main__':
    app.run(debug=True)
