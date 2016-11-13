#app.py 
from flask import Flask, render_template, session, redirect, url_for, request 
from flask_bootstrap import Bootstrap
from flask.ext.wtf import Form
from wtforms import widgets, StringField, SubmitField, RadioField, IntegerField, SelectMultipleField
from wtforms.validators import Required
import string
import random

from models import User, Session, Poll
from database import db_session, db
import googlemaps
from datetime import datetime
from tokens import ServerKey

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
new_address = False
error = False
location,address = 0,""
gmaps = googlemaps.Client(key=ServerKey)


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

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

class CloseForm(Form):
    close = SubmitField('Close Poll')

@app.route("/", methods=['GET', 'POST'])
def search():
    search_form = SearchForm()
    close_form = CloseForm()
    address,error = "",False
    if search_form.validate_on_submit():
        session['searchterm'] = search_form.searchterm.data 
        try:
            new_url, new_address = True, True
            location = gmaps.places_autocomplete(session['searchterm'])[0]
            address = location['description']
            rand_url = addon()
            user_obj = db_session.query(User).filter_by(name=session['user']).first() 
            s = Session(rand_url, user_obj, address)
            db_session.add(s)
            db_session.commit()
        except IndexError:
            error = True
            new_url, new_address = False, False
            rand_url = ""
        #geocode_result = gmaps.geocode(address)
        return render_template('submission.html',form=close_form,new_url=new_url,new_address=new_address,poll_url=poll_url+rand_url,address=address,error=error)
    if 'user' in session.keys() and session['user']:
        logged_in = session['user']
    else:
        logged_in = None
    return render_template('index.html', form=search_form, address=address,username=logged_in,error=error)

"""
POLL VIEWS
"""

class PollForm(Form):
    price = IntegerField(label="price", description="Price")
    keywords = SelectMultipleField(label="Type", choices=[('newamerican', 'New American'), ('tradamerican', 'Traditional American'), ('chinese', 'Chinese'), ('indpak', 'Indian'), ('italian', 'Italian'), ('japanese', 'Japanese'), ('korean', 'Korean'), ('mediterranean', 'Mediterranean'), ('mexican', 'Mexican'), ('thai', 'Thai'), ('taiwanese', 'Taiwanese'), ('vietnamese', 'Vietnamese')])
    #keyterms = StringField("Keyterms")
    submit = SubmitField('Submit')

@app.route("/<unique_id>", methods=['GET', 'POST'])
def poll(unique_id):
    form = PollForm()
    if form.validate_on_submit():
        user_obj = db_session.query(User).filter_by(name=session['user']).first()
        s = db_session.query(Session).filter_by(url_id=unique_id).first()
        price_choice = form.price.data
        print unique_id
        cuisine_choice = ' '.join(form.keywords.data)
        print cuisine_choice
        p = Poll(price_choice, cuisine_choice, s, user_obj)
        db_session.add(p)
        db_session.commit()
	return render_template('thanks.html')
    return render_template('poll.html', form=form)

"""
LOGIN VIEWS
"""

@app.route("/login/<user>")
def login(user):
    user_item = db_session.query(User).filter_by(name=user).first()
    if user_item:
    	session['user'] = user
	return render_template('login.html', user=user, result=True)
    else:
	return render_template('login.html', user=user, result=False)
    
@app.route("/logout")
def logout():
    session['user'] = None
    return render_template('logout.html')

"""
MAIN APP
"""
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

