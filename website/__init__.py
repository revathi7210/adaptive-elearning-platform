from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

app=Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://flaskuser:flaskpwd@localhost:5432/flaskdb'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.config['SECRET_KEY'] = os.urandom(24)

from . import routes, models
