import requests
from app import app,db,models
from flask import request,jsonify,redirect,Response
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

FACEBOOK_CLIENT_ID='670660326330598'
FACEBOOK_CLIENT_SECRET='0ec602b31b2220aaafc41043b699abcf'
GOOGLE_CLIENT_ID='XXXXXX'
GOOGLE_CLIENT_SECRET='XXXXXXXXX'
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
true=True

class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        else:
            return str(obj)
        return json.JSONEncoder.default(self, obj)

def createTaskJSON(task):
	u = models.User.query.get(task.user)
	userJSON = {'id' : u.id, 'name' : u.name, 'fbid': u.fbid}
	if task.timecompleted is None:
		tc = None
	else:
		tmp_time = task.timecompleted
		tmp_time.replace(second=0, microsecond=0)
		tc = json.dumps(tmp_time, cls=DateEncoder)
	completeJSON = {'id':task.id, 'user':userJSON, 'name': task.name, 'hashtag': task.hashtag, 'pictureurl': task.pictureurl, 'private': task.private, 'completed': task.completed, 'timecompleted': tc}
	return completeJSON

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
					newfriend1=models.Friends(userId=user.id,friendid=friend.id)
					newfriend2=models.Friends(userId=friend.id,friendid=user.id)
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

@app.route('/api/hashtags', methods = ['GET'])
def gethashtags():
	listofhashtags = ['#day2dayhappiness', '#newhavenbars', '#yalebucketlist', '#yalehookups', '#fitness', '#yalesports', '#newhavenoutdoors', '#entertainment', '#yaleculture']
	return jsonify(hashtags=listofhashtags)

@app.route('/api/imageforhashtag', methods=['GET'])
def imageforhashtag():
	hashtag = request.args.get('hashtag')
	imageDict = {'#day2dayhappiness':'http://lorempixel.com/400/200/sports/1', '#newhavenbars':'http://lorempixel.com/400/200/sports/1', '#yalebucketlist':'http://lorempixel.com/400/200/sports/1', '#yalehookups':'http://lorempixel.com/400/200/sports/1', '#fitness':'http://lorempixel.com/400/200/sports/1', '#yalesports':'http://lorempixel.com/400/200/sports/1', '#newhavenoutdoors':'http://lorempixel.com/400/200/sports/1', '#entertainment':'http://lorempixel.com/400/200/sports/1', '#yaleculture':'http://lorempixel.com/400/200/sports/1'}
	response = {'imageurl' : imageDict[hashtag], 'hashtag' : hashtag}
	return jsonify(response)

@app.route('/api/login', methods = ['GET'])
def login():
	try:
		shortToken=request.args.get('userToken')

		r=requests.get('https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id='+FACEBOOK_CLIENT_ID+'&client_secret='+FACEBOOK_CLIENT_SECRET+'&fb_exchange_token='+shortToken)
		longToken=parse_qs(r.text)['access_token'][0]
		md5token=hashlib.md5(longToken).hexdigest()
		r=requests.get('https://graph.facebook.com/me?access_token='+longToken)
		lookupid=r.json()['id']
		loginuser=models.User.query.filter_by(fbid=lookupid).first()
		if loginuser==None:
			return "Error: User does not exist!"
		db.session.query(models.User).filter(models.User.fbid==lookupid).update({"token":longToken,"md5token":md5token})
		db.session.commit()
		return jsonify(authToken=longToken,fbid=lookupid, id=loginuser.id)
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
		returndict={'items':[]}
		maxResults=request.args.get('maxResults',None)
		if (maxResults==None):
			maxResults=50
		friendId=request.args.get('friendId',None)
		hashtag=request.args.get('hashtag',None)
		listoffriends=[]
		listoffriends.append(userid)
		friendtable=models.User.query.get(userid).friends
		for f in friendtable:
			if (models.User.query.get(f.friendid).privacy==0):
				listoffriends.append(f.friendid)
		if (hashtag == None and friendId == None):
			# for task in models.Task.query.filter_by(completion=True).order_by(desc(models.Task.timecompleted)).filter(models.Task.user.in_(listoffriends)).limit(maxResults).all():
			for task in models.Task.query.order_by(desc(models.Task.timecompleted)).filter(models.Task.user.in_(listoffriends)).limit(maxResults).all():
				returndict['items'].append(createTaskJSON(task))		
			return jsonify(returndict)
		elif (hashtag != None and friendId == None):
			for task in models.Task.query.filter_by(completed=True).order_by(desc(models.Task.timecompleted)).filter(models.Task.user.in_(listoffriends)).filter_by(hashtag=hashtag).limit(maxResults).all():
				returndict['items'].append(createTaskJSON(task))
			return jsonify(returndict)
		elif (hashtag == None and friendId != None):
			if ((models.User.query.get(friendId) not in models.User.get(userid).friends) or models.User.query.get(friendId).privacy==1):
				return "Error: Access Denied"
			for task in models.Task.query.filter_by(completed=True).order_by(desc(models.Task.timecompleted)).filter_by(user=friendId).limit(maxResults).all():
				returndict['items'].append(createTaskJSON(task))
			return jsonify(returndict)
		elif (hashtag != None and friendId != None):
			if ((models.User.query.get(friendId) not in models.User.get(userid).friends) or models.User.query.get(friendId).privacy==1):
				return "Error: Access Denied"
			for task in models.Task.query.filter_by(completed=True).order_by(desc(models.Task.timecompleted)).filter_by(user=friendId).filter_by(hashtag=hashtag).limit(maxResults).all():
				returndict['items'].append(createTaskJSON(task))
			return jsonify(returndict)

	except:
		print str(traceback.format_exception(*sys.exc_info()))
		return str(traceback.format_exception(*sys.exc_info()))

@app.route('/api/user/<int:userId>/tasks', methods = ['POST'])
def addTimelessTask2(userId):
	try:
		hashToken=request.get_json().get('hashToken')
		userToken=models.User.query.get(userId).md5token
		if (hashToken!=userToken):
			return "Error: Access Denied"
		name=request.get_json().get('name')
		pictureurl=request.get_json().get('pictureurl', None)
		hashtag=request.get_json().get('hashtag')
		private=request.get_json().get('private')
		newTask=models.Task(user=userId, name=name, hashtag=hashtag, pictureurl=pictureurl, private=private)
		db.session.add(newTask)
		db.session.commit()
		return jsonify(createTaskJSON(newTask))
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
		returndict={'items':[]}
		for task in models.Task.query.filter(models.Task.user == userId).all():
			returndict['items'].append(createTaskJSON(task))		
		return jsonify(returndict)
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
			return "HASH TOKEN Error: Access Denied"
		taskid=request.get_json().get('id',None)
		task=models.Task.query.get(taskid)
		if (task.user!=userId):
			return "TASK MATCH Error: Access Denied. Task User: %d, User ID: %d" %(task.user, userID)
		name=request.get_json().get('name',None)
		pictureurl=request.get_json().get('pictureurl',None)
		hashtag=request.get_json().get('hashtag',None)
		private=request.get_json().get('private',None)
		completed=request.get_json().get('completed',None)
		if (name!=None):
			task.name=name
		if (pictureurl!=None):
			task.pictureurl=pictureurl
		if (hashtag!=None):
			task.hashtag=hashtag
		if (private!=None):
			task.private=private
		if (completed==0):
			task.completed=completed
			task.timecompleted=None
		elif (completed==1):
			if (task.completed == 0):
				task.completed = completed
				task.timecompleted = datetime.datetime.now()
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



