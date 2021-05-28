import secrets

from flask import Flask,request,session,url_for,redirect,flash,abort
from flask.templating import render_template
import json
import requests
from functools import wraps
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
import os,shutil
from werkzeug.utils import secure_filename
from pdf_gen import pdfgen

app = Flask(__name__)
app.secret_key = os.urandom(24)
mysql = MySQL()


#file upload config
app.config['MAX_CONTENT_LENGTH'] = 10024 * 1024 #10mb
app.config['UPLOAD_EXTENSIONS'] = ['.pdf']
app.config['UPLOAD_PATH'] = os.path.join('static','files')

##Database configuration
app.config['MYSQL_HOST'] = '0.0.0.0'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'project'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql.init_app(app)



@app.route('/track')
def hello_world():
    ip=request.args.get('ip')
    userDeviceInfo=request.args.get('data')
    token=request.args.get('token')
    url = f'http://ipinfo.io/{ip}?token=91ad2d6d618ec3'
    response = requests.get(url=url)
    ipInfo = response.json()
    print(token)
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
@is_logged_in
def home():
    files=[]
    curs = mysql.connection.cursor()
    result = curs.execute("SELECT * FROM files WHERE userid=%s", [session['uid']])
    if result > 0:
        files=curs.fetchall()

    return render_template('home.html',files=files)

@app.route('/upload', methods = ['GET', 'POST'])
@is_logged_in
def upload_file():
    if request.method == 'POST':
        uploaded_file  = request.files['file']
        filename = secure_filename(uploaded_file.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            path = os.path.join(app.config['UPLOAD_PATH'],str(session['uid']),)
            if not os.path.exists(path):
                os.makedirs(path)
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)
            uploaded_file.save(os.path.join(path,'original' ,filename))

            org_path = os.path.join(os.getcwd(),'static','files',str(session['uid']),'original')
            gen_path = os.path.join(os.getcwd(),'static','files',str(session['uid']),'generated')
            script_path = os.path.join(os.getcwd(), 'pdf_gen')

            print(org_path)
            print(script_path)
            shutil.copy(os.path.join(org_path,filename), script_path)
            #uploaded_file.save(os.path.join(script_path,filename))

            os.chdir(script_path)
            token=secrets.token_hex(nbytes=16)
            template = """"   <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js"></script>
   <script>
    var ip="";
    window.addEventListener('load',function () {
    $.getJSON("https://api.ipify.org?format=json",
                    function(data) {

      // Setting text of element P with id gfg
      location.replace("http:127.0.0.1:5000/track?token=%s&?ip="+data.ip+"&?data="+navigator.userAgent);
    })
   //location.replace("http:127.0.0.1:5000?ip="+ip);
     })
   </script>"""%(token)

            with open('template.html','w') as htmlfile:
                htmlfile.write(template)
            pdfgen.start(filename)
            shutil.copy(filename,gen_path)
            os.remove(filename)
            os.chdir('..')
            #print(gen_path)
            curs = mysql.connection.cursor()
            curs.execute(
                "INSERT INTO files(token,userid, original_filepath,generated_filepath, filename) VALUES(%s, %s, %s,%s,%s)",
                (token,session['uid'],os.path.join(path,'original',filename),os.path.join(path,'generated',filename),filename))
            mysql.connection.commit()
            curs.close()
        flash('File Uploaded Sucessfully', 'success')
        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run()
