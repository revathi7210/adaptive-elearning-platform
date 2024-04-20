from . import db
from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship

class Student(db.Model):
    __tablename__ = 'student'
    id = Column(Integer, primary_key=True)
    email = Column(String(1000))
    pwd = Column(String(65535))
    username = Column(String(1000), unique=True)
    learnstyle = Column(String(1000))

class Client(db.Model):
    __tablename__ = 'client'

    id = Column(Integer, primary_key=True)
    email = Column(String(1000))
    pwd = Column(String(65535))
    clientname = Column(String(1000), unique=True)

class FirstQuiz(db.Model):
    __tablename__ = 'first_quiz'

    id = Column(Integer, primary_key=True)
    question = Column(String(2000))
    choice1 = Column(String(1000))
    choice2 = Column(String(1000))
    choice3 = Column(String(1000))
    choice4 = Column(String(1000))

class Course(db.Model):
    __tablename__ = 'course'

    id = Column(Integer, primary_key=True)
    coursename = Column(String(1000), unique=True)
    coursedescription = Column(String(65535))
    clientid = Column(Integer, ForeignKey('client.id'))
    client = relationship("Client")

class Lesson(db.Model):
    __tablename__ = 'lesson'

    id = Column(Integer, primary_key=True)
    lessonname = Column(String(1000))
    lessondescription = Column(String(65535))
    courseid = Column(Integer, ForeignKey('course.id'))
    course = relationship("Course")


class Material(db.Model):
    __tablename__ = 'material'

    id = Column(Integer, primary_key=True)
    visual = Column(String(65535))
    auditory = Column(String(65535))
    reading = Column(String(65535))
    difficulty = Column(String(1000))
    lessonid = Column(Integer, ForeignKey('lesson.id'))
    lesson = relationship("Lesson")

class Questionnaire(db.Model):
    __tablename__ = 'questionnaire'

    id = Column(Integer, primary_key=True)
    question = Column(String(65535))
    choice1 = Column(String(1000))
    choice2 = Column(String(1000))
    choice3 = Column(String(1000))
    choice4 = Column(String(1000))
    answer = Column(String(65535))
    difficulty = Column(String(1000))
    lessonid = Column(Integer, ForeignKey('lesson.id'))
    lesson = relationship("Lesson")


class MaterialProgress(db.Model):
    __tablename__ = 'material_progress'

    id = Column(Integer, primary_key=True)
    studentid = Column(Integer, ForeignKey('student.id'))
    lessonid = Column(Integer, ForeignKey('lesson.id'))
    materialid = Column(Integer, ForeignKey('material.id'))

class LessonProgress(db.Model):
    __tablename__ = 'lesson_progress'

    id = Column(Integer, primary_key=True)
    progress = Column(Float(precision=2))
    studentid = Column(Integer, ForeignKey('student.id'))
    lessonid = Column(Integer, ForeignKey('lesson.id'))

class CourseProgress(db.Model):
    __tablename__ = 'course_progress'

    id = Column(Integer, primary_key=True)
    progress = Column(Float(precision=2))
    studentid = Column(Integer, ForeignKey('student.id'))
    courseid = Column(Integer, ForeignKey('course.id'))