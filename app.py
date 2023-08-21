import glob
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session  # Import jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
from whoosh.query import Wildcard
import docx2txt
import os
import re
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random
from flask_mail import Mail, Message

# Initialize Flask app and configure it
app = Flask(__name__, template_folder='')
app.config['SECRET_KEY'] = 'KZ15igLRGYgNv9CtBu_Cqm8eDKN9eAMmA6v0'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['MAIL_SERVER'] = 'smtp.office365.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'rplcpsd@outlook.com'
app.config['MAIL_PASSWORD'] = 'Iquasar@123'
app.config['MAIL_DEFAULT_SENDER'] = ('outlook.com', 'rplcpsd@outlook.com')
mail = Mail(app)

# Initialize SQLAlchemy and LoginManager
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

ix = open_dir("index")

# Define User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    verification_code = db.Column(db.String(6))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index.html'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login.html'))

# Define route for registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index.html'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different username.', 'danger')
            return redirect(url_for('register.html'))

        # Generate a random 6-digit verification code
        verification_code = str(random.randint(100000, 999999))

        # Hash the password
        hashed_password = generate_password_hash(password, method='sha256')

        # Store the verification code in the session for verification
        session['verification_code'] = verification_code
        # Store the hashed password in the session for use in the /verify route
        session['temp_hashed_password'] = hashed_password

        # Send verification code via email
        send_verification_email(username, verification_code)

        return redirect(url_for('verify', username=username))

    return render_template('register.html')




# Function to send verification email
def send_verification_email(username, verification_code):
    recipient_email = 'shawn.baba@iquasar.com'

    subject = 'Verification Code'
    message = f'Your verification code is: {verification_code}'

    msg = Message(subject=subject, recipients=[recipient_email])
    msg.body = message

    try:
        mail.send(msg)
        print('Email sent successfully')
    except Exception as e:
        print('Error sending email:', e)

 #Define route for email verification
@app.route('/verify/<username>', methods=['GET', 'POST'])
def verify(username):
    stored_code = session.get('verification_code')

    if request.method == 'POST':
        entered_code = request.form['verification_code']

        if entered_code == stored_code:
            # Clear the session data
            session.pop('verification_code', None)

            # Retrieve the hashed password from the session
            hashed_password = session.get('temp_hashed_password')

            # Create the new user
            user = User(username=username, password_hash=hashed_password, verification_code=entered_code)
            db.session.add(user)
            db.session.commit()

            flash('Verification successful! You can now log in.', 'success')
            return redirect(url_for('login.html'))
        else:
            flash('Invalid verification code. Please try again.', 'danger')

    return render_template('verify.html', username=username)

@app.route('/search')
def search():
    query = request.args.get('query', '')

    with ix.searcher() as searcher:
        title_query_parser = QueryParser("title", ix.schema)
        wildcard_query = Wildcard("title", f"*{query}*")  # Add this line for wildcard title suggestions
        title_query = title_query_parser.parse(query) | wildcard_query  # Combine regular and wildcard title queries
        title_results = searcher.search(title_query, limit=5)
        title_suggestions = [hit['title'] for hit in title_results]

        if title_suggestions:
            return jsonify(title_suggestions)
        else:
            return jsonify({'paragraphs': []})

@app.route('/get_text')
def get_text():
    selected_title = request.args.get('title', '')
    with ix.searcher() as searcher:
        query_parser = QueryParser("title", ix.schema)
        query = query_parser.parse(selected_title)
        results = searcher.search(query)
        if results:
            first_result = results[0]
            docx_path = os.path.join("data", first_result['title'])
            document_content = docx2txt.process(docx_path)
            return jsonify({'content': document_content})
        else:
            return jsonify({'content': ''})



# Update app.py
TEXT_FILES_DIR = "data_repository_search_engine/data/Text"

@app.route('/search_keywords')
def search_keywords():
    keyword = request.args.get('keyword', '').lower()

    matching_paragraphs = []

    # Search for matching paragraphs in text files
    for txt_file_path in glob.glob(os.path.join(TEXT_FILES_DIR, "*.txt")):
        with open(txt_file_path, 'r', encoding='utf-8') as txt_file:
            content = txt_file.read()
            paragraphs = content.split("\n\n")
            for paragraph in paragraphs:
                if keyword in paragraph.lower():
                    matching_paragraphs.append({'content': paragraph})

    return jsonify({'paragraphs': matching_paragraphs})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
