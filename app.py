#app.py 
from flask import Flask, render_template, session, redirect, url_for, request 
from flask.ext.wtf import Form 
from wtforms import StringField, SubmitField, RadioField
from flask.ext.bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy
from wtforms.validators import Required
from database import db_session
from wiki_sentiment import * 

import ipdb

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.from_object("config.Config")
db = SQLAlchemy(app)

app.config['SECRET_KEY'] = 'hard to guess'

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
