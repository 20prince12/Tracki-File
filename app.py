from flask import Flask,request
from flask.templating import render_template
import json
import requests




app = Flask(__name__)


@app.route('/')
def hello_world():
    ip=request.args.get('ip')
    print(ip)
    url = f'http://ipinfo.io/{ip}?token=91ad2d6d618ec3'
    response = requests.get(url=url)
    data = response.json()
    print(data)
    return "<script>window.close()</script>"


if __name__ == '__main__':
    app.run()
