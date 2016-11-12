from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()
engine = create_engine('postgresql://postgres:postgres@localhost:5432/welp', convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    from models import *
    Base.metadata.create_all(bind=engine)
    users = ["Tommy", "Averal", "Jordan", "Kegan", "Mason"]
    for user in users:
	print("Initializing " + user)
    	get_or_create(db_session, User, name=user)
    print("Initializing user done")

def get_or_create(session, model, **kwargs):
  instance = session.query(model).filter_by(**kwargs).first()
  if instance:
    print("User found")
    return instance
  else:
    instance = model(**kwargs)
    session.add(instance)
    session.commit()
    print("New user created")
    return instance

if __name__=="__main__":
    init_db()
