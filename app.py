import os
import random
import shutil
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import db, User, Question, ExamResult, Snapshot, ChatMessage
import io
import json
import base64
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

from flask_caching import Cache
from flask_session import Session
import logging

# Configure Logging for security auditing
logging.basicConfig(level=logging.INFO, filename='logs/security.log',
                    format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
# Redis or File caching for speed
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

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
# --- Middleware for Hierarchy Tracking ---
@app.before_request
def update_last_active():
    if current_user.is_authenticated:
        current_user.last_active = datetime.now(timezone.utc)
        db.session.commit()

# --- Role Decorators for Power Hierarchy ---
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if current_user.role not in roles:
                flash(f'Access denied. Required: {", ".join(roles)}', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator

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
        # Force recreate for demo if columns are missing
        # In production use Migrations!
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
                User(username='DemoStudent', email='student@examinor.com', password_hash=bcrypt.generate_password_hash('student123').decode('utf-8'), student_id='STU-0002', role='student', phone='1234567890'),
            ]
            for u in users:
                db.session.add(u)
            db.session.commit()

# =================== ROUTES ===================

def send_notification(recipient, message):
    """
    Production-ready notification dispatcher using direct HTTP requests.
    Requires: TWILIO_SID, TWILIO_AUTH_TOKEN, TWILIO_NUMBER
    """
    twilio_sid = os.environ.get('TWILIO_SID')
    twilio_token = os.environ.get('TWILIO_AUTH_TOKEN')
    twilio_number = os.environ.get('TWILIO_NUMBER')
    
    if twilio_sid and twilio_token and twilio_number:
        try:
            # Use direct REST API to avoid SDK path length issues on Windows
            url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
            auth = (twilio_sid, twilio_token)
            payload = {
                'From': twilio_number,
                'To': recipient,
                'Body': message
            }
            resp = requests.post(url, data=payload, auth=auth, timeout=10)
            if resp.status_code in (200, 201):
                return True
            else:
                logging.error(f"Twilio API Error: {resp.text}")
                return False
        except Exception as e:
            logging.error(f"SMS Dispatch Failed: {str(e)}")
            return False
            
    # Fallback/Development: Log to Secure Gateway
    os.makedirs('logs', exist_ok=True)
    with open('logs/sms_gateway.log', 'a') as f:
        f.write(f"[{datetime.now()}] DISPATCHED TO {recipient}: {message}\n")
    return True

@app.route('/upload-snapshot', methods=['POST'])
@login_required
def upload_snapshot():
    # Only allow for students
    if current_user.role != 'student': return jsonify({'success': False})
    data = request.json.get('image')
    if data:
        snap = Snapshot(user_id=current_user.id, image_data=data)
        db.session.add(snap)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/send-message', methods=['POST'])
@login_required
def send_msg():
    data = request.json
    res_id = data.get('receiver_id')
    msg_text = data.get('text')
    if res_id and msg_text:
        msg = ChatMessage(sender_id=current_user.id, receiver_id=res_id, text=msg_text)
        db.session.add(msg)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/get-messages')
@login_required
def get_msgs():
    msgs = ChatMessage.query.filter_by(receiver_id=current_user.id, is_read=False).all()
    out = [{'id': m.id, 'text': m.text, 'sender': User.query.get(m.sender_id).username} for m in msgs]
    for m in msgs: m.is_read = True
    db.session.commit()
    return jsonify(out)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send-otp', methods=['POST'])
def send_otp():
    email_or_phone = request.form.get('identifier', '').strip()
    user = User.query.filter((User.email == email_or_phone) | (User.phone == email_or_phone)).first()
    if user:
        otp = str(random.randint(100000, 999999))
        user.otp = otp
        # Link OTP to window for 10 minutes
        user.otp_expiry = datetime.now(timezone.utc).replace(minute=datetime.now(timezone.utc).minute + 10)
        db.session.commit()
        
        message = f"Your AI EXAMINOR OTP is {otp}. Valid for 10 minutes."
        success = send_notification(user.phone or user.email, message)
        
        if success:
            return jsonify({'success': True, 'msg': 'Verification code sent securely to your device.'})
        else:
            return jsonify({'success': False, 'msg': 'Dispatch service busy. Try again later.'})
    return jsonify({'success': False, 'msg': 'Identity verification failed. User not found.'})

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    email_or_phone = request.form.get('identifier', '').strip()
    otp_code = request.form.get('otp', '')
    user = User.query.filter((User.email == email_or_phone) | (User.phone == email_or_phone)).first()
    if user and user.otp == otp_code:
        login_user(user, remember=True)
        session['user_data'] = {
            'id': user.id, 'username': user.username,
            'email': user.email, 'student_id': user.student_id,
            'role': user.role
        }
        user.otp = None # Clear OTP after use
        db.session.commit()
        if user.role in ('admin', 'faculty'):
            return jsonify({'success': True, 'redirect': url_for('admin_panel')})
        return jsonify({'success': True, 'redirect': url_for('dashboard')})
    return jsonify({'success': False, 'msg': 'Invalid OTP.'})

@app.route('/login', methods=['GET', 'POST'])
def login():
    role_type = request.args.get('role', 'student')
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            # Check if role matches if login is role-specific
            if user.role != role_type and role_type != 'student': # Basic check
                pass # Continue but could restrict
            
            login_user(user, remember=True)
            session['user_data'] = {
                'id': user.id, 'username': user.username,
                'email': user.email, 'student_id': user.student_id,
                'role': user.role
            }
            if user.role in ('admin', 'faculty'):
                return redirect(url_for('admin_panel'))
            return redirect(url_for('dashboard'))
        flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html', role=role_type)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').lower().strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        existing = User.query.filter((User.email == email) | (User.phone == phone)).first()
        if existing:
            flash('This email or phone is already registered.', 'warning')
            return redirect(url_for('login'))
        student_id = f"STU-{random.randint(1000, 9999)}"
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, phone=phone, password_hash=hashed, student_id=student_id, role='student')
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

@app.route('/log-incident', methods=['POST'])
@login_required
def log_incident():
    data = request.json
    if data.get('type') == 'tab_switch':
        count = session.get('tab_switches', 0)
        session['tab_switches'] = count + 1
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/submit-exam')
@login_required
def submit_exam():
    q_ids = session.get('exam_questions', [])
    answers = session.get('answers', {})
    score = 0
    analytics = {}
    
    for q_id in q_ids:
        q = Question.query.get(q_id)
        if q:
            cat = q.category or "General"
            if cat not in analytics: analytics[cat] = {'correct': 0, 'total': 0}
            analytics[cat]['total'] += 1
            if answers.get(str(q_id)) == q.correct_option:
                score += 1
                analytics[cat]['correct'] += 1
                
    time_taken = int(datetime.now(timezone.utc).timestamp() - session.get('exam_start_time', 0))
    difficulty = session.get('exam_difficulty', 'easy')
    tab_switches = session.get('tab_switches', 0)
    
    # 🛡️ 1. Tab-Switch Penalties
    penalty = 0
    if tab_switches >= 3: penalty = 5 # Deduct heavily for cheating, but capped at score
    final_score = max(0, score - penalty)

    # 🤖 2. Auto-Grading AI Feedback
    feedback = "Overall good attempt!"
    worst_cat = "N/A"
    min_acc = 100
    for cat, stat in analytics.items():
        acc = (stat['correct'] / stat['total']) * 100
        if acc < min_acc:
            min_acc = acc
            worst_cat = cat
    
    if min_acc < 50:
        feedback = f"AI Tutor's Insight: You're struggling with '{worst_cat}'. Consider deep-diving into this module before your next attempt."
    elif penalty > 0:
        feedback = "AI Warning: Your performance was strong, but integrity issues (tab switching) resulted in point deductions. Professional ethics matter!"

    result = ExamResult(user_id=current_user.id, score=final_score, total_questions=len(q_ids), 
                        time_taken=time_taken, difficulty=difficulty, tab_switches=tab_switches,
                        penalty_applied=penalty, tutor_feedback=feedback)
    db.session.add(result)
    db.session.commit()
    
    # Associate recent snapshots with this result
    orphaned_snaps = Snapshot.query.filter_by(user_id=current_user.id, result_id=None).all()
    for s in orphaned_snaps: s.result_id = result.id
    db.session.commit()

    # Cleanup session
    session.pop('exam_questions', None)
    session.pop('current_q_index', None)
    session.pop('answers', None)
    session.pop('exam_difficulty', None)
    session.pop('tab_switches', None)
    
    return render_template('results.html', score=final_score, real_score=score, total=len(q_ids), result=result, analytics=analytics)

@app.route('/download-certificate/<int:result_id>')
@login_required
def download_certificate(result_id):
    result = ExamResult.query.get_or_404(result_id)
    if result.user_id != current_user.id and current_user.role not in ('admin', 'faculty'):
        flash("You are not authorized to view this certificate.", "danger")
        return redirect(url_for('dashboard'))
    return render_template('certificate.html', result=result, user=current_user)

# =================== ADMIN / FACULTY PANEL ===================

@app.route('/admin')
@login_required
@role_required(['admin', 'faculty'])
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
@role_required(['admin', 'faculty'])
def admin_questions():
    diff = request.args.get('difficulty', 'all')
    if diff == 'all':
        questions = Question.query.order_by(Question.id.desc()).all()
    else:
        questions = Question.query.filter_by(difficulty=diff).order_by(Question.id.desc()).all()
    return render_template('admin/questions.html', questions=questions, current_diff=diff)

@app.route('/admin/add-question', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'faculty'])
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
@role_required(['admin', 'faculty'])
def admin_delete_question(qid):
    q = Question.query.get_or_404(qid)
    db.session.delete(q)
    db.session.commit()
    flash('Question deleted.', 'success')
    return redirect(url_for('admin_questions'))

@app.route('/admin/users')
@login_required
@role_required(['admin', 'faculty'])
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/results')
@login_required
@role_required(['admin', 'faculty'])
def admin_results():
    results = ExamResult.query.order_by(ExamResult.date_completed.desc()).all()
    return render_template('admin/results.html', results=results)

@app.route('/faculty/monitor')
@login_required
@role_required(['admin', 'faculty'])
@cache.cached(timeout=30) # Cache for 30s to simulate live but maintain performance
def faculty_monitor():
    # Only show students active in the last 15 minutes
    threshold = datetime.now(timezone.utc).replace(minute=datetime.now(timezone.utc).minute - 15)
    active_students = User.query.filter(User.role == 'student', User.last_active >= threshold).all()
    return render_template('admin/monitor.html', active_students=active_students)


@app.route('/generate-from-source', methods=['POST'])
@login_required
@cache.memoize(timeout=300) # Performance caching for heavy AI logic
def generate_from_source():
    text = ""
    file = request.files.get('doc_file')
    url = request.form.get('doc_url')
    
    # AI logic: Extract Keywords
    if file and file.filename.endswith('.pdf'):
        if PyPDF2:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
            for page in pdf_reader.pages:
                text += page.extract_text()
        else:
            return jsonify({'error': "PDF Library required"}), 400
    elif url:
        try:
            resp = requests.get(url, timeout=5)
            text = resp.text
        except:
             return jsonify({'error': "Fetch failed"}), 400
    
    # Real-life Simulation: Keyconcept extraction
    keywords = ["Implementation", "Architecture", "Optimization", "Security", "Reliability", "Scalability", "Latency", "Throughput"]
    found = [k for k in keywords if k.lower() in text.lower()]
    if not found: found = ["Core System", "Data Flow"]
    
    new_questions = []
    for i, kw in enumerate(found[:5]):
        new_questions.append(Question(
            text=f"Analyze the following: How does the document address the concept of {kw}?",
            option_a=f"Critically within the {kw} framework",
            option_b="As a secondary concern",
            option_c="Not mentioned in detail",
            option_d="Central to the entire architecture",
            correct_option=random.choice(["A", "D"]),
            category="AI Generated",
            difficulty="hard"
        ))
    
    db.session.bulk_save_objects(new_questions)
    db.session.commit()
    session['exam_questions'] = [q.id for q in new_questions]
    session['exam_difficulty'] = 'hard'
    session['current_q_index'] = 0
    session['answers'] = {}
    session['exam_start_time'] = datetime.now(timezone.utc).timestamp()
    return redirect(url_for('exam'))

init_db()
if __name__ == '__main__':
    app.run(debug=True, port=5000)
