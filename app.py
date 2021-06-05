import secrets
import time
from flask import Flask,request,session,url_for,redirect,flash,abort,send_file,time
from flask.templating import render_template
import requests
from functools import wraps
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
import os,shutil
from werkzeug.utils import secure_filename
from pdf_gen import pdfgen
from wordgen import docxGen
from flask_mail import Mail, Message
from datetime import datetime
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, __version__

app = Flask(__name__)
app.secret_key = os.urandom(24)
mysql = MySQL()


#file upload config
app.config['MAX_CONTENT_LENGTH'] = 10024 * 1024 #10mb
app.config['UPLOAD_EXTENSIONS'] = ['.pdf','.docx']
app.config['UPLOAD_PATH'] = os.path.join('static','files')

##Database configuration
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#Mail server configuration
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = '587'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
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

#dependencies()


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404


def upload_file_azure(file_name,file_path):
    connect_str = os.environ.get('storage_key')
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_name = 'userfiles'
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
    with open(file_path, "rb") as data:
        blob_client.upload_blob(data)



def delete_file_azure(file_name):
    connect_str = os.environ.get('storage_key')
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_name = 'userfiles'
    container_client = blob_service_client.get_container_client(container_name)
    print(file_name)
    blob_client = container_client.get_blob_client("___".join([str(session['uid']),'original',file_name]))
    blob_client.delete_blob()
    blob_client = container_client.get_blob_client("___".join([str(session['uid']),'generated',file_name]))
    blob_client.delete_blob()
    return redirect(url_for('home'))

@app.route('/track')
def hello_world():
    city=""
    host=""
    country=""
    state=""
    city=""
    postal=""
    long,lat="",""
    if request.args.get('ip'):
        ip=request.args.get('ip')
    else:
        ip = request.headers.getlist("X-Forwarded-For")[0]
    #userDeviceInfo=request.args.get('data')
    userDeviceInfo=str(request.headers.get('User-Agent'))
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
    cur2.execute("SELECT email,name,notification From users where id=(select userid from files where token=%s)",[token])
    d=cur2.fetchone()
    cur2.close()
    cur3=mysql.connection.cursor()
    cur3.execute("SELECT filename from files where token=%s",[token])
    e=cur3.fetchone()
    cur3.close()
    filename=e['filename']
    email=d['email']
    name=d['name']
    notification=d['notification']
    if notification:
        msg = Message(f"Your file {filename} was accessed", sender='projecthandbloom@gmail.com', recipients=[email])
        msg.body =f"Hello {name} , your file {e['filename']} was accessed by {ip} on {time} for more details visit https://tracki-file.azurewebsites.net"
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
                session['email'] = data['email']
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
    for file in files:
        file['ext']=file['filename'].split(".")[1]
    return render_template('home.html',files=files)

@app.route('/upload', methods = ['GET', 'POST'])
@is_logged_in
def upload_file():
    if request.method == 'POST':
        uploaded_file  = request.files['file']
        filename = secure_filename(uploaded_file.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            path = os.path.join(app.config['UPLOAD_PATH'])
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                flash('File not supported', 'Danger')
                return redirect(url_for('/'))
            #file_path = os.path.join(os.getcwd(),path, filename)
            uploaded_file.save(filename)
            token = secrets.token_hex(nbytes=16)
            file_ext=filename.split(".")[1]
            uid=str(session['uid'])
            original_file_name="___".join([uid,'original',filename])
            generated_file_name = "___".join([uid, 'generated',filename])
            size = os.stat(filename).st_size
            upload_file_azure(original_file_name,filename)
            flag=0
            if file_ext=='pdf':
                script_path = 'pdf_gen'
                shutil.move(filename, script_path)
                os.chdir(script_path)
                flag=1
                template = """"   <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js"></script>
       <script>
        var ip="";
        window.addEventListener('load',function () {
        $.getJSON("https://api.ipify.org?format=json",
                        function(data) {
    
          // Setting text of element P with id gfg
          location.replace("https://tracki-file.azurewebsites.net/track?token=%s&&ip="+data.ip);
        })
         })
       </script>"""%(token)

                with open('template.html','w') as htmlfile:
                    htmlfile.write(template)
                pdfgen.start(filename)
                time.sleep(1)
                os.remove(filename+".zip")
                upload_file_azure(generated_file_name, filename)
                os.remove(filename)


            elif file_ext=='docx':
                #generating file
                shutil.move(filename, 'wordgen')
                os.chdir('wordgen')
                flag=1
                docxGen.wordgen(token,filename)
                os.rename('generated.zip',filename)
                upload_file_azure(generated_file_name, filename)
                os.remove(filename)


            if flag:
                os.chdir("..")



            else:
                flash('File not supported', 'danger')
                return redirect(url_for('/'))

            # updating database
            curs = mysql.connection.cursor()
            curs.execute(
                "INSERT INTO files(token,userid,filename,filesize) VALUES(%s, %s, %s,%s)",
                (token,uid,filename,size))
            mysql.connection.commit()
            curs.close()
        flash('File Uploaded Sucessfully', 'success')
        return redirect(url_for('home'))

@app.route('/download', methods=['GET', 'POST'])
@is_logged_in
def download():
    if request.method == 'GET':
        filename = request.args.get('filename')
        tempname = filename.split("___")[2]
        if filename.split("___")[0]==str(session['uid']):
            if os.path.isdir('file'):
                shutil.rmtree('file')
            os.mkdir('file')
            connect_str = os.environ.get('storage_key')
            blob_service_client = BlobServiceClient.from_connection_string(connect_str)
            container_name='userfiles'
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=filename)
            with open('file/'+tempname, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())
            return send_file('file/'+tempname,attachment_filename=tempname,as_attachment=True)
    flash("Something went wrong",'danger')
    return render_template('home.html')
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
        delete_file_azure(filename)
        curs = mysql.connection.cursor()
        curs = mysql.connection.cursor()
        curs.execute("DELETE from files where filename=%s", [filename])
        mysql.connection.commit()
        curs.close()
        flash('File Deleted Sucessfully', 'success')
    return redirect(url_for('home'))

@app.route('/out')
@is_logged_in
def logout():
    if 'uid' in session:
        # Create cursor
        session.clear()
        flash('You are logged out', 'success')
        return redirect(url_for('login'))
    return redirect(url_for('login'))

@app.route('/settings',methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        name = request.form.get('name')
        email = request.form.get('email')
        notification=0
        if request.form.get('notification')=='on':
            notification=1
        uid=session['uid']
        sql = f"SELECT * FROM users WHERE email='{email}' and id<>{uid}"
        result = cur.execute(sql)
        if result>0:
            flash("email already exist",'danger')
            return redirect(url_for('settings'))
        else:
            cur2=mysql.connection.cursor()
            password = sha256_crypt.encrypt(request.form.get('password'))
            sql = f"UPDATE users SET name='{name}' , email='{email}',password='{password}',notification={notification} WHERE id={uid}"
            cur2.execute(sql)
            mysql.connection.commit()
            cur2.close()
            flash("Update Success",'success')
            return redirect(url_for('settings'))

        return render_template('settings.html')
    return render_template('settings.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)
