from app import db
class LifeMaxIds(db.Model):
	__tablename__="LifeMaxIds"
	id = db.Column(db.Integer, primary_key = True)
	#gtoken = db.Column(db.String(100),nullable=True)
	#grtoken = db.Column(db.String(100),nullable=True)
	#lastupdatedtoken = db.Column(db.Integer)
class User(db.Model):
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

"""
class TaskList(db.Model):
	https://www.facebook.com/connect/login_success.html#access_token=CAAIAKRek2qMBABA2zXOes2QTGD6EBiRKPOZBZAfwE51u6EVqWZCG1pqw2DIBPFGlyCnXYli0kkWrQMkAzhYclte0sAs5u8Glp5PCDTL40YykXjSxMlRqXUOpvAjfQReZA3ZBllWOUY05Hft6iqjQNOtaMdm8cF3Seb3zFyZCDKzR0yoZBw37KHLChyZBGbWgy69VHfdx6sAS7QZDZD&expires_in=5071
	__tablename__="TaskList"
	id = db.Column(db.Integer, primary_key = True)
	user = db.Column(db.Integer, db.ForeignKey('User.id'))
	tasks = db.relationship('Task', backref = 'list', lazy = 'dynamic', primaryjoin="Task.tasklist==TaskList.id")
	taskinfinitives = db.relationship = db.relationship('TaskInfinitives', backref = 'list', lazy = 'dynamic', primaryjoin="TaskInfinitives.tasklist==TaskList.id" )
	name = db.Column(db.String(50))
"""
class Task(db.Model):
	__tablename__="Task"
	id = db.Column(db.Integer, primary_key = True)
	user = db.Column(db.Integer, db.ForeignKey('User.id'))
	name = db.Column(db.String(50))
	hashtag = db.Column(db.String(50))
	description = db.Column(db.String(1200))
	location = db.Column(db.String(50))
	pictureurl = db.Column(db.String(200))
	completion = db.Column(db.Boolean)
	timecompleted = db.Column(db.Integer, nullable=True, index = True)

"""
class TaskInfinitives(db.Model):
	__tablename__="TaskInfinitives"
	id = db.Column(db.Integer, primary_key = True)
	user = db.Column(db.Integer, db.ForeignKey('User.id'))
	name = db.Column(db.String(50))
	tasklist = db.Column(db.Integer, db.ForeignKey('TaskList.id'))
	description = db.Column(db.String(1200))
	location = db.Column(db.String(250))
	starttime = db.Column(db.String(20))
	endtime = db.Column(db.String(20))
	repeat_year=db.Column(db.Integer)
	repeat_month=db.Column(db.Integer)
	repeat_day=db.Column(db.Integer)
	repeat_week=db.Column(db.Integer)
	repeat_weekday=db.Column(db.Integer)
	photo = db.Column(db.String(200))
"""	
class Friends(db.Model):
	__tablename__="Friends"
	id = db.Column(db.Integer, primary_key = True)
	userid = db.Column(db.Integer, db.ForeignKey('User.id'))
	friendid = db.Column(db.Integer, db.ForeignKey('User.id'))
