from mongoengine import *

class Point(EmbeddedDocument):
    timestamp = DateTimeField(required=True)
    coords = GeoPointField(required=True)
    events = ListField(StringField(required=True))

class Plow(Document):
    id = IntField(unique=True, primary_key=True)
    first_loc = EmbeddedDocumentField(Point)
    last_loc = EmbeddedDocumentField(Point)
    points = ListField(EmbeddedDocumentField(Point))
