from flask import render_template,url_for,redirect,request,session
from website import app
import psycopg2
import os


def db_conn():
    conn = psycopg2.connect(database="", host="localhost", user="",password="",port="5432")
    return conn

@app.route('/')
def home():
    return render_template('home.html')