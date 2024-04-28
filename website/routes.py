from werkzeug.utils import secure_filename
import boto3
import uuid
from website import db
from website.models import Material
from flask import render_template, url_for, redirect, request, session,jsonify
from website import app
import psycopg2
import numpy as np
import random

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
                    return redirect(url_for('insertMaterial',clientId=clientid))

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

def normalize_score(score, min_value, max_value):
    return (score - min_value) / (max_value - min_value)



def calculate_score(learning_style, difficulty, time_taken, is_correct):
    learning_style_weight = 0.1  # Lower weight for learning style
    difficulty_weight = 0.4  # Moderate weight for difficulty
    time_taken_weight = 0.2  # Moderate weight for time taken
    correctness_weight = 0.7  # Highest weight for correctness

    # Maximum time in seconds for normalization
    MAX_TIME = 60
    # Cap the time taken at MAX_TIME
    if time_taken > MAX_TIME:
        time_taken = MAX_TIME
    normalized_time_taken = time_taken / MAX_TIME  # Normalize to 0-1 range

    # Correctness score: high for correct, low for incorrect
    if is_correct:
        correctness_score = correctness_weight * 100  # High score for correct answers
    else:
        correctness_score = correctness_weight * 10  # Low score for incorrect answers

    # Difficulty score: lower impact when incorrect, higher when correct
    difficulty_score = (difficulty / 1) * difficulty_weight * (100 if is_correct else 10)  # Reduced for incorrect
    
    # Time taken score: reward quicker responses for incorrect answers
    if is_correct:
        # Reward faster times when correct
        time_taken_score = (1 - normalized_time_taken) * time_taken_weight * 100
    else:
        # For incorrect answers, quicker responses have a slightly higher score
        time_taken_score = (1 - normalized_time_taken) * time_taken_weight * 30  # Scale to give some reward for quickness
    
    # Learning style score
    learning_style_score = learning_style * learning_style_weight * 100
    
    # Total score with a cap at 100
    total_score = correctness_score + difficulty_score + time_taken_score + learning_style_score
    
    return min(100, total_score)  # Ensure the total score doesn't exceed 100


def calculate_thresholds(current_difficulty, sessionavg):
    """
    Calculates adaptive thresholds for the next question based on current difficulty and sessionavg.
    """
    if current_difficulty == 0.1:
        current_difficulty = "easy"
    elif current_difficulty==0.2:
        current_difficulty = "medium"
    else:
        current_difficulty="hard"

    base_threshold = 30  # Base threshold for 'easy'
    difficulty_offset = {
        'easy': -10,  # Easier questions have lower thresholds
        'medium': 0,  # Medium as baseline
        'hard': 10  # Harder questions have higher thresholds
    }
    
    # Calculate adaptive thresholds based on current difficulty and sessionavg
    easy_threshold = base_threshold + difficulty_offset[current_difficulty] - (sessionavg * 0.5)  # Adjusted for sessionavg
    medium_threshold = base_threshold + 20 + difficulty_offset[current_difficulty] - (sessionavg * 0.5)
    hard_threshold = base_threshold + 40 + difficulty_offset[current_difficulty] - (sessionavg * 0.5)
    
    return easy_threshold, medium_threshold, hard_threshold


def adaptive_algorithm(index, user_answer, correct_answer, difficulty, time_taken, sessionavg, question_count):
    """
    Determines the next question's difficulty based on sessionavg, current question's difficulty, and calculated thresholds.
    """
    # Determine if the answer is correct
    answered_correctly = 1 if user_answer == correct_answer else 0
    
    # Calculate the current question's score
    question_score = calculate_score(0.2, difficulty, time_taken, answered_correctly)
    
    # Update the session average
    total_score = sessionavg * question_count  # Total cumulative score
    total_score += question_score  # Add current question's score
    new_sessionavg = total_score / (question_count + 1)  # Calculate new session average
    
    # Calculate thresholds based on the current difficulty and new sessionavg
    easy_threshold, medium_threshold, hard_threshold = calculate_thresholds(difficulty, new_sessionavg)
    
    # Determine the next question's difficulty based on the calculated thresholds
    if new_sessionavg <= easy_threshold:
        next_difficulty = 'easy'
        index[0] += 1
    elif easy_threshold < new_sessionavg <= medium_threshold:
        next_difficulty = 'medium'
        index[1] += 1
    else:
        next_difficulty = 'hard'
        index[2] += 1
    
    print("Index:", index)
    print("Current Question Score:", question_score)
    print("New Session Average:", new_sessionavg)
    print("Next Difficulty:", next_difficulty)
    
    return question_score, next_difficulty, index






@app.route('/<int:studentId>/course/<int:courseId>/<int:lessonId>/quiz', methods=['GET', 'POST'])
def quiz(studentId,courseId,lessonId):
    questions = get_questions(lessonId)
    easy_questions = [q for q in questions if q[-1].lower() == 'easy']
    medium_questions = [q for q in questions if q[-1].lower() == 'medium']
    hard_questions = [q for q in questions if q[-1].lower() == 'hard']

    random.shuffle(easy_questions)  # Shuffle the 'easy' questions
    random.shuffle(medium_questions)  # Shuffle the 'medium' questions
    random.shuffle(hard_questions)  # Shuffle the 'hard' questions


    if 'index' not in session:
        session['index'] = [1, 0, 0]
        session['current_question'] = 1
        session['score'] = 0
        session['currentscore'] = 0

    if request.method == 'POST':
        user_answer = request.form['user_answer']
        correct_answer = request.form['correct_answer']
        difficulty = request.form['difficulty']
        if difficulty=='hard':
            difficulty = 0.3
        elif difficulty=='medium':
            difficulty = 0.2
        else :
            difficulty =0.1
        time_taken = int(request.form.get('time_taken'))

        # Your code for converting user_answer to 'A', 'B', 'C', 'D', or 'E'
        if user_answer == request.form['option1']:
            user_answer = 'A'
        elif user_answer == request.form['option2']:
            user_answer = 'B'
        elif user_answer == request.form['option3']:
            user_answer = 'C'
        elif user_answer == request.form['option4']:
            user_answer = 'D'
        sessionavg=session['score']/session['current_question']
        currentscore, difficulty, index = adaptive_algorithm(
            session['index'], user_answer, correct_answer, difficulty, time_taken,sessionavg,session['current_question'])

        session['score'] += currentscore

        print("difficulty ",difficulty,"timetaken ",time_taken," questionscore ",currentscore,"sessionscore ",session['score'])   

        if difficulty == 'easy':
            current_question_data = get_question_data(easy_questions, index[0])
        elif difficulty == 'medium':
            current_question_data = get_question_data(medium_questions, index[1])
        else:
            current_question_data = get_question_data(hard_questions, index[2])

        session['index'] = index
        
        if session['current_question'] == 5: 
            session['score']=session['score']/5 # Assuming there are 5 questions
            return redirect(url_for('quizresult', quizScore=session['score'],courseId=courseId,studentId=studentId,lessonId=lessonId))

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

@app.route('/<int:studentId>/course/<int:courseId>/<int:lessonId>/quizresult',methods=['GET','POST'])
def quizresult(studentId,courseId,lessonId):
    quizScore = request.args.get('quizScore')
    conn = db_conn()
    cur = conn.cursor()
    if request.method == 'POST':
        score=float(quizScore)
        if score > 95.0:
            print("hellooooo")
            cur.execute(f'''UPDATE lesson_progress set progress=100 where studentid={studentId} and lessonid={lessonId};''')
            conn.commit()
            return redirect(url_for("lessonComplete",studentId=studentId,courseId=courseId,lessonId=lessonId)) 
        else:
            cur.execute(f'''UPDATE lesson_progress set progress={score} where studentid={studentId} and lessonid={lessonId};''')
            conn.commit()

            coursescore=calCourseScore(courseId)
            cur.execute(f'''UPDATE course_progress set progress={coursescore} where studentid={studentId} and courseid={courseId};''')
            conn.commit()
            #calculate material difficulty to-do
            return redirect(url_for("getMaterial",score=score,studentId=studentId,courseId=courseId,lessonId=lessonId))
    else:
        return render_template('quizresult.html',score=quizScore,studentId=studentId,courseId=courseId,lessonId=lessonId)


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

@app.route('/<int:studentId>/course/<int:courseId>/<int:lessonId>/lessonComplete',methods=['GET'])
def lessonComplete(studentId, courseId, lessonId):
    conn=db_conn()
    cur = conn.cursor()
    cur.execute(f'''UPDATE lesson_progress set progress=100 where studentid={studentId} and lessonid={lessonId};''')
    conn.commit()
    cur.execute('''SELECT progress FROM course_progress WHERE studentid=%s AND courseid=%s;''', (studentId, courseId))
    courseProgress = cur.fetchone()
    return render_template("lessonComplete.html",studentId=studentId,courseId=courseId,courseProgress=courseProgress)

@app.route('/<int:studentId>/course/<int:courseId>/<int:lessonId>/material',methods=['GET'])
def getMaterial(studentId, courseId, lessonId): 
    conn=db_conn()
    cur = conn.cursor()
    cur.execute(f'''select lp.progress from lesson l join lesson_progress lp on l.id = lp.lessonid where lp.studentid={studentId} and lp.lessonid={lessonId}''')
    score=cur.fetchone()[0]
    if score > 0.75 :
        difficulty='hard'
    elif score > 0.5 :
        difficulty='medium'
    else :
        difficulty='easy'

    cur.execute(f'''select learnstyle from student where id={studentId};''')
    data=cur.fetchone()[0]
    print("difficulty", difficulty)
    print("data", data)
    if data == 'visual':
        cur.execute(f'''select visual from material where difficulty='{difficulty}' and lessonid={lessonId};''')
    elif data == 'auditory':
        cur.execute(f'''select auditory from material where difficulty='{difficulty}' and lessonid={lessonId};''')
    elif data == 'reading' or data == 'kinematics' or data == 'Modular':
        cur.execute(f'''select reading from material where difficulty='{difficulty}' and lessonid={lessonId};''')
    material = cur.fetchone()[0]
    print(material)
    return render_template('material.html',material=material,data=data,studentId=studentId,lessonId=lessonId,courseId=courseId)


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
