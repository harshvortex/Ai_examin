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
    phone = db.Column(db.String(15), unique=True, nullable=True)
    otp = db.Column(db.String(6), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)
    role = db.Column(db.String(20), default="student")  # admin > faculty > student
    last_active = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships for monitoring
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
    tab_switches = db.Column(db.Integer, default=0) # Anti-cheating track
    penalty_applied = db.Column(db.Integer, default=0) # Deducted points
    tutor_feedback = db.Column(db.Text, nullable=True) # AI auto-grading feedback
    date_completed = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    snapshots = db.relationship('Snapshot', backref='result', lazy=True)

class Snapshot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey('exam_result.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_data = db.Column(db.Text, nullable=False) # Base64 snapshot
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
