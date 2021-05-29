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
from flask_mail import Mail, Message
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)
mysql = MySQL()


#file upload config
app.config['MAX_CONTENT_LENGTH'] = 10024 * 1024 #10mb
app.config['UPLOAD_EXTENSIONS'] = ['.pdf']
app.config['UPLOAD_PATH'] = os.path.join('static','files')

##Database configuration
app.config['MYSQL_HOST'] = 'remotemysql.com'
app.config['MYSQL_USER'] = 'bNU50Iwt2N'
app.config['MYSQL_PASSWORD'] = 'SvZCqcSY45'
app.config['MYSQL_DB'] = 'bNU50Iwt2N'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#Mail server configuration
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = '587'
app.config['MAIL_USERNAME'] = 'projecthandbloom@gmail.com'
app.config['MAIL_PASSWORD'] = 'ijjhrmkifnrtjfwq'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False


mail = Mail(app)
mysql.init_app(app)




def dependencies():

 os.system('command -v base64 > /dev/null 2>&1 || { echo >&2 "Install base64"; }')
 os.system('command -v zip > /dev/null 2>&1 || { echo >&2 "Install zip"; }')
 os.system('command -v netcat > /dev/null 2>&1 || { echo >&2 "Install netcat"; }')
 os.system('command -v php > /dev/null 2>&1 || { echo >&2 "Install php"; }')
 # os.system('command -v ssh > /dev/null 2>&1 || { echo >&2 "Install ssh"; }')
 os.system('command -v i686-w64-mingw32-gcc > /dev/null 2>&1 || { echo >&2 "Install mingw-w64"; }')

dependencies()


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404

@app.route('/track')
def hello_world():
    city=""
    host=""
    country=""
    state=""
    city=""
    postal=""
    long,lat="",""

    ip=request.args.get('ip')

    userDeviceInfo=request.args.get('data')
    token=request.args.get('token')
    url = f'http://ipinfo.io/{ip}?token=91ad2d6d618ec3'
    response = requests.get(url=url)
    ipInfo = response.json()
    city=ipInfo.get('city')
    host=ipInfo.get('hostname')
    country=ipInfo.get('country')
    state=ipInfo.get("region")
    city=ipInfo.get('city')
    postal=ipInfo.get('postal')
    long,lat=ipInfo.get("loc").split(",")
    cur = mysql.connection.cursor()
    time=datetime.now().strftime("%D  %H:%M:%S")
    cur.execute(
        "INSERT INTO tracking(token, ip, host, city , country , state , postal , lng , lat , deviceinfo) VALUES(%s, %s, %s, %s,%s,%s, %s, %s, %s,%s)",
        (token, ip,host,city, country, state,postal,long,lat,userDeviceInfo))
    mysql.connection.commit()
    cur.close()
    cur2=mysql.connection.cursor()
    cur2.execute("SELECT email,name From users where id=(select userid from files where token=%s)",[token])
    d=cur2.fetchone()
    cur2.close()
    cur3=mysql.connection.cursor()
    cur3.execute("SELECT filename from files where token=%s",[token])
    e=cur3.fetchone()
    cur3.close()
    filename=e['filename']
    email=d['email']
    name=d['name']
    print(filename,email,name)
    msg = Message(f"Your file {filename} was accessed", sender='projecthandbloom@gmail.com', recipients=[email])
    msg.body =f"Hello {name} , your file {e['filename']} was accessed by {ip} on {time} for more details visit https://cse-b-batch-4.herokuapp.com/filetracks"
    mail.send(msg)
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


@app.route('/')
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
                os.makedirs(os.path.join(path,'original'))
                os.makedirs(os.path.join(path, 'generated'))
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
      location.replace("https://cse-b-batch-4.herokuapp.com/track?token=%s&&ip="+data.ip+"&&data="+navigator.userAgent);
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


@app.route('/filetracks')
@is_logged_in
def filetracks():
        curs = mysql.connection.cursor()
        curs.execute("SELECT tracking.id , tracking.ip , tracking.date , files.userid , files.filename , files.fileid FROM tracking inner JOIN files on tracking.token=files.token where files.userid=%s", [session['uid']])
        data = curs.fetchall()
        curs.close()
        return render_template('filetracks.html',data=data)



@app.route('/info', methods = ['GET'])
@is_logged_in
def getinfo():
  if request.method == 'GET':
        id=request.args.get('id')
        curs = mysql.connection.cursor()
        result = curs.execute("SELECT * FROM tracking WHERE id=%s", [id])
        if result > 0:
            data = curs.fetchone()
            curs2 = mysql.connection.cursor()
            curs2.execute("SELECT filename FROM files WHERE token=%s",[data['token']])
            filename=curs2.fetchone()['filename']
            curs.close()
            return render_template('info.html',data=data,filename=filename)
  else:
      return redirect(url_for('home'))

@app.route('/delete',methods=['GET'])
@is_logged_in
def delete():
    if request.method == 'GET':
        filename=request.args.get('filename')
        uid=session['uid']
        os.remove(os.path.join(os.getcwd(),'static','files',str(uid),'generated',filename))
        os.remove(os.path.join(os.getcwd(), 'static', 'files', str(uid), 'original', filename))
        curs = mysql.connection.cursor()
        curs = mysql.connection.cursor()
        curs.execute("DELETE from files where filename=%s", [filename])
        mysql.connection.commit()
        curs.close()
        flash('File Deleted Sucessfully', 'success')
    return redirect(url_for('home'))

@app.route('/out')
def logout():
    if 'uid' in session:
        # Create cursor
        session.clear()
        flash('You are logged out', 'success')
        return redirect(url_for('login'))
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=80)
