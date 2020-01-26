import os

from flask import Flask, session, request, render_template
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
#@login_required REACTIVATE LATER??
def index():
  session.clear()
  if request.method == "POST":
    return render_template("index.html")
  else:
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
  session.clear()
  if request.method == "POST":
    user = request.form.get("username")
    if user == None:
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
      db.execute("INSERT INTO users (name, hash) VALUES (:name, :hash)", {"name": user, "hash": hash})
      db.commit()
    except:
      print("STOP BUG 4")
      return render_template("apology.html", text="User already exists or something else wrong.")
    session["username"] = user
    return render_template("index.html")

  else:
    return render_template("register.html")
