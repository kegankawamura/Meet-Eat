import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
	SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost:5432/welp" #os.environ['DATABASE_URL']
	DATABASE_URL = "postgresql://localhost/welp"

