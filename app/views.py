from flask import request, render_template, redirect, url_for, session
from app import app, models, db
from app.models import *
from flask_oauth import OAuth


DEBUG = True
FACEBOOK_APP_ID = '188477911223606'
FACEBOOK_APP_SECRET = '621413ddea2bcc5b2e83d42fc40495de'

oauth = OAuth()

facebook = oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=FACEBOOK_APP_ID,
    consumer_secret=FACEBOOK_APP_SECRET,
    request_token_params={'scope': 'email'}
)

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html',
        title = 'Sup')

@app.route('/lists')
def lists():
    try:
        user = getuser(session['md5token'])
    except KeyError:
        return "access denied"

    tls = user.tasklists
    return render_template('lists.html', title = 'Your Lists', tasklists = tls)

@app.route('/lists/tasklists/new', methods=['POST'])
def createList():
    requestDict = request.values
    requestDict = dict(zip(requestDict, map(lambda x: requestDict.get(x), requestDict)))
    tl = TaskList(user=getuser(session['md5token']).id, name=requestDict['listname'])
    db.session.add(tl)
    db.session.commit()
    return redirect(url_for("lists"))

@app.route('/lists/tasks/new', methods=['POST'])
def createTask():
    requestDict = request.values
    requestDict = dict(zip(requestDict, map(lambda x: requestDict.get(x), requestDict)))
    t = Task(user=getuser(session['md5token']).id, name=requestDict['listname'], tasklist = requestDict['tl'], description = "penis", location = "dumb", starttime=requestDict['starttime'], endtime=requestDict['endtime'], photo="www.google.com",completion=False)
    db.session.add(t)
    db.session.commit()
    return redirect(url_for("lists"))

@app.route('/feed')
def feed():
    return render_template('feed.html', title = 'Your Feed')   

@app.route('/login', methods = ['POST'])
def firstlogin():
    return facebook.authorize(callback=url_for('facebook_authorized',
        next=request.args.get('next') or request.referrer or None,
        _external=True))

@app.route('/login/authorized')
@facebook.authorized_handler
def facebook_authorized(resp):
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    session['oauth_token'] = (resp['access_token'], '')
    me = facebook.get('/me')
    user=checkIfUserExists(me.data['id'])
    uID = user.id
    if not uID:
        user = User(fbid=me.data['id'])
        db.session.add(user)
        db.session.commit()
    
    if user:
        session['md5token']= user.md5token
        return redirect(url_for("lists"))


@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')


def checkIfUserExists(fbid):
    if User.query.filter(User.fbid == fbid).first() != None:
        return User.query.filter(User.fbid == fbid).first()
    return False

def getuser(hashToken):
    return User.query.filter(User.md5token == hashToken).first()

# if getuser(session['token'])==None:
    # return "Access Denied!"



