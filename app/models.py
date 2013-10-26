from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    fbid = db.Column(db.Integer, index = True, unique = True)
    token = db.Column(db.String(1000))
    md5token = db.Column(db.String(100))
    tasklists = db.relationship('TaskList', backref = 'owner', lazy = 'dynamic')
    tasks = db.relationship('Task', backref = 'owner', lazy = 'dynamic')

class TaskList(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	user = db.Column(db.Integer, db.ForeignKey('user.id'))
	name = db.Column(db.String(120), index=True)


class Task(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	user = db.Column(db.Integer, db.ForeignKey('user.id'))
	name = db.Column(db.String(120))
	tasklist = db.Column(db.Integer, index = True)
	description = db.Column(db.String(1200))
	location = db.Column(db.String(250))
	starttime = db.Column(db.String(10))
	endtime = db.Column(db.String(10))
	frequency = db.Column(db.String(10))
	photo = db.Column(db.String(20))
	completion = db.Column(db.Boolean)
