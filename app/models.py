from app import db
import datetime
import time

class TimestampMixin(object):
    created_at = db.Column(db.DateTime, default=datetime.datetime.now())

class LifeMaxIds(TimestampMixin, db.Model):
	__tablename__="LifeMaxIds"
	id = db.Column(db.Integer, primary_key = True)
	#gtoken = db.Column(db.String(100),nullable=True)
	#grtoken = db.Column(db.String(100),nullable=True)
	#lastupdatedtoken = db.Column(db.Integer)
class User(TimestampMixin, db.Model):
	__tablename__="User"
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String(100))
	profilepic=db.Column(db.String(1000))
	fbid = db.Column(db.String(100), index = True, unique = True)
	token = db.Column(db.String(1000))
	md5token = db.Column(db.String(100))
	#gtoken = db.Column(db.String(100),nullable=True)
	#grtoken = db.Column(db.String(100),nullable=True)
	lastupdatedtoken = db.Column(db.Integer, nullable=True)
	#gidcalendar=db.Column(db.String(100),nullable=True)
	tasks = db.relationship('Task', backref = 'owner', lazy = 'dynamic', primaryjoin="Task.user==User.id")
	friends=db.relationship('Friends', backref = 'owner', lazy= 'dynamic', primaryjoin="Friends.userid==User.id")
	privacy=db.Column(db.Integer)

	def __repr__(self):
		return '#%d: Name: %s, ProfilePic: %s, FBID: %s, Privacy: %d' % (self.id, self.name, self.profilepic, self.fbid, self.privacy)

class Task(TimestampMixin, db.Model):
	__tablename__="Task"
	id = db.Column(db.Integer, primary_key = True)
	user = db.Column(db.Integer, db.ForeignKey('User.id'))
	name = db.Column(db.String(50))
	hashtag = db.Column(db.String(50))
	# description = db.Column(db.String(1200))
	# location = db.Column(db.String(50))
	pictureurl = db.Column(db.String(200))
	# completion = db.Column(db.Boolean)
	private = db.Column(db.Boolean, default = False)
	completed = db.Column(db.Boolean, default = False)
	timecompleted = db.Column(db.DateTime, default=None)

	def __repr__(self):
		return '#%d, User: %d, Name: %s, Hashtag: %s, PictureURL: %s, Privacy: %d, Time Completed: %s' %(self.id, self.user, self.name, self.hashtag, self.pictureurl, self.private, self.timecompleted)

class Friends(TimestampMixin, db.Model):
	__tablename__="Friends"
	id = db.Column(db.Integer, primary_key = True)
	userid = db.Column(db.Integer, db.ForeignKey('User.id'))
	friendid = db.Column(db.Integer, db.ForeignKey('User.id'))
