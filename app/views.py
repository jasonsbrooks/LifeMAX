
from flask import request,render_template
from app import app

@app.route('/')
@app.route('/index')
def index():
    return "Welcome!"

@app.route('/about')
def about():
	return render_template('about.html')