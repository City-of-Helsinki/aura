from mongoengine import *

class Point(EmbeddedDocument):
    timestamp = DateTimeField(required=True)
    coords = GeoPointField(required=True)
    events = ListField(StringField(required=True))

    def __unicode__(self):
        return "%s (%s) at %f, %f" % (self.timestamp, ', '.join(self.events),
                self.coords[0], self.coords[1])

class Plow(Document):
    id = IntField(unique=True, primary_key=True)
    first_loc = EmbeddedDocumentField(Point)
    last_loc = EmbeddedDocumentField(Point)
    points = ListField(EmbeddedDocumentField(Point))

    def __unicode__(self):
        return "%d (first %s; last %s; %d points)" % (self.id,
                self.first_loc, self.last_loc, len(self.points))