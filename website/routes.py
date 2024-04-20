from flask import render_template, url_for, redirect, request, session
from website import app
import psycopg2

def db_conn():
    conn = psycopg2.connect(database="flaskdb", host="localhost", user="flaskuser",password="flaskpwd",port="5432")
    return conn

@app.route('/signup', methods=['GET','POST'])
def signup():
    conn=db_conn()
    cur = conn.cursor()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        selectExistingUserQuery = f'''SELECT * from student where username='{username}';'''
        cur.execute(selectExistingUserQuery)
        data1 = cur.fetchone()
        print(data1)
        selectExistingEmailQuery = f'''SELECT * from student where email='{email}';'''
        cur.execute(selectExistingEmailQuery)
        data2 = cur.fetchone()
        print(data2)
        
        if len(data1) != 0 or len(data2) != 0:
            return "Username or email already exists. Please choose another one."
        
        cur.execute("INSERT INTO student (email, pwd, username) VALUES (%s, %s, %s);", ('{email}', '{password}','{username}'))
        # getStudentId = f'''Select id from student where email='{email}' and username='{username}';'''
        # cur.execute(getStudentId)
        # data = cur.fetchall()[0]
        return redirect(url_for('home'))

    return render_template("signup.html")

@app.route('/home')
def home(StudentId):
    return render_template('home.html')

@app.route('/')
def what():
    conn=db_conn()
    cur = conn.cursor()
    select = '''select * from student;'''
    cur.execute(select)
    data=cur.fetchone()
    print(data)
    return render_template("home.html")
