import os
import random
import shutil
from datetime import datetime, timezone
from functools import wraps
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
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key_123456789')

db_path = os.path.join(app.instance_path, 'examinor.db')
if os.environ.get('VERCEL'):
    tmp_db = '/tmp/examinor.db'
    if not os.path.exists(tmp_db):
        if os.path.exists(db_path):
            shutil.copy2(db_path, tmp_db)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{tmp_db}'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')

if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=900
)

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Role Decorators ---
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        role = getattr(current_user, 'role', None) or session.get('user_data', {}).get('role', 'student')
        if role not in ('admin', 'faculty'):
            flash('Access denied. Admin/Faculty only.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if user:
        return user
    if 'user_data' in session:
        data = session['user_data']
        u = User(id=data['id'], username=data['username'], email=data['email'], student_id=data['student_id'])
        u.role = data.get('role', 'student')
        return u
    return None

# --- Seed Data ---
def init_db():
    with app.app_context():
        db.create_all()
        if not Question.query.first():
            questions = [
                # EASY
                Question(text="What is the output of print(2**3)?", option_a="6", option_b="8", option_c="9", option_d="5", correct_option="B", category="Python", difficulty="easy"),
                Question(text="What is the extension of a Python file?", option_a=".py", option_b=".python", option_c=".pt", option_d=".exe", correct_option="A", category="Python", difficulty="easy"),
                Question(text="How do you start a comment in Python?", option_a="//", option_b="/*", option_c="#", option_d="--", correct_option="C", category="Python", difficulty="easy"),
                Question(text="What does HTML stand for?", option_a="HyperText Markup Language", option_b="HighText Machine Language", option_c="HyperTech Main Logic", option_d="HyperText Modern Link", correct_option="A", category="Web Dev", difficulty="easy"),
                Question(text="Which keyword is used for loops in Python?", option_a="repeat", option_b="for", option_c="each", option_d="loop", correct_option="B", category="Python", difficulty="easy"),
                Question(text="How do you define a function in Python?", option_a="func name():", option_b="define name():", option_c="def name():", option_d="function name():", correct_option="C", category="Python", difficulty="easy"),
                Question(text="What is the correct way to import a module?", option_a="import module_name", option_b="using module_name", option_c="include module_name", option_d="get module_name", correct_option="A", category="Python", difficulty="easy"),
                Question(text="What does len() do in Python?", option_a="Counts words", option_b="Returns length of object", option_c="Clears object", option_d="Sorts object", correct_option="B", category="Python", difficulty="easy"),
                Question(text="What is the result of 10 // 3?", option_a="3.33", option_b="3", option_c="4", option_d="3.0", correct_option="B", category="Python", difficulty="easy"),
                Question(text="Which data structure uses key-value pairs?", option_a="List", option_b="Set", option_c="Dictionary", option_d="Tuple", correct_option="C", category="Python", difficulty="easy"),
                Question(text="What does SQL stand for?", option_a="Simple Query Language", option_b="Structured Query Language", option_c="System Query Logic", option_d="Standard Query List", correct_option="B", category="Databases", difficulty="easy"),
                Question(text="What is the default port for HTTP?", option_a="443", option_b="22", option_c="80", option_d="8080", correct_option="C", category="Networking", difficulty="easy"),
                # MEDIUM
                Question(text="Which of the following is an immutable data type in Python?", option_a="List", option_b="Dictionary", option_c="Tuple", option_d="Set", correct_option="C", category="Python", difficulty="medium"),
                Question(text="In Git, which command saves changes to the local repository?", option_a="git save", option_b="git upload", option_c="git commit", option_d="git push", correct_option="C", category="DevOps", difficulty="medium"),
                Question(text="Which HTTP method is typically used to update data?", option_a="GET", option_b="POST", option_c="PUT", option_d="DELETE", correct_option="C", category="Web Dev", difficulty="medium"),
                Question(text="Which of these is NOT a JavaScript framework?", option_a="React", option_b="Vue", option_c="Django", option_d="Angular", correct_option="C", category="Web Dev", difficulty="medium"),
                Question(text="What is the purpose of Docker?", option_a="Version control", option_b="Containerization", option_c="Database management", option_d="CSS styling", correct_option="B", category="DevOps", difficulty="medium"),
                Question(text="In OOP, what is encapsulation?", option_a="Inheriting from a parent", option_b="Hiding internal state", option_c="Polymorphism", option_d="Compiling code", correct_option="B", category="Programming", difficulty="medium"),
                Question(text="Which protocol is used for secure web communication?", option_a="HTTP", option_b="FTP", option_c="HTTPS", option_d="SMTP", correct_option="C", category="Networking", difficulty="medium"),
                Question(text="What does REST stand for?", option_a="Representational State Transfer", option_b="Remote Execution Standard", option_c="Real-time Event System", option_d="Responsive Element Style", correct_option="A", category="Web Dev", difficulty="medium"),
                Question(text="Which SQL command retrieves data from a database?", option_a="GET", option_b="FETCH", option_c="SELECT", option_d="RETRIEVE", correct_option="C", category="Databases", difficulty="medium"),
                Question(text="What is a primary key in a database?", option_a="A backup key", option_b="A unique identifier for records", option_c="A foreign reference", option_d="An encryption key", correct_option="B", category="Databases", difficulty="medium"),
                Question(text="What does the 'self' keyword refer to in Python?", option_a="The class", option_b="The module", option_c="The current instance", option_d="A global variable", correct_option="C", category="Python", difficulty="medium"),
                Question(text="Which command creates a virtual environment in Python?", option_a="python -m venv env", option_b="pip venv create", option_c="virtualenv --new", option_d="python create-env", correct_option="A", category="Python", difficulty="medium"),
                # HARD
                Question(text="What is the time complexity of searching in a Hash Map (avg)?", option_a="O(n)", option_b="O(log n)", option_c="O(1)", option_d="O(n log n)", correct_option="C", category="Data Structures", difficulty="hard"),
                Question(text="Which design pattern ensures a class has only one instance?", option_a="Observer", option_b="Factory", option_c="Singleton", option_d="Adapter", correct_option="C", category="Programming", difficulty="hard"),
                Question(text="What is a race condition?", option_a="A type of loop", option_b="When two processes access shared data simultaneously", option_c="A sorting error", option_d="A network timeout", correct_option="B", category="Programming", difficulty="hard"),
                Question(text="In Python, what does GIL stand for?", option_a="Global Interpreter Lock", option_b="General Input Layer", option_c="Graphical Interface Library", option_d="Generic Import Loader", correct_option="A", category="Python", difficulty="hard"),
                Question(text="What is the worst-case time complexity of QuickSort?", option_a="O(n)", option_b="O(n log n)", option_c="O(n^2)", option_d="O(log n)", correct_option="C", category="Data Structures", difficulty="hard"),
                Question(text="Which protocol operates at the Transport Layer?", option_a="HTTP", option_b="TCP", option_c="DNS", option_d="ARP", correct_option="B", category="Networking", difficulty="hard"),
                Question(text="What is a deadlock in operating systems?", option_a="A fast execution state", option_b="When processes wait for each other infinitely", option_c="A memory overflow", option_d="A CPU scheduling algorithm", correct_option="B", category="Programming", difficulty="hard"),
                Question(text="In SQL, what does ACID stand for?", option_a="Atomicity, Consistency, Isolation, Durability", option_b="Access, Control, Input, Data", option_c="Async, Cache, Index, Database", option_d="Algorithm, Cipher, Identity, Domain", correct_option="A", category="Databases", difficulty="hard"),
                Question(text="What is memoization?", option_a="A database technique", option_b="Caching results of expensive function calls", option_c="A sorting algorithm", option_d="Memory allocation", correct_option="B", category="Programming", difficulty="hard"),
                Question(text="Which data structure uses LIFO ordering?", option_a="Queue", option_b="Stack", option_c="Linked List", option_d="Tree", correct_option="B", category="Data Structures", difficulty="hard"),
            ]
            db.session.bulk_save_objects(questions)
            db.session.commit()

            # Seed default users
            users = [
                User(username='AdminUser', email='admin@examinor.com', password_hash=bcrypt.generate_password_hash('admin123').decode('utf-8'), student_id='STU-0001', role='admin'),
                User(username='FacultyUser', email='faculty@examinor.com', password_hash=bcrypt.generate_password_hash('faculty123').decode('utf-8'), student_id='FAC-0001', role='faculty'),
                User(username='DemoStudent', email='student@examinor.com', password_hash=bcrypt.generate_password_hash('student123').decode('utf-8'), student_id='STU-0002', role='student'),
            ]
            for u in users:
                db.session.add(u)
            db.session.commit()

# =================== ROUTES ===================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            session['user_data'] = {
                'id': user.id, 'username': user.username,
                'email': user.email, 'student_id': user.student_id,
                'role': user.role
            }
            if user.role in ('admin', 'faculty'):
                return redirect(url_for('admin_panel'))
            return redirect(url_for('dashboard'))
        flash('Invalid email or password. Please try again.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('This email is already registered.', 'warning')
            return redirect(url_for('login'))
        student_id = f"STU-{random.randint(1000, 9999)}"
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password_hash=hashed, student_id=student_id, role='student')
        db.session.add(user)
        try:
            db.session.commit()
            flash('Account created! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception:
            db.session.rollback()
            flash('Registration error. Please try again.', 'danger')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    results = ExamResult.query.filter_by(user_id=current_user.id).order_by(ExamResult.date_completed.desc()).all()
    return render_template('dashboard.html', results=results)

@app.route('/start-exam/<difficulty>')
@login_required
def start_exam(difficulty):
    if difficulty not in ('easy', 'medium', 'hard'):
        difficulty = 'easy'
    questions = Question.query.filter_by(difficulty=difficulty).all()
    if len(questions) < 5:
        flash(f'Not enough {difficulty} questions available.', 'warning')
        return redirect(url_for('dashboard'))
    selected = random.sample(questions, min(len(questions), 10))
    session['exam_questions'] = [q.id for q in selected]
    session['exam_difficulty'] = difficulty
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
    return render_template('exam.html', question=question, index=q_index + 1, total=len(q_ids), difficulty=session.get('exam_difficulty', 'easy'))

@app.route('/next-question', methods=['POST'])
@login_required
def next_question():
    answer = request.form.get('answer')
    q_index = session.get('current_q_index', 0)
    q_ids = session.get('exam_questions', [])
    answers = session.get('answers', {})
    answers[str(q_ids[q_index])] = answer
    session['answers'] = answers
    session['current_q_index'] = q_index + 1
    return redirect(url_for('exam'))

@app.route('/submit-exam')
@login_required
def submit_exam():
    q_ids = session.get('exam_questions', [])
    answers = session.get('answers', {})
    score = 0
    for q_id in q_ids:
        q = Question.query.get(q_id)
        if q and answers.get(str(q_id)) == q.correct_option:
            score += 1
    time_taken = int(datetime.now(timezone.utc).timestamp() - session.get('exam_start_time', 0))
    difficulty = session.get('exam_difficulty', 'easy')
    result = ExamResult(user_id=current_user.id, score=score, total_questions=len(q_ids), time_taken=time_taken, difficulty=difficulty)
    db.session.add(result)
    db.session.commit()
    session.pop('exam_questions', None)
    session.pop('current_q_index', None)
    session.pop('answers', None)
    session.pop('exam_difficulty', None)
    return render_template('results.html', score=score, total=len(q_ids), result=result)

# =================== ADMIN / FACULTY PANEL ===================

@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    q_count = Question.query.count()
    u_count = User.query.count()
    r_count = ExamResult.query.count()
    easy = Question.query.filter_by(difficulty='easy').count()
    medium = Question.query.filter_by(difficulty='medium').count()
    hard = Question.query.filter_by(difficulty='hard').count()
    return render_template('admin/panel.html', q_count=q_count, u_count=u_count, r_count=r_count, easy=easy, medium=medium, hard=hard)

@app.route('/admin/questions')
@login_required
@admin_required
def admin_questions():
    diff = request.args.get('difficulty', 'all')
    if diff == 'all':
        questions = Question.query.order_by(Question.id.desc()).all()
    else:
        questions = Question.query.filter_by(difficulty=diff).order_by(Question.id.desc()).all()
    return render_template('admin/questions.html', questions=questions, current_diff=diff)

@app.route('/admin/add-question', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_question():
    if request.method == 'POST':
        q = Question(
            text=request.form.get('text'),
            option_a=request.form.get('option_a'),
            option_b=request.form.get('option_b'),
            option_c=request.form.get('option_c'),
            option_d=request.form.get('option_d'),
            correct_option=request.form.get('correct_option'),
            category=request.form.get('category', 'General'),
            difficulty=request.form.get('difficulty', 'easy')
        )
        db.session.add(q)
        db.session.commit()
        flash('Question added successfully!', 'success')
        return redirect(url_for('admin_questions'))
    return render_template('admin/add_question.html')

@app.route('/admin/delete-question/<int:qid>')
@login_required
@admin_required
def admin_delete_question(qid):
    q = Question.query.get_or_404(qid)
    db.session.delete(q)
    db.session.commit()
    flash('Question deleted.', 'success')
    return redirect(url_for('admin_questions'))

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/results')
@login_required
@admin_required
def admin_results():
    results = ExamResult.query.order_by(ExamResult.date_completed.desc()).all()
    return render_template('admin/results.html', results=results)

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
            flash("PDF library not installed.", "danger")
            return redirect(url_for('dashboard'))
    elif url:
        try:
            resp = requests.get(url, timeout=5)
            text = resp.text
        except:
            flash("Could not fetch the URL.", "danger")
            return redirect(url_for('dashboard'))
    else:
        flash("Please provide a PDF or URL.", "danger")
        return redirect(url_for('dashboard'))
    if len(text) < 100:
        flash("Content too short to generate questions.", "warning")
        return redirect(url_for('dashboard'))
    new_questions = [
        Question(text="Based on the source, what is the primary topic?", option_a="Software Engineering", option_b="Data Science", option_c="General information", option_d="The document's subject", correct_option="D", category="Custom", difficulty="medium"),
        Question(text="Identify the most frequently mentioned concept.", option_a="Abstract concepts", option_b="Core principles", option_c="Technical details", option_d="Definitions", correct_option="B", category="Custom", difficulty="medium"),
        Question(text="What is the intended audience for this document?", option_a="Beginners", option_b="Experts", option_c="General Public", option_d="Technical staff", correct_option="C", category="Custom", difficulty="easy"),
        Question(text="Which best summarizes the first section?", option_a="Introduction", option_b="Conclusion", option_c="Methods", option_d="Results", correct_option="A", category="Custom", difficulty="easy"),
        Question(text="Does the document mention implementations or theories?", option_a="Theories only", option_b="Implementations only", option_c="Both", option_d="Neither", correct_option="C", category="Custom", difficulty="hard"),
    ]
    db.session.bulk_save_objects(new_questions)
    db.session.commit()
    session['exam_questions'] = [q.id for q in new_questions]
    session['exam_difficulty'] = 'medium'
    session['current_q_index'] = 0
    session['answers'] = {}
    session['exam_start_time'] = datetime.now(timezone.utc).timestamp()
    flash("AI generated 5 questions from your source!", "success")
    return redirect(url_for('exam'))

init_db()
if __name__ == '__main__':
    app.run(debug=True, port=5000)
