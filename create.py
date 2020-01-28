import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker # Not sure I need scoped_session for create.py, users don't mess with this..?

# create an engine
# Note: os.getenv("...") is used to get value of env variable (&returns connection string). Below is a connection string though.
# create_engine() then expects a connection string as argument.
engine = create_engine("postgres://otdgotgwpmsmhr:f88d0e15de2c7ee58e196e140accad01a7ccb16fd3e994734419e197a709d1ca@ec2-79-125-126-205.eu-west-1.compute.amazonaws.com:5432/df6uopvbd3t6ii")

# Create a configured Session-class
Session = sessionmaker(bind=engine)

# create a session
db = Session()

db.execute("CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR UNIQUE NOT NULL, hash VARCHAR NOT NULL)")
db.execute("CREATE TABLE books (isbn VARCHAR PRIMARY KEY, title VARCHAR NOT NULL, author VARCHAR, year VARCHAR)")
db.execute("CREATE TABLE reviews (id SERIAL PRIMARY KEY, rating INTEGER, user_id INTEGER REFERENCES users, isbn VARCHAR REFERENCES books, CHECK (rating > 0 AND rating < 6))")
db.commit()
