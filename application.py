import os
import requests

from flask import Flask, session, request, render_template, redirect, flash
from flask_session import Session
#from flask_sqlalchemy import SQLAlchemy # I added this I think
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required

app = Flask(__name__)

# I added below line
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("postgres://otdgotgwpmsmhr:f88d0e15de2c7ee58e196e140accad01a7ccb16fd3e994734419e197a709d1ca@ec2-79-125-126-205.eu-west-1.compute.amazonaws.com:5432/df6uopvbd3t6ii")

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
  return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
  session.clear()
  if request.method == "POST":
    name = request.form.get("username")
    if name == None:
      print("STOP BUG 1")
      return render_template("apology.html", text="Please choose username.")

    if not request.form.get("password") or not request.form.get("confirmation"):
      print("STOP BUG 2")
      return render_template("apology.html", text="Pls provide a password and confirm it.")
    hash = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)
    if not check_password_hash(hash, request.form.get("confirmation")):
      print("STOP BUG 3")
      return render_template("apology.html", text="Password and confirmation do not match.")

    try: # how do I know whicherror to catch if I dont know which error will occur? duplication, connection error, syntax error...?
      db.execute("INSERT INTO users (name, hash) VALUES (:name, :hash)", {"name": name, "hash": hash})
      db.commit()
    except:
      print("STOP BUG 4")
      return render_template("apology.html", text="User already exists or something else wrong.")
    #session["username"] = name
    session["id"] = db.execute("SELECT id FROM users WHERE name= :name", {"name": name[0]}).fetchone()[0]
    return redirect ("/") #why not render_template("index.html")?

  else:
    return render_template("register.html")

@app.route("/login", methods = ["GET", "POST"])
def login():
  session.clear()
  if request.method == "POST":
    if not (request.form.get("username") and request.form.get("password")):
      return render_template("apology.html", text="Please provide username and password.")
    name = db.execute("SELECT name FROM users WHERE name= :name", {"name": request.form.get("username")}).fetchone()
    print(f"I GOT THE NAME AS {name}")
    if not name:
      return render_template("apology.html", text="No such user.")
    hash = db.execute("SELECT hash FROM users WHERE name= :name", {"name": request.form.get("username")}).fetchone()
    print(f"I GOT THE HASH AS {hash}")
    if not check_password_hash(hash[0], request.form.get("password")):
      return render_template("apology.html", text="Incorrect password.")
    #session["username"] = name[0]
    session["id"] = db.execute("SELECT id FROM users WHERE name= :name", {"name": name[0]}).fetchone()[0]
    sid = session["id"]
    print(f"I GOT SESH USER STORED AS {sid}")
    return render_template("index.html")
  else:
    return render_template("login.html")

@app.route("/logout", methods = ["GET", "POST"])
def logout():
  session.clear()
  return redirect("/")

@app.route("/search", methods = ["GET", "POST"])
@login_required
def search():
  if request.method == "POST":
    input = request.form.get("input")
    if not input:
      flash("Please provide a search term.")
      return redirect("/")
    # get list of possible result rows
    results = db.execute("SELECT * FROM books WHERE (isbn ILIKE '%' || :input || '%') OR (title ILIKE '%' || :input || '%') OR (author ILIKE '%' || :input || '%')", {"input": input, "input": input, "input": input})
    # when fetching more than 1 row, array/dict is returned, but not None, hence use rowcount (Apparently)
    if results.rowcount == 0:
      flash("Search yields no result among my 5000 books.")
      return redirect("/")
    # render search results w/ links to single book pages
    return render_template("results.html", results=results.fetchall())
  return redirect("/")

@app.route("/view_book/<isbn>", methods = ["GET", "POST"])
@login_required
def view_book(isbn):
  #user_id ="108797443"
  key ="okE6HOfUm5bzxE11NbAZmw"
  # check. r.status_code - do some try except thing
  res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn})
  print(f"JSON RESULT {res.json()}")
  book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
  return render_template("book.html", book=book, res=res.json())
