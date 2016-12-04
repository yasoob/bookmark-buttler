from flask import Flask, request, redirect, url_for, send_from_directory, render_template
from gevent.wsgi import WSGIServer
from selenium import webdriver
from urlparse import urlparse
from werkzeug.utils import secure_filename
import datetime
from celery import Celery
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.getcwd(),'remote_images')
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db_path = os.path.join(os.path.dirname(__file__), 'app.db')
db_uri = 'sqlite:///{}'.format(db_path)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

db = SQLAlchemy(app)

driver = webdriver.PhantomJS()
driver.set_window_size(1440, 768) # set the window size that you need 

@app.route("/")
def hello():
    all_results = Bookmark.query.all()
    return render_template('index.html', bookmarks = all_results)

@app.route("/book")
def book():
    remote_url = request.args.get('url','')
    all_results = Bookmark.query.all()
    
    if remote_url != '':
        if Bookmark.query.filter_by(url = remote_url).all() == []:
            driver.get(remote_url)
            title = driver.title
            favicon = "http://www.google.com/s2/favicons?domain="+remote_url
            domain = urlparse(remote_url).netloc.strip('www.')
            file_name = domain.strip('.com')+ ' ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '.png'
            filename_complete = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
            print filename_complete
            
            db.session.add(Bookmark(domain,title,remote_url,favicon,file_name))
            db.session.commit()
            
            driver.save_screenshot(filename_complete)
            return render_template('index.html', bookmarks = all_results)
        else:
            return render_template('index.html', bookmarks = all_results)    
            #return redirect(url_for('uploaded_file',
            #                            filename=file_name))
    return render_template('index.html', bookmarks = all_results)    


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(80), unique=True)
    title = db.Column(db.String(120), unique=True)
    url = db.Column(db.String(120), unique=True)
    favicon = db.Column(db.String(120), unique=True)
    filename = db.Column(db.String(120), unique=True)    

    def __init__(self, domain, title, url, favicon, filename):
        self.domain = domain
        self.title = title
        self.url = url
        self.favicon = favicon
        self.filename = filename

    def __repr__(self):
        return '<User %r>' % self.domain

db.create_all()

if __name__ == "__main__":
    #app.run()
    http_server = WSGIServer(('', 5000), app)
    http_server.serve_forever()

