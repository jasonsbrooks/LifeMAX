from app import db

class User(db.Model):
	__tablename__="User"
	id = db.Column(db.Integer, primary_key = True)
	fbid = db.Column(db.Integer, index = True, unique = True)
	token = db.Column(db.String(1000))
	md5token = db.Column(db.String(100))
	tasklists = db.relationship('TaskList', backref = 'owner', lazy = 'dynamic', primaryjoin="TaskList.user==User.id")
	tasks = db.relationship('Task', backref = 'owner', lazy = 'dynamic', primaryjoin="Task.user==User.id")
	taskinfinitives = db.relationship('TaskInfinitives', backref = 'owner', lazy = 'dynamic', primaryjoin="TaskInfinitives.user==User.id")
	friends=db.relationship('Friends', backref = 'owner', lazy= 'dynamic', primaryjoin="Friends.userid==User.id")

class TaskList(db.Model):
	__tablename__="TaskList"
	id = db.Column(db.Integer, primary_key = True)
	user = db.Column(db.Integer, db.ForeignKey('User.id'))
	tasks = db.relationship('Task', backref = 'list', lazy = 'dynamic', primaryjoin="Task.tasklist==TaskList.id")
	taskinfinitives = db.relationship = db.relationship('TaskInfinitives', backref = 'list', lazy = 'dynamic', primaryjoin="TaskInfinitives.tasklist==TaskList.id" )
	name = db.Column(db.String(50))

class Task(db.Model):
	__tablename__="Task"
	id = db.Column(db.Integer, primary_key = True)
	user = db.Column(db.Integer, db.ForeignKey('User.id'))
	name = db.Column(db.String(50))
	tasklist = db.Column(db.Integer, db.ForeignKey('TaskList.id'))
	description = db.Column(db.String(1200))
	location = db.Column(db.String(50))
	starttime = db.Column(db.String(20))
	endtime = db.Column(db.String(20))
	photo = db.Column(db.String(200))
	completion = db.Column(db.Boolean)

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
	photo = db.Column(db.String(200))
	period = db.Column(db.Integer)

class Friends(db.Model):
	__tablename__="Friends"
	id = db.Column(db.Integer, primary_key = True)
	userid = db.Column(db.Integer, db.ForeignKey('User.id'))
	friendid = db.Column(db.Integer, db.ForeignKey('User.id'))
