from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Base

engine = create_engine('sqlite:///catalog.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
db_session = DBSession()

db_session.add(Category(name="Soccer"))
db_session.add(Category(name="Basketball"))
db_session.add(Category(name="Baseball"))
db_session.add(Category(name="Frisbee"))
db_session.add(Category(name="Snowboarding"))
db_session.add(Category(name="Rock Climbing"))
db_session.add(Category(name="Foosball"))
db_session.add(Category(name="Skating"))
db_session.add(Category(name="Hockey"))

db_session.commit()
