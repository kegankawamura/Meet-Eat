#app.py 
from flask import Flask, render_template, session, redirect, url_for, request 
from flask_bootstrap import Bootstrap
from flask.ext.wtf import Form
from wtforms import widgets, StringField, SubmitField, RadioField, IntegerField, SelectMultipleField
from wtforms.validators import Required
import string
import random
import rauth


from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user,\
    current_user, login_required
from oauth import OAuthSignIn

from flask_googlemaps import GoogleMaps, Map


from models import User, Session, Poll
from database import db_session, db
import googlemaps
from datetime import datetime
from tokens import *

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
app.config['GOOGLEMAPS_KEY'] = ServerKey

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.from_object("config.Config")
app.config['SECRET_KEY'] = 'hard'
bootstrap = Bootstrap(app)
db.init_app(app)
lm = LoginManager(app)
lm.login_view = 'index'

"""
Google Maps
"""
GoogleMaps(app, key=ServerKey)

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

class CloseForm(Form):
    close = SubmitField('Close Poll')

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
def index():
    if current_user.is_anonymous:
	return redirect(url_for('login'))
    search_form = SearchForm()
    close_form = CloseForm()
    address,error = "",False
    if search_form.validate_on_submit():
        session['searchterm'] = search_form.searchterm.data 
        try:
            new_url, new_address = True, True
            location = gmaps.places_autocomplete(session['searchterm'])[0]
            address = location['description']
	    coord = gmaps.geocode(address)
	    latitude = coord[0]['geometry']['location']['lat']
            longitude = coord[0]['geometry']['location']['lng']
            search_map = Map(identifier="vicinity", lat=latitude, lng=longitude, markers=[(latitude, longitude, address)])
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
        return render_template('submission.html',form=close_form,new_url=new_url,new_address=new_address,poll_url=poll_url+"/"+rand_url,address=address,error=error,display_map=search_map)
    elif close_form.validate_on_submit():
        return redirect(url_for('close'))
    return render_template('index.html', form=search_form, address=address,username=current_user.name,error=error)


def make_query():
    # aggregate polls

    me = db_session.query(User).filter_by(name=current_user.name).first()
    cur_session = db_session.query(Session).filter_by(owner=me).order_by(Session.time_created.desc()).first()
    polls = db_session.query(Poll).filter_by(session=cur_session).all()

    if not polls:
        return None, None
    response_data = {}
    average_price = 0.
    # majority vote
    for poll in polls:
        average_price += poll.price
        prefs = poll.resp.split()
        for pref in prefs:
            if pref not in response_data:
                response_data[pref] = 1
            else:
                response_data[pref] += 1
    average_price /= len(polls)
    most_votes = max(response_data.values())
    best_cuisine = ",".join([k for k,v in response_data.items() if v == most_votes])

    print best_cuisine
    print average_price
    print cur_session.location

    
    params = {}
    params["term"] = "restaurants"
    params["location"] = cur_session.location
    params["radius_filter"] = "20000"
    params["limit"] = "3"
    params["category_filter"] = best_cuisine

    s = rauth.OAuth1Session(
        consumer_key = CONSUMER_KEY,
        consumer_secret = CONSUMER_SECRET,
        access_token = TOKEN,
        access_token_secret = TOKEN_SECRET
        )

    request = s.get("http://api.yelp.com/v2/search", params=params)
    data = request.json()
    s.close()
    if 'businesses' not in data.keys() or len(data['businesses']) == 0:
        return None, None
    filter_data = []
    for business in data['businesses']:
        # check if the business is closed
        if not business['is_closed']:
            filter_data.append(business)

    fields = extract_useful_data(filter_data)
    return fields, average_price

# if an entry doesn't exist, return 'None'
def extract_useful_data(businesses):
    useful_data = [] 
    for business in businesses:
        d = {'name': if_exists('name', business), 'rating': if_exists('rating', business), 'review_count': if_exists('review_count', business), 'url': if_exists('url', business), 'rating_img_url': if_exists('rating_img_url', business), 'image_url': if_exists('image_url', business)}
        if 'location' in business:
           d['address'] = if_exists('address', business)
        useful_data.append(d)
    return useful_data

def if_exists(key, dictionary):
    if key in dictionary:
        return dictionary[key]
    return None

"""
RESULTS VIEWS
"""
@app.route("/close", methods=["GET", "POST"])
def close():
    businesses, average_price = make_query()
    if not businesses or not average_price:
        print("ERROR!")
    return render_template('results.html', businesses=businesses)

"""
POLL VIEWS
"""

class PollForm(Form):
    price = IntegerField(label="price", description="Price")
    keywords = SelectMultipleField(label="Type", choices=[('newamerican', 'New American'), ('tradamerican', 'Traditional American'), ('chinese', 'Chinese'), ('indpak', 'Indian'), ('italian', 'Italian'), ('japanese', 'Japanese'), ('korean', 'Korean'), ('mediterranean', 'Mediterranean'), ('mexican', 'Mexican'), ('thai', 'Thai'), ('taiwanese', 'Taiwanese'), ('vietnamese', 'Vietnamese')])
    #keyterms = StringField("Keyterms")
    submit = SubmitField('Submit')

@app.route("/poll/<unique_id>", methods=['GET', 'POST'])
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

class LoginForm(Form):
    username = StringField('Username', validators=[Required()])
    submit = SubmitField('Submit')
    def validate(self):
        rv = Form.validate(self)
        if not rv:
	    return False
	user = db_session.query(User).filter_by(name=self.username.data).first()
        return not (user is None)


@app.route("/login_staff/", methods=["GET", "POST"])
def login_staff():
    form = LoginForm()
    if form.validate_on_submit():
	login_user(User.query.filter_by(name=form.username.data).first())
	return redirect(url_for('index'))
    return render_template('login_staff.html', form=form)

"""
MAIN APP
"""
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

