from sqlalchemy.dialects.postgresql import JSON
from database import Base, db
from flask_login import UserMixin
from datetime import datetime

class Session(Base):
  __tablename__ = 'session'

  id = db.Column(db.Integer, primary_key=True)
  url_id = db.Column(db.String())
  time_created = db.Column(db.DateTime())
  owner = db.relationship("User")
  owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
  location = db.Column(db.String())

  def __init__(self, url_id, owner, location):
    self.url_id = url_id
    self.owner = owner
    self.location = location
    self.time_created = datetime.now()

class Poll(Base):
  __tablename__ = 'poll'
  id = db.Column(db.Integer, primary_key=True)
  
  price = db.Column(db.Integer())
  resp = db.Column(db.String()) 
  session = db.relationship("Session") 
  session_id = db.Column(db.Integer, db.ForeignKey('session.id'))
  user = db.relationship("User")
  user_id = db.Column(db.Integer, db.ForeignKey('user.id')) 
 
  def __init__(self, price, resp, session, user):
    self.price = price
    self.resp = resp
    self.session = session
    self.user = user

class User(UserMixin, Base):
  __tablename__ = 'user'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String())
  social_id = db.Column(db.String(64), nullable=False)
  email = db.Column(db.String(64), nullable=True) 

  def __init__(self, social_id, name, email=None):
     self.name = name
     self.social_id = social_id
     self.email = email
