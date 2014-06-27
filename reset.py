from app.models import *
import datetime
print "Dropping Tables"
db.drop_all()
print "Creating Tables"
db.create_all()
print "Creating Default User"
u = User(id=0, name="Max", fbid="12345", privacy=0, points=0)
db.session.add(u)
db.session.commit()

