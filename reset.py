from app.models import *
import datetime
db.drop_all()
db.create_all()



# for hashtag in defaultTasks:
# 	for name in defaultTasks[hashtag]:
# 		t = Task(user=0, name=name, hashtag=hashtag, completed=True, timecompleted=datetime.datetime.now())
# 		db.session.add(t)
# 		db.session.commit()

