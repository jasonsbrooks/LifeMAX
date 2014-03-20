from app.models import *
import datetime
db.drop_all()
db.create_all()
u = User(id=0, name="Max", fbid="12345", privacy=0)
db.session.add(u)
db.session.commit()

