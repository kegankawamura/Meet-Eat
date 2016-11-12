#app.py 
from flask import Flask, render_template, session, redirect, url_for, request 
from flask.ext.wtf import Form 
from wtforms import StringField, SubmitField, RadioField
from flask.ext.bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy
from wtforms.validators import Required
from database import db_session
import string
import random
import ipdb

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.from_object("config.Config")
db = SQLAlchemy(app)

app.config['SECRET_KEY'] = 'hard to guess'
new_url = False

def addon():
    result = ""
    for _ in range(5):
        choose = random.randint(0,1)
        if choose:
            result += str(random.randint(1,9))
        else:
            result += random.choice(string.letters)
    return result
poll_url = "localhost:5000/"
bootstrap = Bootstrap(app)

class PollForm(Form):
    price = RadioField(label="price", description="Price", choices=[('$', '$'), ('$$', '$$'), ('$$$', '$$$')])
    keywords = RadioField("Type", choices=[('As', 'Asian'), ('Am', 'American'), ('Eu', 'European'), ('Af', 'African')])
    keyterms = StringField("Keyterms")
    submit = SubmitField('Submit')

@app.teardown_appcontext
def shutdown_session(exception=None):
  db_session.remove()

@app.route("/user/<unique_id>", methods=['GET', 'POST'])
def poll(unique_id):
    form = PollForm()
    if form.validate_on_submit():
	return render_template('thanks.html')
    return render_template('poll.html', form=form)

@app.route("/login/<user>")
def login(user):
    user_item = db_session.query(User).filer_by(name=user).first()
    if user_item:
    	session['user'] = user_item
	return render_template('login.html', user=user, result=True)
    else:
	return render_template('login.html', user=user, result=False)
    

@app.route("/resume")
def hello():
    return render_template('index.html')

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


if __name__ == "__main__":
    app.run(debug=True)
