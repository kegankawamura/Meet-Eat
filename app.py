#app.py 
from flask import Flask, render_template, session, redirect, url_for, request 
from flask_bootstrap import Bootstrap
from flask.ext.wtf import Form
from wtforms import widgets, StringField, SubmitField, RadioField, IntegerField, SelectMultipleField
from wtforms.validators import Required
import string
import random


from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user,\
    current_user
from oauth import OAuthSignIn


from models import User, Session, Poll
from database import db_session, db
import googlemaps
from datetime import datetime
from tokens import ServerKey, ip

"""
APP SETTINGS
"""
app = Flask(__name__)

# app.config['SECRET_KEY'] = 'top secret!'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['OAUTH_CREDENTIALS'] = {
    'facebook': {
        'id': '1603553963285641',
        'secret': 'ebd2e3b162b4c1814d630aae5fe84ab7'
    },   
    'twitter': {
        'id': 'fake',
        'secret': 'fake'
    }

}

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.from_object("config.Config")
app.config['SECRET_KEY'] = 'hard'
bootstrap = Bootstrap(app)
db.init_app(app)
lm = LoginManager(app)
lm.login_view = 'index'

"""
SESSION CREATION
"""

new_url = False
poll_url = ip
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
def index():
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
            user_obj = db_session.query(User).filter_by(name=current_user.name).first() 
            s = Session(rand_url, user_obj, address)
            db_session.add(s)
            db_session.commit()
        except IndexError:
            error = True
            new_url, new_address = False, False
            rand_url = ""
        #geocode_result = gmaps.geocode(address)
        return render_template('submission.html',form=close_form,new_url=new_url,new_address=new_address,poll_url=poll_url+"/"+rand_url,address=address,error=error)
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
    s = db_session.query(Session).filter_by(url_id=unique_id).first()
    owner = s.owner.name
    if form.validate_on_submit():
        user_obj = db_session.query(User).filter_by(name=current_user.name).first()
        price_choice = form.price.data
        print unique_id
        cuisine_choice = ' '.join(form.keywords.data)
        print cuisine_choice
        p = Poll(price_choice, cuisine_choice, s, user_obj)
        db_session.add(p)
        db_session.commit()
	return render_template('thanks.html', owner=owner)
    return render_template('poll.html', form=form, owner=owner)

"""
LOGIN VIEWS
"""

@lm.user_loader
def load_user(id):
	return User.query.get(int(id))

@app.route("/login/")
def login():
    return render_template('login.html')
    
@app.route("/logout")
def logout():
    #session['user'] = None
    #return render_template('logout.html')
    logout_user()
    return redirect(url_for('index'))
@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, name=username, email=email)
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    return redirect(url_for('index'))


"""
MAIN APP
"""
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

