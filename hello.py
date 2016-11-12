#app.py 
from flask import Flask, render_template, session, redirect, url_for 
from flask.ext.wtf import Form 
from wtforms import StringField, SubmitField
from flask.ext.bootstrap import Bootstrap
from wtforms.validators import Required
import string
import random

app = Flask(__name__)
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