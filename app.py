from flask import Flask,request,session,url_for,redirect,flash
from flask.templating import render_template
import json
import requests
from functools import wraps
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.urandom(24)
mysql = MySQL()


app.config['UPLOAD_FOLDER']='static/files'
app.config['MAX_CONTENT_PATH']='10485760'

##Database configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'project'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql.init_app(app)



@app.route('/track')
def hello_world():
    ip=request.args.get('ip')
    print(ip)
    url = f'http://ipinfo.io/{ip}?token=91ad2d6d618ec3'
    response = requests.get(url=url)
    data = response.json()
    print(data)
    return "<script>window.close()</script>"

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, *kwargs)
        else:
            return redirect(url_for('login'))

    return wrap

def not_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return redirect(url_for('home'))
        else:
            return f(*args, *kwargs)

    return wrap

def wrappers(func, *args, **kwargs):
    def wrapped():
        return func(*args, **kwargs)

    return wrapped


@app.route('/login', methods=['GET', 'POST'])
@not_logged_in
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password_candidate = request.form.get('pass')
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM users WHERE username=%s", [username])
        if result > 0:
            data = cur.fetchone()
            password = data['password']
            uid = data['id']
            name = data['name']
            print(password)
            print(password_candidate)
            print(sha256_crypt.verify(password_candidate, password))
            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['uid'] = uid
                session['s_name'] = name
                return redirect(url_for('home'))
            else:
                flash('Incorrect password', 'danger')
                return render_template('login.html')
        else:
            flash('User not found', 'danger')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
@not_logged_in
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        username = request.form.get('username')
        print(request.form.get('pass'))
        password = sha256_crypt.encrypt(request.form.get('pass'))
        curs = mysql.connection.cursor()
        if curs.execute("SELECT * FROM users WHERE email=%s", [email]) >= 1:
            flash('Email Already exist', 'danger')
            return redirect(url_for('register'))
        elif curs.execute("SELECT * FROM users WHERE username=%s", [username]) >= 1:
            flash('Username Already exist', 'danger')
            return redirect(url_for('register'))

        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)",
            (name, email, username, password))
        mysql.connection.commit()
        cur.close()

        flash('You are sucessfully registered.You can login now', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/home')
#@is_logged_in
def home():
    return render_template('home.html')

@app.route('/upload', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        f.save(secure_filename(f.filename))
        return 'file uploaded successfully'

if __name__ == '__main__':
    app.run()
