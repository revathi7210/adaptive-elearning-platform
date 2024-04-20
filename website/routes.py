from flask import render_template, url_for, redirect, request, session
from website import app, db
from website.models import User

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']

    existing_user = User.query.filter_by(username=username).first()
    existing_email = User.query.filter_by(email=email).first()
    if existing_user or existing_email:
        return "Username or email already exists. Please choose another one."
    
    new_user = User(username=username, email=email,password=password)

    db.session.add(new_user)
    db.session.commit()
    StudentId = new_user.id

    return redirect(url_for('/home',StudentId=StudentId))

@app.route('<int:StudentId>/home')
def home(StudentId):
    return render_template('home.html')