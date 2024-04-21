from werkzeug.utils import secure_filename
import boto3
import uuid
from website import db
from website.models import Material
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
        usertype = request.form['usertype']
        if usertype == 'student':
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

        if usertype == 'client':
            selectExistingUserQuery = f'''SELECT * from client where clientname='{username}';'''
            cur.execute(selectExistingUserQuery)
            data1 = cur.fetchone()
            selectExistingEmailQuery = f'''SELECT * from client where email='{email}';'''
            cur.execute(selectExistingEmailQuery)
            data2 = cur.fetchone()
            if data1 != None or data2 != None:
                return "Username or email already exists. Please choose another one."
            
            cur.execute("INSERT INTO client (email, pwd, clientname) VALUES (%s, %s, %s);", (email, password,username))
            conn.commit()
            return redirect(url_for('login'))
        
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
        usertype = request.form['usertype']
        if usertype == 'student':
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
        if usertype == 'client':
            getClientId = f'''Select * from client where clientname='{username}';'''
            cur.execute(getClientId)
            data = cur.fetchone()
            
            clientid=data[0]
            pwd=data[2]
            if clientid == None :
                return "User account Does not exist. Please Signup."
            else :
                if password != pwd :
                    return "Incorrect password."
                else :
                    return redirect(url_for('insertMaterial',clientid=clientid))

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

        print(not_enrolled_courses)

        return render_template('dashboard.html',studentId=studentId,enrolled_courses=enrolled_courses,not_enrolled_courses=not_enrolled_courses)
    elif request.method == 'POST':

        data = request.json
        # Access the course ID
        course_id = data.get('courseId')

        # Process the course ID as needed
        print("Received course ID:", course_id)
        return redirect(url_for('course'))


@app.route('/enroll', methods=['POST'])
def enroll():
    studentId = request.json.get('studentId')
    courseId = request.json.get('courseId')
    
    conn=db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO course_progress (progress, studentid, courseid) VALUES (%s, %s, %s);", ('0',studentId, courseId))
    cur.execute("SELECT id FROM lesson WHERE courseid = %s", (courseId),)
    course_lessons = cur.fetchall()
    for lesson in course_lessons:
        cur.execute("INSERT INTO lesson_progress (progress, studentid, lessonid) VALUES (%s, %s, %s);", ('0',studentId, lesson))

    conn.commit()
    return redirect(url_for('course',studentId=studentId,courseId=courseId))  # Correct way to redirect

@app.route('/<int:studentId>/course/<int:courseId>', methods=['GET', 'POST'])
def course(studentId,courseId):
    conn=db_conn()
    cur = conn.cursor()
    if request.method == 'GET':
        
        cur.execute("SELECT l.id, l.lessonname, l.lessondescription FROM lesson l JOIN lesson_progress lp ON l.id=lp.lessonid WHERE lp.progress = 0 AND lp.studentid = %s AND l.courseid = %s", (studentId, courseId,))
        not_attempted_lessons = cur.fetchall()
        print('0',not_attempted_lessons)

        cur.execute("SELECT l.id, l.lessonname, l.lessondescription FROM lesson l JOIN lesson_progress lp ON l.id=lp.lessonid WHERE lp.progress > 0 AND lp.progress < 100 AND lp.studentid = %s AND l.courseid = %s", (studentId, courseId,))
        on_going_lessons = cur.fetchone()
        print('0-100',on_going_lessons)

        cur.execute("SELECT l.id, l.lessonname, l.lessondescription FROM lesson l JOIN lesson_progress lp ON l.id=lp.lessonid WHERE lp.progress = 100 AND lp.studentid = %s AND l.courseid = %s", (studentId, courseId,))
        completed_lessons = cur.fetchall()
        print('100',completed_lessons)


        return render_template('course.html',studentId=studentId,courseId=courseId,not_attempted_lessons=not_attempted_lessons,on_going_lessons=on_going_lessons,completed_lessons=completed_lessons)  




def get_questions(LessonId):
    conn = db_conn()
    cur = conn.cursor()
    
    select_query = f'''SELECT question,choice1,choice2,choice3,choice4,answer,difficulty FROM questionnaire where lessonid={LessonId};'''
    cur.execute(select_query)
    questions = cur.fetchall()
    # print(questions)

    return questions

def calculate_score(difficulty, time_taken,answered):
    # Assign weights based on difficulty
    weight_difficulty = 3 if difficulty == "hard" else 2 if difficulty == "medium" else 1 
    # Calculate score for the question
    score = ((weight_difficulty * answered )/(int(time_taken)))*10
    return score

def adaptive_algorithm(index,user_answer,correct_answer,difficulty,time_taken):
    if user_answer == correct_answer:
        answered = 1
    else:
        answered = 0
    question_score = calculate_score(difficulty, time_taken,answered)
    #score=score + question_score
    print(difficulty," ",time_taken," ",question_score)
    if(question_score<=3):
        difficulty='easy'
        index[0]+=1
    elif(question_score>3 and question_score<=6):
        difficulty='medium'
        index[1]+=1
    else:
        difficulty='hard'
        index[2]+=1
    
    print(index)
    print("Score:",question_score)
    return question_score,difficulty,index





@app.route('/<int:studentId>/course/<int:courseId>/<int:lessonId>/quiz', methods=['GET', 'POST'])
def quiz(studentId,courseId,lessonId):
    questions = get_questions(lessonId)
    easy_questions = [q for q in questions if q[-1].lower() == 'easy']
    medium_questions = [q for q in questions if q[-1].lower() == 'medium']
    hard_questions = [q for q in questions if q[-1].lower() == 'hard']

    if 'index' not in session:
        session['index'] = [1, 0, 0]
        session['current_question'] = 1
        session['score'] = 0
        session['currentscore'] = 0

    if request.method == 'POST':
        user_answer = request.form['user_answer']
        correct_answer = request.form['correct_answer']
        difficulty = request.form['difficulty']
        time_taken = request.form.get('time_taken')

        # Your code for converting user_answer to 'A', 'B', 'C', 'D', or 'E'
        if user_answer == request.form['option1']:
            user_answer = 'A'
        elif user_answer == request.form['option2']:
            user_answer = 'B'
        elif user_answer == request.form['option3']:
            user_answer = 'C'
        elif user_answer == request.form['option4']:
            user_answer = 'D'
        
        currentscore, difficulty, index = adaptive_algorithm(
            session['index'], user_answer, correct_answer, difficulty, time_taken)

        session['score'] += currentscore

        if difficulty == 'easy':
            current_question_data = get_question_data(easy_questions, index[0])
        elif difficulty == 'medium':
            current_question_data = get_question_data(medium_questions, index[1])
        else:
            current_question_data = get_question_data(hard_questions, index[2])

        session['index'] = index

        if session['current_question'] == 5:  # Assuming there are 5 questions
            return render_template('quiz_result.html', score=session['score'],courseId=courseId,studentId=studentId,lessonId=lessonId)

        session['current_question'] += 1

    else:
        
        current_question_data = get_question_data(
            easy_questions, session['index'][0])

    return render_template('quiz.html',
                            question=current_question_data[0],
                            options=current_question_data[1:5],
                            correct_answer=current_question_data[5],
                            difficulty=current_question_data[6],
                            courseId=courseId, lessonId=lessonId,studentId=studentId)


def get_question_data(questions_list, index):
    return questions_list[index]




def calscore(score):
    return score

def calCourseScore(courseId):
    conn=db_conn()
    cur = conn.cursor()
    cur.execute("SELECT progress FROM lesson_progress WHERE lessonid IN (SELECT id FROM lesson WHERE courseid = %s);", (courseId,))
    lesson_progress_list = [float(progress[0]) for progress in cur.fetchall()]

    if not lesson_progress_list:
        return 0.0  # No progress if the list is empty

    # Calculate the average progress across all lessons
    total_progress = sum(lesson_progress_list)
    num_lessons = len(lesson_progress_list)

    course_progress = (total_progress / num_lessons)

    # Ensure the progress is between 0 and 100
    return min(max(course_progress, 0), 100)
    

@app.route('/quizresult' ,methods=['POST'])
def updateProgressDb():
    studentId=request.args.get('studentId')
    lessonId=request.args.get('lessonId')
    courseId=request.args.get('courseId')
    score=request.args.get('score')
    score=calscore(score)
    conn=db_conn()
    cur = conn.cursor()
    cur.execute(f'''UPDATE lesson_progress set progress={score} where studentid={studentId} and lessonid={lessonId};''')
    conn.commit()

    coursescore=calCourseScore(courseId)
    cur.execute(f'''UPDATE course_progress set progress={coursescore} where studentid={studentId} and courseid={courseId};''')
    conn.commit()
    return redirect(url_for('material',studentId=studentId,courseId=courseId,lessonId=lessonId))



@app.route('/<int:studentId>/course/<int:courseId>/<int:lessonId>/material',methods=['POST','GET'])

@app.route('/insertMaterial/<int:clientId>',methods=['POST','GET'])
def insertMaterial(clientId):
    if request.method == "POST":
        # Extract data from the request
        visual_file = request.files.get('visual_file')
        auditory_file = request.files.get('auditory_file')
        reading_file = request.files.get('reading_file')
        difficulty = request.form.get('difficulty')
        lessonId = request.form.get('lessonId')

        # Save files to S3 or any other storage backend
        s3 = boto3.resource("s3")
        bucket_name = 'readingm'  # Replace with your bucket name

        # Ensure the files are not None and have a valid filename
        if visual_file:
            VisualFilename = uuid.uuid4().hex + '.' + secure_filename(visual_file.filename).rsplit('.', 1)[1].lower()
            s3.Bucket(bucket_name).upload_fileobj(visual_file, VisualFilename)

        if auditory_file:
            AuditoryFilename = uuid.uuid4().hex + '.' + secure_filename(auditory_file.filename).rsplit('.', 1)[1].lower()
            s3.Bucket(bucket_name).upload_fileobj(auditory_file, AuditoryFilename)

        if reading_file:
            ReadingFilename = uuid.uuid4().hex + '.' + secure_filename(reading_file.filename).rsplit('.', 1)[1].lower()
            s3.Bucket(bucket_name).upload_fileobj(reading_file, ReadingFilename)

        # Save data to the database
        material = Material(
            visual=f"https://{bucket_name}.s3.amazonaws.com/{VisualFilename}" if visual_file else "",
            auditory=f"https://{bucket_name}.s3.amazonaws.com/{AuditoryFilename}" if auditory_file else "",
            reading=f"https://{bucket_name}.s3.amazonaws.com/{ReadingFilename}" if reading_file else "",
            difficulty=difficulty,
            lessonid=lessonId,
        )
        db.session.add(material)  # Add to SQLAlchemy session
        db.session.commit()  # Commit to the database

        return redirect(url_for("insertMaterial",clientId=clientId))
    return render_template("uploadfiles.html",clientId=clientId)

@app.route('/')
def home():
    return render_template("home.html")
