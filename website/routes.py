from flask import render_template,url_for,redirect,request,session
from website import app
import os


@app.route('/')
def home():
    return render_template('home.html')