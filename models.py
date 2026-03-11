from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    bio = db.Column(db.String(255), default="Ready to excel!")
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    role = db.Column(db.String(20), default="student")  # student, faculty, admin
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    results = db.relationship('ExamResult', backref='student', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)
    category = db.Column(db.String(50), default="General")
    difficulty = db.Column(db.String(10), default="easy")  # easy, medium, hard

class ExamResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, default=10)
    time_taken = db.Column(db.Integer)
    difficulty = db.Column(db.String(10), default="easy")
    date_completed = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
