import os
import random
from datetime import datetime, timezone
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import db, User, Question, ExamResult
import io
import requests
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///examinor.db')
# Handle DATABASE_URL for Postgres if using Render/Railway (they often use 'postgres://')
if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize Database and Sample Data
def init_db():
    with app.app_context():
        db.create_all()
        if not Question.query.first():
            sample_questions = [
                Question(text="What is the output of print(2**3)?", option_a="6", option_b="8", option_c="9", option_d="5", correct_option="B", category="Python"),
                Question(text="Which of the following is an immutable data type in Python?", option_a="List", option_b="Dictionary", option_c="Tuple", option_d="Set", correct_option="C", category="Python"),
                Question(text="What is the result of 10 // 3?", option_a="3.33", option_b="3", option_c="4", option_d="3.0", correct_option="B", category="Python"),
                Question(text="How do you define a function in Python?", option_a="func name():", option_b="define name():", option_c="def name():", option_d="function name():", correct_option="C", category="Python"),
                Question(text="Which keyword is used for loops in Python?", option_a="repeat", option_b="for", option_c="each", option_d="loop", correct_option="B", category="Python"),
                Question(text="What is the extension of a Python file?", option_a=".py", option_b=".python", option_c=".pt", option_d=".exe", correct_option="A", category="Python"),
                Question(text="How do you start a comment in Python?", option_a="//", option_b="/*", option_c="#", option_d="--", correct_option="C", category="Python"),
                Question(text="What is the correct way to import a module?", option_a="import module_name", option_b="using module_name", option_c="include module_name", option_d="get module_name", correct_option="A", category="Python"),
                Question(text="Which data structure uses key-value pairs?", option_a="List", option_b="Set", option_c="Dictionary", option_d="Tuple", correct_option="C", category="Python"),
                Question(text="What does len() do in Python?", option_a="Counts words", option_b="Returns length of object", option_c="Clears object", option_d="Sorts object", correct_option="B", category="Python"),
                Question(text="In Git, which command is used to save changes to the local repository?", option_a="git save", option_b="git upload", option_c="git commit", option_d="git push", correct_option="C", category="DevOps"),
                Question(text="What does SQL stand for?", option_a="Simple Query Language", option_b="Structured Query Language", option_c="System Query Logic", option_d="Standard Query List", correct_option="B", category="Databases"),
                Question(text="Which HTTP method is typically used to update data on a server?", option_a="GET", option_b="POST", option_c="PUT", option_d="DELETE", correct_option="C", category="Web Dev"),
                Question(text="What is the time complexity of searching in a Hash Map (average case)?", option_a="O(n)", option_b="O(log n)", option_c="O(1)", option_d="O(n log n)", correct_option="C", category="Data Structures"),
                Question(text="Which of these is NOT a Javascript framework?", option_a="React", option_b="Vue", option_c="Django", option_d="Angular", correct_option="C", category="Web Dev"),
                Question(text="What is the purpose of Docker?", option_a="Version control", option_b="Containerization", option_c="Database management", option_d="CSS styling", correct_option="B", category="DevOps"),
                Question(text="In object-oriented programming, what is encapsulation?", option_a="Inheriting from a parent", option_b="Hiding internal state of an object", option_c="Polymorphism", option_d="Compiling code", correct_option="B", category="Programming"),
                Question(text="What does HTML stand for?", option_a="HyperText Markup Language", option_b="HighText Machine Language", option_c="HyperTech Main Logic", option_d="HyperText Modern Link", correct_option="A", category="Web Dev"),
                Question(text="Which protocol is used for secure communication over the internet?", option_a="HTTP", option_b="FTP", option_c="HTTPS", option_d="SMTP", correct_option="C", category="Networking"),
                Question(text="What is the default port for HTTP?", option_a="443", option_b="22", option_c="80", option_d="8080", correct_option="C", category="Networking")
            ]
            db.session.bulk_save_objects(sample_questions)
            db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        student_id = f"STU-{random.randint(1000, 9999)}"
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password_hash=hashed_password, student_id=student_id)
        db.session.add(user)
        try:
            db.session.commit()
            flash('Your account has been created!', 'success')
            return redirect(url_for('login'))
        except:
            flash('Email already exists.', 'danger')
    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    results = ExamResult.query.filter_by(user_id=current_user.id).order_by(ExamResult.date_completed.desc()).all()
    return render_template('dashboard.html', results=results)

@app.route('/start-exam')
@login_required
def start_exam():
    # Fetch 10 random questions
    questions = Question.query.all()
    selected_questions = random.sample(questions, min(len(questions), 10))
    # Reset session for new exam
    session['exam_questions'] = [q.id for q in selected_questions]
    session['current_q_index'] = 0
    session['answers'] = {}
    session['exam_start_time'] = datetime.now(timezone.utc).timestamp()
    return redirect(url_for('exam'))

@app.route('/exam')
@login_required
def exam():
    if 'exam_questions' not in session:
        return redirect(url_for('dashboard'))
    
    q_index = session.get('current_q_index', 0)
    q_ids = session.get('exam_questions', [])
    
    if q_index >= len(q_ids):
        return redirect(url_for('submit_exam'))
        
    question = Question.query.get(q_ids[q_index])
    return render_template('exam.html', question=question, index=q_index + 1, total=len(q_ids))

@app.route('/next-question', methods=['POST'])
@login_required
def next_question():
    answer = request.form.get('answer')
    q_index = session.get('current_q_index', 0)
    q_ids = session.get('exam_questions', [])
    
    # Save answer
    answers = session.get('answers', {})
    answers[str(q_ids[q_index])] = answer
    session['answers'] = answers
    
    # Move to next
    session['current_q_index'] = q_index + 1
    return redirect(url_for('exam'))

@app.route('/submit-exam')
@login_required
def submit_exam():
    q_ids = session.get('exam_questions', [])
    answers = session.get('answers', {})
    
    score = 0
    for q_id in q_ids:
        question = Question.query.get(q_id)
        if answers.get(str(q_id)) == question.correct_option:
            score += 1
            
    time_taken = int(datetime.now(timezone.utc).timestamp() - session.get('exam_start_time', 0))
    
    result = ExamResult(user_id=current_user.id, score=score, total_questions=len(q_ids), time_taken=time_taken)
    db.session.add(result)
    db.session.commit()
    
    # Clear session
    session.pop('exam_questions', None)
    session.pop('current_q_index', None)
    session.pop('answers', None)
    
    return render_template('results.html', score=score, total=len(q_ids), result=result)

@app.route('/generate-from-source', methods=['POST'])
@login_required
def generate_from_source():
    text = ""
    file = request.files.get('doc_file')
    url = request.form.get('doc_url')

    if file and file.filename.endswith('.pdf'):
        if PyPDF2:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
            for page in pdf_reader.pages:
                text += page.extract_text()
        else:
            flash("PDF processing library not installed on server.", "danger")
            return redirect(url_for('dashboard'))
    elif url:
        try:
            resp = requests.get(url, timeout=5)
            text = resp.text # Simple text extraction (could use BeautifulSoup for better results)
        except:
            flash("Could not fetch the URL.", "danger")
            return redirect(url_for('dashboard'))
    else:
        flash("Please provide a PDF file or a URL.", "danger")
        return redirect(url_for('dashboard'))

    if len(text) < 100:
        flash("Source content too short to generate questions.", "warning")
        return redirect(url_for('dashboard'))

    # Mock AI Generation Logic
    # In a real app, you would send 'text' to an LLM like Gemini/OpenAI
    # Here we simulate by creating generic questions related to "The provided content"
    new_questions = [
        Question(text=f"Based on the source, what is the primary topic discussed?", option_a="Software Engineering", option_b="Data Science", option_c="General information", option_d="The document's subject", correct_option="D", category="Custom"),
        Question(text=f"Identify the most frequently mentioned concept in the analyzed text.", option_a="Abstract concepts", option_b="Core principles", option_c="Technical details", option_d="Definitions", correct_option="B", category="Custom"),
        Question(text=f"What is the intended audience for this document based on its tone?", option_a="Beginners", option_b="Experts", option_c="General Public", option_d="Technical staff", correct_option="C", category="Custom"),
        Question(text=f"Which of the following best summarizes the first section of the document?", option_a="Introduction", option_b="Conclusion", option_c="Methods", option_d="Results", correct_option="A", category="Custom"),
        Question(text=f"Does the provided document mention specific implementations or theories?", option_a="Theories only", option_b="Implementations only", option_c="Both", option_d="Neither", correct_option="C", category="Custom")
    ]
    
    db.session.bulk_save_objects(new_questions)
    db.session.commit()
    
    # Start exam with these new questions
    session['exam_questions'] = [q.id for q in new_questions]
    session['current_q_index'] = 0
    session['answers'] = {}
    session['exam_start_time'] = datetime.now(timezone.utc).timestamp()
    
    flash("AI has generated 5 specialized questions from your source!", "success")
    return redirect(url_for('exam'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
