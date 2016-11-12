#app.py 
from flask import Flask, render_template, session, redirect, url_for, request 
from flask_bootstrap import Bootstrap
from flask.ext.wtf import Form 
from wtforms import StringField, SubmitField, RadioField
from wtforms.validators import Required
import string
import random

from models import User, Session, Poll
from database import db_session, db
"""
APP SETTINGS
"""
app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.from_object("config.Config")
app.config['SECRET_KEY'] = 'hard'
bootstrap = Bootstrap(app)
db.init_app(app)

"""
SESSION CREATION
"""

new_url = False
poll_url = "localhost:5000/"
def addon():
    result = ""
    for _ in range(5):
        choose = random.randint(0,1)
        if choose:
            result += str(random.randint(1,9))
        else:
            result += random.choice(string.letters)
    return result

class SearchForm(Form):
    searchterm = StringField('Where do you want to eat?', validators=[Required()])
    submit = SubmitField('Submit')

@app.route("/", methods=['GET', 'POST'])
def search():
    form = SearchForm()
    if form.validate_on_submit():
        session['searchterm'] = form.searchterm.data 
        new_url = True
        return render_template('index.html',form=form,searchterm=session.get('searchterm'),new_url = new_url,poll_url = poll_url+addon())
    return render_template('index.html', form=form, searchterm=session.get('searchterm'))

"""
POLL VIEWS
"""

class PollForm(Form):
    price = RadioField(label="price", description="Price", choices=[('$', '$'), ('$$', '$$'), ('$$$', '$$$')])
    keywords = RadioField("Type", choices=[('As', 'Asian'), ('Am', 'American'), ('Eu', 'European'), ('Af', 'African')])
    keyterms = StringField("Keyterms")
    submit = SubmitField('Submit')

@app.route("/user/<unique_id>", methods=['GET', 'POST'])
def poll(unique_id):
    form = PollForm()
    if form.validate_on_submit():
	return render_template('thanks.html')
    return render_template('poll.html', form=form)

"""
LOGIN VIEWS
"""

@app.route("/login/<user>")
def login(user):
    user_item = db_session.query(User).filer_by(name=user).first()
    if user_item:
    	session['user'] = user_item
	return render_template('login.html', user=user, result=True)
    else:
	return render_template('login.html', user=user, result=False)
    


"""
MAIN APP
"""
if __name__ == "__main__":
    app.run(debug=True)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

