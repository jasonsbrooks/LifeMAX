import requests
from app import app,db,models
from flask import request,jsonify,redirect
from urlparse import parse_qs
import hashlib
@app.route('/api/fbcallback', methods = ['GET'])
def verify():
	challenge=request.args.get('hub.challenge')
	return challenge
@app.route('/api/fbcallback', methods = ['POST'])
def updatefriends():
	r=request.getjson()
	for i in r['entry']:
		if 'friends' in i['changed_fields']:
			user=models.User.query.filter_by(fbid=i['uid'])
			r=requests.get('https://graph.facebook.com/me/friends?access_token='+user.token)
			for i in r.json()['data']:
				friendid=i['id']
				friend=models.User.query.filter_by(fbid=friendid).first()
				if (friend!=None):
					newfriend1=models.Friends(userid=user.id,friendid=friend.id)
					newfriend2=models.Friends(userid=friend.id,friendid=user.id)
					db.session.add(newfriend1)
					db.session.add(newfriend2)
					db.session.commit()
	return 'Updated!'

@app.route('/api/register', methods = ['POST'])	
def register():
	shortToken=request.args.get('shortToken')
	r=requests.get('https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=563126443760291&client_secret=f94db9242158077af965906aee82181d&fb_exchange_token='+shortToken)
	longToken=parse_qs(r.text)['access_token'][0]
	md5token=hashlib.md5(longToken).hexdigest()
	r=requests.get('https://graph.facebook.com/me?access_token='+longToken)
	lookupid=int(r.json()['id'])
	if(models.User.query.filter_by(fbid=lookupid).all()!=None):
		return "Error: User exists!"
	newuser=models.User(lookupid, longToken, md5Token)
	db.session.add(newuser)
	db.session.commit()
	r=requests.get('https://graph.facebook.com/me/friends?access_token='+longToken)
	for i in r.json()['data']:
		friendid=i['id']
		friend=models.User.query.filter_by(fbid=friendid).first()
		if (friend!=None):
			newfriend1=models.Friends(userid=newuser.id,friendid=friend.id)
			newfriend2=models.Friends(userid=friend.id,friendid=newuser.id)
			db.session.add(newfriend1)
			db.session.add(newfriend2)
			db.session.commit()

	return jsonify(authToken=longToken,fbid=lookupid)
@app.route('/api/login', methods = ['GET'])
def login():
	shortToken=request.args.get('userToken')
	r=requests.get('https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=563126443760291&client_secret=f94db9242158077af965906aee82181d&fb_exchange_token='+shortToken)
	longToken=parse_qs(r.text)['access_token'][0]
	md5token=hashlib.md5(longToken).hexdigest()
	r=requests.get('https://graph.facebook.com/me?access_token='+longToken)
	lookupid=int(r.json()['id'])
	if(models.User.query.filter_by(fbid=lookupid).all()==None):
		return "Error: User does not exist!"
	db.session.query(models.User).filter(models.User.fbid==lookupid).update({"token":longToken,"md5token":md5token})
	db.session.commit()
	return jsonify(authToken=longToken,fbid=lookupid)

@app.route('/api/user/<int:userid>/tasklists', methods = ['GET'])
def getTasklists(userid):
	hashToken=request.args.get('hashToken')
	userToken=models.User.query.get(userid).md5token
	if (hashToken!=userToken):
		return "Error: Access Denied"
	UserLists=models.TaskList.query.filter_by(user=userid).all()
	taskLists=[str(i.id) for i in UserLists]
	return jsonify(taskListCount=len(UserLists),taskLists=taskLists)
@app.route('/api/user/<int:userid>/tasklists', methods = ['POST'])
def addTasklist(userid):
	hashToken=request.form['hashToken']
	userToken=models.User.query.get(userid).md5token
	if (hashToken!=userToken):
		return jsonify(success='false')
	name=request.form['name']
	newTaskList=models.TaskList(userid,name)
	db.session.add(newTaskList)
	db.session.commit()

	return jsonify(success=True,taskListID=newTaskList.id)
@app.route('/api/user/<int:userid>/tasklist/<int:tasklistid>/tasks', methods = ['GET'])
def getTasksInList(userid,tasklistid):
	hashToken=request.args.get('hashToken')
	userToken=models.User.query.get(userid).md5token
	if (hashToken!=userToken):
		return "Error: Access Denied"
	if (models.TaskList.query.get(tasklistid).user!=userid):
		return "Error: TaskList does not belong to User"
	
	tasks=models.Task.query.filter_by(tasklist=tasklistid).all()
	tasksinlist=[str(i.id) for i in tasks]
	return jsonify(name=models.TaskList.query.get(tasklistid).name,taskCount=len(tasks),tasks=tasksinlist)

@app.route('/api/user/<int:userid>/tasklist/<int:tasklistid>/tasks', methods = ['POST'])
def addTask(userid,tasklistid):
	hashToken=request.form['hashToken']
	userToken=models.User.query.get(userid).md5token
	if (hashToken!=userToken):
		return "Error: Access Denied"
	if (models.TaskList.query.get(tasklistid).user!=userid):
		return "Error: TaskList does not belong to User"
	name=request.form['name']
	description=request.form['description']
	location=request.form['location']
	starttime=request.form['starttime']
	endtime=request.form['endtime']
	newTask=models.Task(user=userid, name=request.form['name'], tasklist=tasklistid, description=request.form['description'], location=request.form['location'], starttime=request.form['starttime'], endtime=request.form['endtime'], photo=request.form['pictureurl'], completion=False)
	db.session.add(newTask)
	db.session.commit()
	return jsonify(success=True,taskID=newTask.id)
@app.route('/api/user/<int:userid>/tasklist/<int:tasklistid>', methods = ['DELETE'])
def deleteTaskList(userid,tasklistid):
	hashToken=request.args.get('hashToken')
	userToken=models.User.query.get(userid).md5token
	if (hashToken!=userToken):
		return jsonify(success=False)
	if (models.TaskList.query.get(tasklistid).user!=userid):
		return jsonify(success=False)
	taskListToDelete=models.TaskList.query.get(tasklistid)
	db.session.delete(taskListToDelete)
	db.session.commit()	
	return jsonify(success=True)
@app.route('/api/user/<int:userid>/tasklist/<int:tasklistid>/task/<int:taskid>', methods = ['GET'])
def getTask(userid,tasklistid,taskid):
	hashToken=request.args.get('hashToken')
	userToken=models.User.query.get(userid).md5token
	if (hashToken!=userToken):
		return "Error: Access Denied"
	if (models.TaskList.query.get(tasklistid).user!=userid):
		return "Error: TaskList does not belong to User"
	if (models.Task.query.get(taskid).tasklist!=tasklistid):
		return "Error: Task does not belong to TaskList"

	task=models.Task.query.get(taskid)
	return jsonify(name=task.name, description=task.description, location=task.location, starttime=task.starttime, endtime=task.endtime, pictureurl=task.photo, completion=task.completion)

@app.route('/api/user/<int:userid>/tasklist/<int:tasklistid>/task/<int:taskid>', methods = ['DELETE'])
def deleteTask(userid,tasklistid,taskid):
	hashToken=request.args.get('hashToken')
	userToken=models.User.query.get(userid).md5token
	if (hashToken!=userToken):
		return jsonify(success=False)
	if (models.TaskList.query.get(tasklistid).user!=userid):
		return jsonify(success=False)
	if (models.Task.query.get(taskid).tasklist!=tasklistid):
		return jsonify(success=False)
	taskToDelete=models.Task.query.get(taskid)
	db.session.delete(taskToDelete)
	db.session.commit()
	return jsonify(success=True)
@app.route('/caslogin', methods = ['GET'])
def caslogin():
	if request.args.get('ticket')==None:
		return redirect("https://secure.its.yale.edu/cas/login?service=http://localhost:5000/caslogin")
	r=requests.get('https://secure.its.yale.edu/cas/serviceValidate?service=http://localhost:5000/caslogin&ticket='+request.args.get('ticket'))
	f=r.text.find('<cas:user>')
	if (f==-1):
		return 'Login failed!'
	return r.text[f+10:r.text.find('<',f+1)]
