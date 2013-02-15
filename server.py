from datetime import datetime
import json
import mongoengine
from flask import Flask, request, make_response
from flask.ext import restful
from flask.ext.restful import fields, reqparse
from models import *


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
parser.add_argument('history', type=bool, help="Return plow location history")

class SnowPlow(restful.Resource):
    @restful.marshal_with(point_fields)
    def serialize_point(self, point):
        return point

    def serialize(self, plow, history):
        last_loc = self.serialize_point(plow.last_loc)
        ret = {'id': unicode(plow.id), 'last_loc': last_loc}
        if history:
            ret['history'] = [self.serialize_point(p) for p in plow.points]
        return ret

    def get(self):
        args = parser.parse_args()
        history = args['history']
        plows = Plow.objects.all()
        return [self.serialize(plow, history) for plow in plows]

api.add_resource(SnowPlow, '/api/snowplows')

mongoengine.connect('test')

app.run(debug=True)
