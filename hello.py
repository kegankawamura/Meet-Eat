#app.py 
from flask import Flask, render_template, session, redirect, url_for, request 
from flask.ext.wtf import Form 
from wtforms import StringField, SubmitField, RadioField
from flask.ext.bootstrap import Bootstrap
from wtforms.validators import Required

from wiki_sentiment import * 

import ipdb
import rauth
import time
# from yelp.client import Client
# from yelp.oauth1_authenticator import Oauth1Authenticator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess'

bootstrap = Bootstrap(app)

# location data type is a tuple(lat, long)
# response data type is {user1: {price: '$', type: 'bbq'}, ..., userN: {price: '$$$', type: 'mexican'}}
# below call should query bbq places
# make_query((37.7749, -122.4194), {'tommy': {'price': '$', 'type': 'bbq'}, 'jordan': {'price': '$$', 'type': 'bbq'}, 'averal': {'price': '$$$', 'type': 'african'}})
def make_query(location, response):

    query_cuisine = dict()
    # majority vote
    for user in response:
        if response[user]['type'] not in query_cuisine:
            query_cuisine[response[user]['type']] = 1
        else:
            query_cuisine[response[user]['type']] += 1
    popular_cuisine = max(query_cuisine, key=query_cuisine.get)

    params = {}
    params["term"] = "restaurants"
    params["ll"] = "{},{}".format(str(location[0]),str(location[1]))
    params["radius_filter"] = "25"
    params["limit"] = "3"
    params["category_filter"] = popular_cuisine

    session = rauth.OAuth1Session(
        consumer_key = YOUR_CONSUMER_KEY,
        consumer_secret = YOUR_CONSUMER_SECRET,
        access_token = YOUR_TOKEN,
        access_token_secret = YOUR_TOKEN_SECRET
        )

    request = session.get("http://api.yelp.com/v2/search", params=params)
    data = request.json()
    session.close()
    if len(data['businesses']) == 0:
        return None
    filter_data = []
    for business in data['businesses']:
        # check if the business is closed
        if not business['is_closed']:
            filter_data.append(business)

    print filter_data
    fields = extract_useful_data(filter_data)
    return fields

def replace_NA(key, dictionary):
    if key in dictionary:
        return dictionary[key]
    return 'N/A'



# from a list of businesses, we want to extract their name, rating, rating_img_url, review_count, url, display_phone, distance, location->display_address
# if an entry doesn't exist, return 'N/A'
def extract_useful_data(businesses):
    useful_data = [] 
    for business in businesses:
        useful_data.append([replace_NA('name', business), replace_NA('rating', business), replace_NA('rating_img_url', business), replace_NA('review_count', business),
            replace_NA('url', business), replace_NA('display_phone', business), replace_NA('distance', business), replace_NA('display_address', business['location'])[0], replace_NA('display_address', business['location'])[1]])
    return useful_data

print make_query((37.7749, -122.4194), {'tommy': {'price': '$', 'type': 'bbq'},
 'jordan': {'price': '$$', 'type': 'asianfusion'}, 'averal': {'price': '$$$', 'type': 'asianfusion'}})

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

@app.route("/resume")
def hello():
    return render_template('index.html')

@app.route("/", methods=['GET', 'POST'])
def search():
    if form.validate_on_submit():
        session['searchterm'] = form.searchterm.data 
        session['sentiment'], session['titlearticle'], session['wikiurl'] = get_sentiment_from_url(get_one_url_from_wiki_search(session.get('searchterm')))
        return redirect(url_for('search'))
    return render_template('search.html', form=form, searchterm=session.get('searchterm'), number=session.get('sentiment'), titlearticle=session.get('titlearticle'), wikiUrl=session.get('wikiurl'))


if __name__ == "__main__":
    app.run(debug=True)
