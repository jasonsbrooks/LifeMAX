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
FACEBOOK_CLIENT_ID='670660326330598'
FACEBOOK_CLIENT_SECRET='0ec602b31b2220aaafc41043b699abcf'
GOOGLE_CLIENT_ID='XXXXXX'
GOOGLE_CLIENT_SECRET='XXXXXXXXX'
true=True
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
		print shortToken
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
		return str(traceback.format_exception(*sys.exc_info()))


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
		return str(traceback.format_exception(*sys.exc_info()))

@app.route('/api/user/<int:userid>/newsfeed', methods = ['GET'])
def newsfeed(userid):
	try:
		hashToken=request.args.get('hashToken',None)
		userToken=models.User.query.get(userid).md5token
		if (hashToken!=userToken):
			return "Error: Access Denied"
		returndict={'posts':[]}
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
		if (hashtag == None and friendId == None):
			for task in models.Task.query.filter_by(completion=True).order_by(desc(models.Task.timecompleted)).filter(models.Task.user.in_(listoffriends)).limit(maxResults).all():
				friendname=task.user.name
				friendpic=task.user.profilepic
				returndict['items'].append({'user':friendname,'profilepic':friendpic,'name':task.name, 'description':task.description,'location':task.location, 'pictureurl':task.pictureurl, 'completion':task.completion})		
			return jsonify(returndict)
		elif (hashtag != None and friendId == None):
			for task in models.Task.query.filter_by(completion=True).order_by(desc(models.Task.timecompleted)).filter(models.Task.user.in_(listoffriends)).filter_by(hashtag=hashtag).limit(maxResults).all():
				friendname=task.user.name
				friendpic=task.user.profilepic
				returndict['items'].append({'user':friendname,'profilepic':friendpic,'name':task.name, 'description':task.description,'location':task.location, 'pictureurl':task.pictureurl, 'completion':task.completion})
			return jsonify(returndict)
		elif (hashtag == None and friendId != None):
			if ((models.User.query.get(friendId) not in models.User.get(userid).friends) or models.User.query.get(friendId).privacy==1):
				return "Error: Access Denied"
			for task in models.Task.query.filter_by(completion=True).order_by(desc(models.Task.timecompleted)).filter_by(user=friendId).limit(maxResults).all():
				friendname=task.user.name
				friendpic=task.user.profilepic
				returndict['items'].append({'user':friendname,'profilepic':friendpic,'name':task.name, 'description':task.description,'location':task.location, 'pictureurl':task.pictureurl, 'completion':task.completion})
			return jsonify(returndict)
		elif (hashtag != None and friendId != None):
			if ((models.User.query.get(friendId) not in models.User.get(userid).friends) or models.User.query.get(friendId).privacy==1):
				return "Error: Access Denied"
			for task in models.Task.query.filter_by(completion=True).order_by(desc(models.Task.timecompleted)).filter_by(user=friendId).filter_by(hashtag=hashtag).limit(maxResults).all():
				friendname=task.user.name
				friendpic=task.user.profilepic
				returndict['items'].append({'user':friendname,'profilepic':friendpic,'name':task.name, 'description':task.description,'location':task.location, 'pictureurl':task.pictureurl, 'completion':task.completion})
			return jsonify(returndict)

	except:
		return str(traceback.format_exception(*sys.exc_info()))
"""

@app.route('/api/user/<int:userid>/gcallist', methods=['GET'])
def gcallist(userid):
	try:

		hashToken=request.args.get('hashToken')
		user=models.User.query.get(userId)
		userToken=user.md5token
		if (hashToken!=userToken):
			return "Error: Access Denied"
		if (user.gtoken == None):
			return "No google account"
		service=gconnect(user)
		calendars=service.calendarList().list(fields='items',showHidden=True).execute()
		return jsonify(calendar['items'])
	except:
		return str(traceback.format_exception(*sys.exc_info()))

@app.route('/api/user/<int:userid>/gcalevents', methods=['GET'])
def gcalevents(userid):
	try:
		hashToken=request.args.get('hashToken')
		calId=request.args.get('calendarId')
		user=models.User.query.get(userId)
		userToken=user.md5token
		if (hashToken!=userToken):
			return "Error: Access Denied"
		if (user.gtoken == None):
			return "No google account"
		maxEvents=int(request.get('maxEvents',None))
		starttime=request.get('start', None)
		endtime=request.get('end', None)
		service=gconnect(user)

		events=service.events().list(calendarId=calId,maxEvents=maxResults,orderBy='startTime',singleEvents=True,timeMax=endtime,timeMin=starttime).execute()
		return Response(json.dumps(events),  mimetype='application/json')
	except:
		return str(traceback.format_exception(*sys.exc_info()))

@app.route('/api/user/<int:userid>/gcalevents', methods=['POST'])
def gcalimport(userid):
	try:
		#hashToken=request.form.get('hashToken')
		#calId=request.form.get('calendarId')
		#listofids=ast.literal_eval(request.form.get('listOfIds'))
		hashToken=request.get_json()['hashToken']
		calId=request.get_json()['calendarId']
		listofids=request.get_json()['listOfIds']
		pictureurl="test"
		user=models.User.query.get(userId)
		userToken=user.md5token
		if (hashToken!=userToken):
			return "Error: Access Denied"
		if (user.gtoken == None):
			return "No google account"
		service=gconnect(user)
		service2=gconnect(models.LifeMaxIds.query.first())
		
		listofevents={'events':[]}
		for i in listofids:
			event=service.events().get(calendarId=calId,eventId=i).execute()
			event['extendedProperties']={'shared':{'hashtag':hashtag,'pictureurl':pictureurl}}
			events.append(event)
			service2.events().import_(calendarId=user.gidcalendar,body=event).execute(http=http2)
		return jsonify(events)
	except:
		return str(traceback.format_exception(*sys.exc_info()))

@app.route('/api/user/<int:userid>/gcalpush', methods=['POST'])
def gcalpush(userid):
	try:
		#hashToken=request.form.get('hashToken')
		#calId=request.form.get('calendarId')
		hashToken=request.get_json()['hashToken']
		calId=request.get_json()['calendarId']
		user=models.User.query.get(userId)
		userToken=user.md5token
		if (hashToken!=userToken):
			return "Error: Access Denied"
		if (user.gtoken == None):
			return "No google account"
		service=gconnect(user)
		service2=gconnect(models.LifeMaxIds.query.first())
		events=service2.events().list(calendarId=user.gidcalendar).execute(http=http2)
		for i in events:
			service.events().insert(calendarId=calId,body=i).execute()
		return jsonify(events)
	except:
		return str(traceback.format_exception(*sys.exc_info()))

@app.route('/api/googlelogin', methods=['GET'])
def glogin():
	try:
		code=request.args.get('code')
		state=request.args.get('hashToken')
		user=models.User.query.filter_by(md5token=md5token).first()
		params={'code':code,'client_id':GOOGLE_CLIENT_ID,'client_secret':GOOGLE_CLIENT_SECRET,'redirect_uri':'https://lifemax-staging.herokuapp.com/oauth2callback','grant_type':'authorization_code'}
		r=requests.post('https://accounts.google.com/o/oauth2/token',data=params)
		gtoken=r.json()['access_token']
		grtoken=r.json()['refresh_token']
		user.gtoken=gtoken
		user.grtoken=grtoken
		user.lastupdatedtoken=int(time.time())
		db.session.commit()
		
		service=gconnect(gtoken)
		calendars=service.calendarList().list(fields='items',showHidden=True).execute()
		summaries=[i['summary'] for i in calendars['items']]
		if 'LifeMaxCalendar' not in summaries:
			body={'summary': 'LifeMaxCalendar'}
			createdcalendar=service.calendars().insert(body=body).execute()
			user.gidcalendar=createdcalendar['id']
			service.calendarList().insert(body={'id':createdcalendar['id'],'hidden':True}).execute()
			db.session.commit()
		
		return jsonify(success=True)
	except:
		return str(traceback.format_exception(*sys.exc_info()))

def gconnect(user):
	try:
		if ((int(time.time())-user.lastupdatedtoken)>2500):
			params={'client_id':GOOGLE_CLIENT_ID,'client_secret':GOOGLE_CLIENT_SECRET,'refresh_token':user.grtoken,'grant_type':'refresh_token'}
			r=requests.post('https://accounts.google.com/o/oauth2/token',data=params)
			user.gtoken=r.json()['access_token']
			user.lastupdatedtoken=int(time.time())
		credentials = client.AccessTokenCredentials(user.gtoken, 'my-user-agent/1.0')
		http = httplib2.Http()
	  	http = credentials.authorize(http)
		service = build('calendar', 'v3',http=http)
		return service
	except:
		return str(traceback.format_exception(*sys.exc_info()))
"""
@app.route('/api/user/<int:userId>/tasks', methods = ['POST'])
def addTimelessTask2(userId):
	try:
		hashToken=request.get_json().get('hashToken')
		userToken=models.User.query.get(userId).md5token
		if (hashToken!=userToken):
			return "Error: Access Denied"
		name=request.get_json().get('name')
		description=request.get_json().get('description')
		location=request.get_json().get('location')
		pictureurl=request.get_json().get('pictureurl')
		hashtag=request.get_json().get('hashtag')
		newTask=models.Task(user=userId, name=name, description=description, hashtag=hashtag, location=location, pictureurl=pictureurl, completion=False)
		db.session.add(newTask)
		db.session.commit()
		return jsonify(success=True,taskID=newTask.id)
	except:
		return str(traceback.format_exception(*sys.exc_info()))
"""
def addTask(userId):
	try:
		#hashToken=request.form.get('hashToken')
		hashToken=request.get_json()['hashToken']
		user=models.User.query.get(userId)
		userToken=user.md5token
		if (hashToken!=userToken):
			return "Error: Access Denied"
		name=request.get_json().get('name')
		description=request.get_json().get('description')
		location=request.get_json().get('location')
		starttime=request.get_json().get('starttime')
		endtime=request.get_json().get('endtime')
		pictureurl=request.get_json().get('pictureurl')
		hashtag=request.get_json().get('hashtag')
		recurrence=request.get_json().get('recurrence')
		startdate=request.get_json().get('startdate')
		enddate=request.get_json().get('enddate')
		if (starttime == None and endtime == None):

			if (recurrence==None):
				event = {'summary':name,'description':description, 'start':{'date':startdate},'end':{'date':endtime},
				'location':location, 'extendedProperties':{'shared':{'hashtag':hashtag,'pictureurl':pictureurl}} }
			else:
				event = {'summary':name,'description':description, 'start':{'date':starttime},'end':{'date':endtime},
				'location':location, 'extendedProperties':{'shared':{'hashtag':hashtag,'pictureurl':pictureurl}}, 'recurrence':recurrence }
		else:
			if (recurrence==None):
				event = {'summary':name,'description':description, 'start':{'dateTime':starttime},'end':{'dateTime':endtime},
				'location':location, 'extendedProperties':{'shared':{'hashtag':hashtag,'pictureurl':pictureurl}} }
			else:
				event = {'summary':name,'description':description, 'start':{'dateTime':starttime},'end':{'dateTime':endtime},
				'location':location, 'extendedProperties':{'shared':{'hashtag':hashtag,'pictureurl':pictureurl}}, 'recurrence':recurrence }
			service=gconnect(models.LifeMaxIds.query.first())
		
		newtask=service.events().insert(calendarId=user.gidcalendar, body=event).execute()
		return jsonify(newtask)
	except:
		return str(traceback.format_exception(*sys.exc_info()))"""
@app.route('/api/user/<int:userId>/tasks', methods = ['GET'])
def getTimelessTasks2(userId):
	try:
		hashToken=request.args.get('hashToken')
		userToken=models.User.query.get(userId).md5token
		if (hashToken!=userToken):
			return "Error: Access Denied"
		returndict={'items':[]}
		for task in models.Task.query.filter(Task.user == userID).all():
			returndict['items'].append({'id':task.id,'hashtag':task.hashtag,'user':userID,'name':task.name,'description':task.description,'location':task.location,
				'pictureurl':task.pictureurl, 'completion':task.completion})
		
		return jsonify(returndict)
	except:
		return str(traceback.format_exception(*sys.exc_info()))
"""
def getTasks(userId):
	try:
		hashToken=request.args.get('hashToken')
		user=models.User.query.get(userId)
		try:
			userToken=user.md5token
		except:
			return "Error: User does not exist"
		if (hashToken!=userToken):
			return "Error: Access Denied"
		maxEvents=request.args.get('maxEvents',None)
		if (maxEvents!=None):
			maxEvents=int(maxEvents)
		starttime=request.args.get('start', None)
		endtime=request.args.get('end', None)
		hashtag=request.args.get('hashtag', None)
		service=gconnect(models.LifeMaxIds.query.first())
		
		events=service.events().list(calendarId=user.gidcalendar,maxResults=maxEvents,orderBy='startTime',singleEvents=True,timeMax=endtime,timeMin=starttime,sharedExtendedProperty=hashtag).execute()
		return Response(json.dumps(events['items']), mimetype='application/json')
	except:
		return str(traceback.format_exception(*sys.exc_info()))
"""
@app.route('/api/user/<int:userId>/deletetasks', methods = ['POST'])
def deleteTask(userId):
	try:
		hashToken=request.get_json().get('hashToken')
		taskId=request.get_json().get('taskId');
		userToken=models.User.query.get(userId).md5token
		if (hashToken!=userToken):
			return "Access Denied"
		if (models.TaskList.query.get(tasklistid).user!=userId):
			return "Access Denied"
		if (models.Task.query.get(taskid).tasklist!=tasklistid):
			return jsonify(success=False)
		taskToDelete=models.Task.query.get(taskid)
		db.session.delete(taskToDelete)
		db.session.commit()
		return jsonify(success=True)
	except:
		return str(traceback.format_exception(*sys.exc_info()))
"""	try:
		hashToken=request.get_json().get('hashToken')
		user=models.User.query.get(userId)
		userToken=user.md5token
		if (hashToken!=userToken):
			return "Error: Access Denied"
		eventId=request.get_json().get('eventId')
		service=gconnect(models.LifeMaxIds.query.first())

		deletedevent=service.events().delete(calendarId=user.gidcalendar,eventId=eventId).execute()
		delchars = ''.join(c for c in map(chr, range(256)) if not c.isalnum())
		if deletedevent.translate(None,delchars) == '':
			return "Success"
	except:
		return str(traceback.format_exception(*sys.exc_info()))
"""
"""
#@app.route('/api/user/<int:userId>/timelesstasks', methods = ['POST'])
def addTimelessTask(userId):
	try:
		hashToken=request.get_json().get('hashToken')
		userToken=models.User.query.get(userId).md5token
		if (hashToken!=userToken):
			return "Error: Access Denied"
		name=request.get_json().get('name')
		description=request.get_json().get('description')
		location=request.get_json().get('location')
		photo=request.get_json().get('pictureurl')
		newTask=models.Task(user=userId, name=name, tasklist=tasklistid, description=description, location=location, starttime=int(starttime), endtime=int(endtime), photo=photo, completion=False)
		db.session.add(newTask)
		db.session.commit()

		return jsonify(success=True,taskID=newTask.id)
	except:
		return str(traceback.format_exception(*sys.exc_info()))
"""
@app.route('/api/user/<int:userId>/updatetask', methods = ['POST'])
def updateTask(userId):
	try:
		hashToken=request.args.get('hashToken',None)
		user=models.User.query.get(userId)
		userToken=user.md5token
		if (hashToken!=userToken):
			return "Error: Access Denied"
		taskid=request.get_json().get('taskId',None)
		task=models.Task.query.get(taskid)
		if (task.user.id!=userId):
			return "Error: Access Denied"
		name=request.get_json().get('name',None)
		description=request.get_json().get('description',None)
		location=request.get_json().get('location',None)
		pictureurl=request.get_json().get('pictureurl',None)
		hashtag=request.get_json().get('hashtag',None)
		completion=request.get_json().get('completion',None)
		if (name!=None):
			task.name=name
		if (description!=None):
			task.description=description
		if (location!=None):
			task.location=location
		if (pictureurl!=None):
			task.pictureurl=pictureurl
		if (hashtag!=None):
			task.hashtag=hashtag
		if (completion=='True'):
			task.completion=True
			task.timecompleted=int(time.time())
		elif (completion=='False'):
			task.completion=False
			task.timecompleted=None
		db.session.commit()
		return jsonify(name=task.name,description=task.description,location=task.location,pictureurl=task.pictureurl,hashtag=task.hashtag,completion=task.completion)
	except:
		return str(traceback.format_exception(*sys.exc_info()))

"""
@app.route('/api/user/<int:userId>/completetask', methods=['POST'])
def completeTask(userId):
	try:
		hashToken=request.args.get('hashToken')
		user=models.User.query.get(userId)
		userToken=user.md5token
		if (hashToken!=userToken):
			return "Error: Access Denied"
		taskid=request.get_json().get('taskid')
		task=models.Task.query.get(taskid)
		if (task.user.id!=userId)
			return "Error: Access Denied"
		task.timecompleted=int(time.time())
		db.session.commit()
		ct=CompletedTask(user=userId,task=taskid)
		db.session.add(ct)
		db.session.commit()
	except:
		return str(traceback.format_exception(*sys.exc_info()))
		"""
"""
"""
#@app.route('/api/user/<int:userId>/timelesstasks', methods = ['GET'])
"""
def getTimelessTasks(userId):
	try:
		hashToken=request.args.get('hashToken')
		userToken=models.User.query.get(userId).md5token
		if (hashToken!=userToken):
			return "Error: Access Denied"
		returndict={'items':[]}
		for task in models.Task.query.all():
			returndict['items'].append({'name':task.name,'description':task.description,'location':task.location,
				'pictureurl':task.pictureurl, 'completion':task.completion})
		
		return jsonify(returndict)
	except:
		return str(traceback.format_exception(*sys.exc_info()))

@app.route('/api/user/<int:userId>/deletetimelesstasks', methods = ['POST'])
def deleteTimelessTask(userId):
	try:
		hashToken=request.get_json().get('hashToken')
		taskId=request.get_json().get('taskId');
		userToken=models.User.query.get(userId).md5token
		if (hashToken!=userToken):
			return jsonify(success=False)
		if (models.TaskList.query.get(tasklistid).user!=userId):
			return jsonify(success=False)
		if (models.Task.query.get(taskid).tasklist!=tasklistid):
			return jsonify(success=False)
		taskToDelete=models.Task.query.get(taskid)
		db.session.delete(taskToDelete)
		db.session.commit()
		return jsonify(success=True)
	except:
		return str(traceback.format_exception(*sys.exc_info()))
"""
@app.route('/caslogin', methods = ['GET'])
def caslogin():
	if request.args.get('ticket')==None:
		return redirect("https://secure.its.yale.edu/cas/login?service=http://localhost:5000/caslogin")
	r=requests.get('https://secure.its.yale.edu/cas/serviceValidate?service=http://localhost:5000/caslogin&ticket='+request.args.get('ticket'))
	f=r.text.find('<cas:user>')
	if (f==-1):
		return 'Login failed!'
	return r.text[f+10:r.text.find('<',f+1)]

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def md5sum(file):
    with file as f:
        d = hashlib.md5()
        for buf in iter(partial(f.read, 128), b''):
            d.update(buf)
    return d.hexdigest()

@app.route('/api/user/<int:userid>/photoupload', methods = ['POST'])
def photoupload(userid):
	hashToken=request.form.get('hashToken')
	userToken=models.User.query.get(userId).md5token
	if (hashToken!=userToken):
		return "Error: Access Denied"
	file = request.files['file']
	sum=md5sum(file)
	if file and allowed_file(sum):
		filename = secure_filename(sum)
		file.save(os.path.join('/photos/', filename))
        models.User.query.get(userId).pictureurl=filename
        db.session.commit()
        return filename
	return False
