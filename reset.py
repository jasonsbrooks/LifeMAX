from app.models import *
import datetime
print "Dropping Tables"
db.drop_all()
print "Creating Tables"
db.create_all()
print "Creating Default User"
u = User(id=0, name="Max", fbid="12345", privacy=0, points=15)
u1 = User(name="Max", fbid="123456", privacy=0, points=20)
u2 = User(name="Max", fbid="123457", privacy=0, points=25)
u3 = User(name="Max", fbid="123458", privacy=0, points=8)
db.session.add(u)
db.session.add(u1)
db.session.add(u2)
db.session.add(u3)
db.session.commit()
f = Friends(userid=u1.id,friendid=u.id)
f1 = Friends(userid=u2.id,friendid=u.id)
f2 = Friends(userid=u3.id,friendid=u.id)
f3 = Friends(userid=u1.id,friendid=u2.id)
f4 = Friends(userid=u1.id,friendid=u3.id)
db.session.add(f)
db.session.add(f1)
db.session.add(f2)
db.session.add(f3)
db.session.add(f4)
db.session.commit()

