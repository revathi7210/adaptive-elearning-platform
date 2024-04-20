from flask import render_template, url_for, redirect, request, session,jsonify
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
        selectExistingEmailQuery = f'''SELECT * from student where email='{email}';'''
        cur.execute(selectExistingEmailQuery)
        data2 = cur.fetchone()
        
        
        if data1 != None or data2 != None:
            return "Username or email already exists. Please choose another one."
        
        cur.execute("INSERT INTO student (email, pwd, username) VALUES (%s, %s, %s);", (email, password,username))
        conn.commit()

        cur.execute(f'''select id from student where username = '{username}';''')
        studentId=cur.fetchone()
        return redirect(url_for('displayFirstQuiz',id=studentId[0]))
    return render_template("signup.html")

@app.route('/firstquiz',methods=['GET','POST'])
def displayFirstQuiz():
    studentId=request.args.get('id')
    conn=db_conn()
    cur = conn.cursor()
    cur.execute("select * from first_quiz;")
    firstQuiz = cur.fetchall()
    if request.method == 'POST':
        learnstyle = request.form['learnStyle']
        cur.execute(f'''update student set learnstyle='{learnstyle}' where id={studentId};''')
        conn.commit()
        print(learnstyle)
        return redirect(url_for('dashboard',studentId=studentId))
    return render_template("firstquiz.html",firstQuiz=firstQuiz)

@app.route('/login', methods=['GET','POST'])
def login():
    conn=db_conn()
    cur = conn.cursor()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        getStudentId = f'''Select * from student where username='{username}';'''
        cur.execute(getStudentId)
        data = cur.fetchone()
        
        studentid=data[0]
        pwd=data[2]
        #print (studentid, pwd)
        if studentid == None :
            return "User account Does not exist. Please Signup."
        else :
            if password != pwd :
                return "Incorrect password."
            else :
                return redirect(url_for('dashboard',studentId=studentid))

    return render_template("login.html")

@app.route('/<int:studentId>/dashboard',methods=['GET','POST'])
def dashboard(studentId):
    conn=db_conn()
    cur = conn.cursor()
    if request.method == 'GET':
        cur.execute("SELECT courseid FROM course_progress WHERE studentid = %s", (studentId,))
        enrolled_course_ids = [row[0] for row in cur.fetchall()]

        # Fetch the enrolled courses
        if enrolled_course_ids != []:
            cur.execute("SELECT * FROM course WHERE id IN %s", (tuple(enrolled_course_ids),))
            enrolled_courses = cur.fetchall()
            cur.execute("SELECT * FROM course WHERE id NOT IN %s", (tuple(enrolled_course_ids),))
            not_enrolled_courses = cur.fetchall()
        else:
            enrolled_courses = []
            cur.execute("SELECT * FROM course")
            not_enrolled_courses = cur.fetchall()        

        return render_template('dashboard.html',studentId=studentId,enrolled_courses=enrolled_courses,not_enrolled_courses=not_enrolled_courses)
    elif request.method == 'POST':

        data = request.json

        # Access the course ID
        course_id = data.get('courseId')

        # Process the course ID as needed
        print("Received course ID:", course_id)
        return redirect(url_for('course'))


@app.route('/course',methods=['GET','POST'])
def course():
    if request.method == 'GET':
        return render_template('course.html')

@app.route('/')
def home():
    return render_template("home.html")
