import requests
from app import app,db,models
from flask import request,jsonify
from urlparse import parse_qs
import hashlib
@app.route('/login', methods = ['GET'])
def returnkey():
	shortToken=request.args.get('userToken')
	r=requests.get('https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=563126443760291&client_secret=f94db9242158077af965906aee82181d&fb_exchange_token='+shortToken)
	longToken=parse_qs(r.text)['access_token'][0]
	md5token=hashlib.md5(longToken).hexdigest()
	r=requests.get('https://graph.facebook.com/me?access_token='+longToken)
	lookupid=int(r.json()['id'])
	db.session.query(models.User).filter(models.User.fbid==lookupid).update({"token":longToken,"md5token":md5token})
	db.session.commit()
	return jsonify(longToken=longToken, md5token=md5token)

@app.route('/user/<int:userid>/tasklists', methods = ['GET'])
def tasklists(userid):
	"""hashToken=request.args.get('hashToken')
	userToken=User.get(userid).md5token
	if (hashToken!=userToken):
		return "Error: Access Denied"
	"""
	UserLists=models.TaskList.query.filter_by(user=userid).all()
	taskLists=[str(i.id) for i in UserLists]
	return jsonify(taskListCount=len(UserLists),taskLists=taskLists)

@app.route('/user/<int:userid>/tasklist/<int:tasklistid>', methods = ['GET'])
def tasksinlist(userid,tasklistid):
	"""hashToken=request.args.get('hashToken')
	userToken=User.get(userid).md5token
	if (hashToken!=userToken):
		return "Error: Access Denied"
	if (TaskList.query.get(tasklistid).user!=userid):
		return "Error: TaskList does not belong to User"
	"""
	tasks=models.Task.query.filter_by(tasklist=tasklistid).all()
	tasksinlist=[str(i.id) for i in tasks]
	return jsonify(name=models.TaskList.query.get(tasklistid).name,taskCount=len(tasks),tasks=tasksinlist)

@app.route('/user/<int:userid>/tasklist/<int:tasklistid>/task/<int:taskid>', methods = ['GET'])
def gettask(userid,tasklistid,taskid):
	"""hashToken=request.args.get('hashToken')
	userToken=User.get(userid).md5token
	if (hashToken!=userToken):
		return "Error: Access Denied"
	if (TaskList.query.get(tasklistid).user!=userid):
		return "Error: TaskList does not belong to User"
	if (Task.query.get(taskid).tasklist!=tasklistid):
		return "Error: Task does not belong to TaskList"
	"""
	task=models.Task.query.get(taskid)
	return jsonify(description=task.description, location=task.location, starttime=task.starttime, endtime=task.endtime, pictureurl=task.photo, completion=task.completion)