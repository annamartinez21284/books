import os
import requests

from flask import Flask, session, request, render_template, redirect, flash, url_for, jsonify, json
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
      flash("Please choose username.")

    if not request.form.get("password") or not request.form.get("confirmation"):
      flash("Pls provide a password and confirm it.")
      return render_template("register.html")
    hash = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)
    if not check_password_hash(hash, request.form.get("confirmation")):
      flash("Password and confirmation do not match.")
      return render_template("register.html")

    try: # how do I know whicherror to catch if I dont know which error will occur? duplication, connection error, syntax error...?
      db.execute("INSERT INTO users (name, hash) VALUES (:name, :hash)", {"name": name, "hash": hash})
      db.commit()

    except:
      flash("User already exists or something else wrong.")
      return render_template("register.html")

    session["id"] = db.execute("SELECT id FROM users WHERE name= :name", {"name": name}).fetchone()[0]
    return redirect ("/") #why not render_template("index.html")?

  else:
    return render_template("register.html")

@app.route("/login", methods = ["GET", "POST"])
def login():
  session.clear()
  if request.method == "POST":
    if not (request.form.get("username") and request.form.get("password")):
      flash("Please provide username and password.")
      return render_template("login.html")
    name = db.execute("SELECT name FROM users WHERE name= :name", {"name": request.form.get("username")}).fetchone()

    if not name:
      flash("No such user.")
      return render_template("login.html")
    hash = db.execute("SELECT hash FROM users WHERE name= :name", {"name": request.form.get("username")}).fetchone()

    if not check_password_hash(hash[0], request.form.get("password")):
      flash("Incorrect password.")
      return render_template("login.html")

    # store user's sesh ID
    session["id"] = db.execute("SELECT id FROM users WHERE name= :name", {"name": name[0]}).fetchone()[0]

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
    # when fetching more than 1 row, array/dict is returned, but not None, even if empty, hence use rowcount (Apparently)
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
  # Make API request for Goodreads ratings info & check status quote
  res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn})
  if res.status_code != 200:
      raise Exception("ERROR: API request unsuccessful.")
  # get author, etc from my DB
  book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
  reviews = db.execute("SELECT * FROM reviews WHERE isbn = :isbn",{"isbn": isbn}).fetchall()
  return render_template("book.html", book=book, res=res.json(), reviews=reviews)

@app.route("/review/<isbn>", methods = ["GET", "POST"])
@login_required
def review(isbn):
  if request.method == "POST":
    rating = request.form.get("rating")
    review = request.form.get("review")
    reviewed = db.execute("SELECT * FROM reviews WHERE isbn= :isbn AND user_id= :user_id", {"isbn": isbn, "user_id": session["id"]}).fetchone()
    if not reviewed:
      try:
        db.execute("INSERT INTO reviews (rating, user_id, isbn, review) VALUES (:rating, :user_id, :isbn, :review)", {"rating": rating, "user_id": session["id"], "isbn": isbn, "review": review})
        db.commit()
        flash("Review submitted.")
        return redirect(url_for('view_book', isbn=isbn))
      except:
        flash("Some DB error occured.")
        return redirect(url_for('view_book', isbn=isbn))
    else:
      flash("You have already reviewed this book.")
      return redirect(url_for('view_book', isbn=isbn))
  return redirect(url_for('view_book', isbn=isbn))

@app.route("/api/<isbn>", methods =["GET"]) #methods needed?
def books_api(isbn):
  # ensure isbn exists
  book = db.execute("SELECT * FROM books WHERE isbn= :isbn", {"isbn": isbn}).fetchone()
  if book is None:
    return jsonify({"error": "ISBN not found"}), 404

  # get review count and average rating
  reviews = db.execute("SELECT AVG(rating) AS average_score, COUNT(*) AS review_count FROM reviews WHERE isbn= :isbn", {"isbn": isbn}).fetchone()
  # need the below because AVG returns Decimal which is not serializable in json
  avg_score = json.dumps(float(reviews.average_score))

  return jsonify({"title": book.title, "author": book.author, "year": book.year, "isbn": book.isbn, "review_count": reviews.review_count, "average_score": avg_score})
