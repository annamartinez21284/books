import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# create_engine() then expects a connection string as argument.
engine = create_engine("postgres://otdgotgwpmsmhr:f88d0e15de2c7ee58e196e140accad01a7ccb16fd3e994734419e197a709d1ca@ec2-79-125-126-205.eu-west-1.compute.amazonaws.com:5432/df6uopvbd3t6ii")

# Create a configured Session-class
Session = sessionmaker(bind=engine)

# create a session
db = Session()

f = open("books.csv")
reader = csv.reader(f)

for isbn, title, author, year in reader:
  db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", \
  {"isbn": isbn, "title": title, "author": author, "year": year})

db.commit()
