import requests
from app import app,db,models
from flask import request,jsonify,redirect,Response, abort
from urlparse import parse_qs
import hashlib
import re
import time
import datetime
import httplib2
from apiclient.discovery import build
from oauth2client import client
import ast
import json
import sys, traceback
from sqlalchemy import desc
import boto
from boto.s3.key import Key
import os
import hashlib
from hashtags import defaultTasks, imageAssociations
import pdb
import random

FACEBOOK_CLIENT_ID='670660326330598'
FACEBOOK_CLIENT_SECRET='0ec602b31b2220aaafc41043b699abcf'
GOOGLE_CLIENT_ID='XXXXXX'
GOOGLE_CLIENT_SECRET='XXXXXXXXX'
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
true=True

def createTaskJSON(task):
	u = models.User.query.get(task.user)
	userJSON = {'id' : u.id, 'name' : u.name, 'fbid': u.fbid}
	if task.timecompleted is None:
		tc = None
	else:
		tc = task.timecompleted.strftime("%Y-%m-%dT%H:%M:%SZ")
	completeJSON = {'id':task.id, 'description': task.description, 'user':userJSON, 'name': task.name, 'hashtag': task.hashtag, 'pictureurl': task.pictureurl, 'private': task.private, 'completed': task.completed, 'timecompleted': tc, 'timecreated': task.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")}
	return completeJSON

def randomTask():
	mostRecent = models.Task.query.filter(models.Task.user == 0).order_by(models.Task.id.desc()).first()
	cont = False
	if mostRecent is not None:
		a = mostRecent.created_at
		b = datetime.datetime.utcnow()
		if (b-a).total_seconds() < 43200:
			return
	ht = random.choice(defaultTasks.keys())
	taskName = random.choice(defaultTasks[ht])
	task = models.Task(user=0, name=taskName, description="Hello matey isn't it a fine day for some swimming? I hope we win the world cup soon", hashtag=ht, completed=True, timecompleted=datetime.datetime.utcnow(), created_at=datetime.datetime.utcnow())
	db.session.add(task)
	db.session.commit()

def manualRandomTask():
	ht = random.choice(defaultTasks.keys())
	taskName = random.choice(defaultTasks[ht])
	task = models.Task(user=0, name=taskName, description="Hello matey isn't it a fine day for some swimming? I hope we win the world cup soon", hashtag=ht, completed=True, timecompleted=datetime.datetime.utcnow(), created_at=datetime.datetime.utcnow())
	db.session.add(task)
	db.session.commit()

@app.route('/api/fbcallback', methods = ['GET'])
def verify():
	challenge=0
	if(request.args.get('hub.verify_token')=='boolaboola'):
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
	try:
		# shortToken=request.form['shortToken']
		shortToken=request.get_json().get('shortToken')
		r=requests.get('https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id='+FACEBOOK_CLIENT_ID+'&client_secret='+FACEBOOK_CLIENT_SECRET+'&fb_exchange_token='+shortToken)
		try:
			longToken=parse_qs(r.text)['access_token'][0]
		except:
			return "Error: Invalid Token"
		md5token=hashlib.md5(longToken).hexdigest()
		r=requests.get('https://graph.facebook.com/me?access_token='+longToken)
		lookupid=r.json()['id']
		if(models.User.query.filter_by(fbid=lookupid).first()!=None):
			return "Error: User exists!"
		r=requests.get('https://graph.facebook.com/'+lookupid)
		name=r.json()['name']
		r=requests.get('https://graph.facebook.com/'+lookupid+'/picture',allow_redirects=False)
		pic=r.headers['location']
		privacy=request.get_json().get('privacy')
		newuser=models.User(fbid=lookupid, token=longToken, md5token=md5token,name=name,profilepic=pic,privacy=privacy)
		db.session.add(newuser)
		db.session.commit()
		maxfriend=models.Friends(userid=newuser.id,friendid=0)
		db.session.add(maxfriend)
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
		#service=gconnect(models.LifeMaxIds.query.first())
		#body={'summary': 'User '+str(newuser.id)+'\'sLifeMaxCalendar'}
		#createdcalendar=service.calendars().insert(body=body).execute()
		#newuser.gidcalendar=createdcalendar['id']
		#service.calendarList().insert(body={'id':createdcalendar['id']}).execute()
		db.session.commit()
		return jsonify(authToken=longToken,fbid=lookupid,id=newuser.id)
	except:
		print str(traceback.format_exception(*sys.exc_info()))
		return str(traceback.format_exception(*sys.exc_info()))
@app.route('/api/<int:userid>/privacychange',methods=['POST'])
def privacychange(userid):
	try:
		hashToken=request.form.get('hashToken',None)
		userToken=models.User.query.get(userid).md5token
		if (hashToken!=userToken):
			return "Error: Access Denied"
		privacy=int(request.form.get('privacy'))
		models.User.query.get(userid).privacy=privacy
		db.session.commit()
	except:
		print str(traceback.format_exception(*sys.exc_info()))
		return str(traceback.format_exception(*sys.exc_info()))

def objectforhashtag(hashtag):
	response = {'imageurl' : imageAssociations[hashtag], 'hashtag' : hashtag}
	return response

@app.route('/api/hashtags', methods = ['GET'])
def gethashtags():
	try:
		response = []
		for hashtag in defaultTasks.keys():
			response.append(objectforhashtag(hashtag))
		json_resp = jsonify(hashtags=response)
		print json_resp
		return json_resp
	except:
		print str(traceback.format_exception(*sys.exc_info()))
		return str(traceback.format_exception(*sys.exc_info()))

@app.route('/api/imageforhashtag', methods=['GET'])
def imageforhashtag():
	try:
		hashtag = request.args.get('hashtag')
		imageurl = imageAssociations.get('hashtag', None)
		# print '%s -> %s' (hashtag, imageurl)
		if(imageurl != None):
			return redirect(imageurl, code=302)
		return Response('', status=404)

	except: 
		print str(traceback.format_exception(*sys.exc_info()))
		return str(traceback.format_exception(*sys.exc_info()))

@app.route('/api/login', methods = ['GET'])
def login():
	try:
		shortToken=request.args.get('userToken')
		r=requests.get('https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id='+FACEBOOK_CLIENT_ID+'&client_secret='+FACEBOOK_CLIENT_SECRET+'&fb_exchange_token='+shortToken)
		print r.text
		longToken=parse_qs(r.text)['access_token'][0]
		md5token=hashlib.md5(longToken).hexdigest()
		r=requests.get('https://graph.facebook.com/me?access_token='+longToken)
		lookupid=r.json()['id']
		loginuser=models.User.query.filter_by(fbid=lookupid).first()
		if loginuser==None:
			return "Error: User does not exist!"
		db.session.query(models.User).filter(models.User.fbid==lookupid).update({"token":longToken,"md5token":md5token})
		db.session.commit()
		json_resp = jsonify(authToken=longToken,fbid=lookupid, id=loginuser.id)
		print json_resp
		return json_resp
	except:
		print str(traceback.format_exception(*sys.exc_info()))
		return str(traceback.format_exception(*sys.exc_info()))

@app.route('/api/user/<int:userid>/maxsuggests', methods=['GET'])
def maxsuggests(userid):
	try:
		hashToken=request.args.get('hashToken',None)
		userToken=models.User.query.get(userid).md5token
		if (hashToken!=userToken):
			return "Error: Access Denied"
		randomTask()
		returndict={'items':[]}
		maxResults=request.args.get('maxResults',None)
		if (maxResults==None):
			maxResults=50
		friendId=request.args.get('friendId',None)
		hashtag=request.args.get('hashtag',None)
		if (hashtag == None and friendId == None):
			a = models.Task.query.filter(models.Task.user.in_([0]))
			hiddentaskids = []
			for t in models.User.query.get(userid).hiddentasks.all():
				hiddentaskids.append(t.taskid)
			if hiddentaskids:
				b = models.Task.query.filter(models.Task.id.in_(hiddentaskids))
				u = a.except_(b).order_by(desc(models.Task.timecompleted), desc(models.Task.created_at)).limit(maxResults).all()
			else:
				u = a.order_by(desc(models.Task.timecompleted), desc(models.Task.created_at)).limit(maxResults).all()
			for task in u:
				returndict['items'].append(createTaskJSON(task))
			json_resp = jsonify(returndict)
			print returndict
			return json_resp
	except:
		print str(traceback.format_exception(*sys.exc_info()))
		return str(traceback.format_exception(*sys.exc_info()))

@app.route('/api/user/<int:userid>/newsfeed', methods = ['GET'])
def newsfeed(userid):
	try:
		hashToken=request.args.get('hashToken',None)
		userToken=models.User.query.get(userid).md5token
		if (hashToken!=userToken):
			return "Error: Access Denied"
		randomTask()
		returndict={'items':[]}
		maxResults=request.args.get('maxResults',None)
		if (maxResults==None):
			maxResults=50
		friendId=request.args.get('friendId',None)
		hashtag=request.args.get('hashtag',None)
		listoffriends=[]
		friendtable=models.User.query.get(userid).friends
		for f in friendtable:
			if (models.User.query.get(f.friendid).privacy==0):
				listoffriends.append(f.friendid)
		if 0 in listoffriends:
			listoffriends.remove(0)
		if (hashtag == None and friendId == None):
			if listoffriends:
				a = models.Task.query.filter(models.Task.user.in_(listoffriends)).filter_by(private=False).filter_by(completed=True)
				b = models.Task.query.filter(models.Task.user.in_([userid])).filter_by(completed=True)
				u = a.union(b).order_by(desc(models.Task.timecompleted), desc(models.Task.created_at)).limit(maxResults).all()
			else:
				b = models.Task.query.filter(models.Task.user.in_([userid])).filter_by(completed=True)
				u = b.order_by(desc(models.Task.timecompleted), desc(models.Task.created_at)).limit(maxResults).all()
			for task in u:
				returndict['items'].append(createTaskJSON(task))
			json_resp = jsonify(returndict)
			print returndict
			return json_resp
		# elif (hashtag != None and friendId == None):
		# 	for task in models.Task.query.filter_by(completed=True).order_by(desc(models.Task.timecompleted)).filter(models.Task.user.in_(listoffriends)).filter_by(hashtag=hashtag).limit(maxResults).all():
		# 		returndict['items'].append(createTaskJSON(task))
		# 	json_resp = jsonify(returndict)
		# 	print json_resp
		# 	return json_resp
		# elif (hashtag == None and friendId != None):
		# 	if ((models.User.query.get(friendId) not in models.User.get(userid).friends) or models.User.query.get(friendId).privacy==1):
		# 		return "Error: Access Denied"
		# 	for task in models.Task.query.filter_by(completed=True).order_by(desc(models.Task.timecompleted)).filter_by(user=friendId).limit(maxResults).all():
		# 		returndict['items'].append(createTaskJSON(task))
		# 	json_resp = jsonify(returndict)
		# 	print json_resp
		# 	return json_resp
		# elif (hashtag != None and friendId != None):
		# 	if ((models.User.query.get(friendId) not in models.User.get(userid).friends) or models.User.query.get(friendId).privacy==1):
		# 		return "Error: Access Denied"
		# 	for task in models.Task.query.filter_by(completed=True).order_by(desc(models.Task.timecompleted)).filter_by(user=friendId).filter_by(hashtag=hashtag).limit(maxResults).all():
		# 		returndict['items'].append(createTaskJSON(task))
		# 	json_resp = jsonify(returndict)
		# 	print json_resp
		# 	return json_resp	
	except:
		print str(traceback.format_exception(*sys.exc_info()))
		return str(traceback.format_exception(*sys.exc_info()))

@app.route('/api/user/<int:userId>/tasks', methods = ['POST'])
def addTimelessTask2(userId):
	try:
		hashToken=request.get_json().get('hashToken')
		u = models.User.query.get(userId)
		userToken=u.md5token
		if (hashToken!=userToken):
			resp = "Error: Access Denied"
			print resp
			return resp
		randomTask()
		name=request.get_json().get('name')
		pictureurl=request.get_json().get('pictureurl', None)
		hashtag=request.get_json().get('hashtag')
		private=request.get_json().get('private')
		completed=request.get_json().get('completed', False)
		description=request.get_json().get('description', None)
		newTask=models.Task(user=userId, description=description, name=name, hashtag=hashtag, pictureurl=pictureurl, private=private, created_at=datetime.datetime.utcnow(), completed=completed)
		db.session.add(newTask)
		db.session.commit()
		json_resp = jsonify(createTaskJSON(newTask))
		print json_resp
		
		if completed == True:
			u.points = u.points + 1
			db.session.commit()

		maxSuggestsTask = models.Task.query.filter(models.Task.name == name).filter(models.Task.user == 0).first()
		if maxSuggestsTask:
			hidden = models.HiddenTasks(userid=userId, taskid=maxSuggestsTask.id)
			db.session.add(hidden)
			db.session.commit()
		return json_resp
	except:
		print str(traceback.format_exception(*sys.exc_info()))
		return str(traceback.format_exception(*sys.exc_info()))


@app.route('/api/user/<int:userId>/tasks', methods = ['GET'])
def getTimelessTasks2(userId):
	try:
		hashToken=request.args.get('hashToken')
		userToken=models.User.query.get(userId).md5token
		if (hashToken!=userToken):
			return "Error: Access Denied"
		randomTask()
		returndict={'items':[]}
		for task in models.Task.query.filter(models.Task.user == userId).all():
			returndict['items'].append(createTaskJSON(task))		
		return jsonify(returndict)
	except:
		print str(traceback.format_exception(*sys.exc_info()))
		return str(traceback.format_exception(*sys.exc_info()))

@app.route('/api/user/<int:userId>/leaderboard', methods = ['GET'])
def getLeaders(userId):
	try:
		hashToken=request.args.get('hashToken')
		userToken=models.User.query.get(userId).md5token
		if (hashToken!=userToken):
			return "Error: Access Denied"
		returndict={'users':[]}
		listoffriends=[]
		listoffriends.append(userId)
		friendtable=models.User.query.get(userId).friends
		for f in friendtable:
			listoffriends.append(f.friendid)
		listoffriends.remove(0)
		for u in models.User.query.filter(models.User.id.in_(listoffriends)).order_by(models.User.points.desc()).limit(10).all():
			returndict['users'].append({'id' : u.id, 'score' : u.points,'name' : u.name, 'fbid': u.fbid, 'picture': u.profilepic})		
		return jsonify(returndict)
	except:
		print str(traceback.format_exception(*sys.exc_info()))
		return str(traceback.format_exception(*sys.exc_info()))

@app.route('/api/user/<int:userId>/hidesuggestion', methods = ['POST'])
def hideTask(userId):
	try:
		hashToken=request.get_json().get('hashToken')
		taskId = request.get_json().get('taskId')
		userToken=models.User.query.get(userId).md5token
		if (hashToken!=userToken):
			return "Error: Access Denied"
		task = models.Task.query.get(taskId)
		if (task.user != 0):
			return jsonify(success=False)
		hidden = models.HiddenTasks(userid=userId, taskid=taskId)
		db.session.add(hidden)
		db.session.commit()
		return jsonify(success=True)
	except:
		print str(traceback.format_exception(*sys.exc_info()))
		return str(traceback.format_exception(*sys.exc_info()))


@app.route('/api/user/<int:userId>/deletetasks', methods = ['POST'])
def deleteTask(userId):
	try:
		hashToken=request.get_json().get('hashToken')
		taskId=request.get_json().get('taskId');
		userToken=models.User.query.get(userId).md5token
		if (hashToken!=userToken):
			return "Access Denied"
		if taskId is None:
			return jsonify(success=False)
		taskToDelete=models.Task.query.get(taskId)
		if taskToDelete != None:
			db.session.delete(taskToDelete)
			db.session.commit()
			return jsonify(success=True)
		else:
			return jsonify(success=False)
	except:
		print str(traceback.format_exception(*sys.exc_info()))
		return str(traceback.format_exception(*sys.exc_info()))

@app.route('/api/user/<int:userId>/updatetask', methods = ['POST'])
def updateTask(userId):
	try:
		hashToken=request.get_json().get('hashToken')
		user=models.User.query.get(userId)
		userToken=user.md5token
		if (hashToken!=userToken):
			return "Error: Access Denied"
		taskid=request.get_json().get('id',None)
		task=models.Task.query.get(taskid)
		if (task.user!=userId):
			return "Error: Access Denied"
		randomTask()
		name=request.get_json().get('name',None)
		pictureurl=request.get_json().get('pictureurl',None)
		hashtag=request.get_json().get('hashtag',None)
		private=request.get_json().get('private',None)
		completed=request.get_json().get('completed',None)
		description=request.get_json().get('description', None)
		if (name!=None):
			task.name=name
		if (description!=None):
			task.description=description
		if (pictureurl!=None):
			task.pictureurl=pictureurl
		if (hashtag!=None):
			task.hashtag=hashtag
		if (private!=None):
			task.private=private
		if (completed==0):
			if (task.completed == 1):
				user.points = user.points - 1
			task.completed=completed
			task.timecompleted=None
		elif (completed==1):
			if (task.completed == 0):
				user.points = user.points + 1
				task.completed = completed
				task.timecompleted = datetime.datetime.utcnow()
		db.session.commit()
		return jsonify(createTaskJSON(task))
	except:
		print str(traceback.format_exception(*sys.exc_info()))
		return str(traceback.format_exception(*sys.exc_info()))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def md5sum(file):
    with file as f:
        d = hashlib.md5()
        for buf in iter(partial(f.read, 128), b''):
            d.update(buf)
    return d.hexdigest()

@app.route('/api/user/<int:userId>/photoupload', methods = ['POST'])
def photoupload(userId):
	try:
		hashToken=request.form.get('hashToken')
		userToken=models.User.query.get(userId).md5token
		if (hashToken!=userToken):
			return "Error: Access Denied"
		file = request.files['photo']
		conn = boto.connect_s3(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
		bucket = conn.get_bucket('lifemax')
		k = Key(bucket)
		k.key =  hashlib.sha224(file.read()).hexdigest() + '.jpg'
		file.seek(0)
		k.set_contents_from_string(file.read())
		k.make_public()
		url = k.generate_url(expires_in=0, query_auth=False)
		print url
		return jsonify(imageurl=url, success=True)
	except:
		print str(traceback.format_exception(*sys.exc_info()))
		return str(traceback.format_exception(*sys.exc_info()))



