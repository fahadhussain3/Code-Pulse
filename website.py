import pymysql
pymysql.install_as_MySQLdb()

import json
import math
from flask import Flask, render_template, request,session,redirect
from flask_mail import Mail, Message  # Import Message class
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Getting the data of JSON file
with open('config.json', 'r') as f:
    parameter = json.load(f)["params"]

app = Flask(__name__)

# we have to create the secret key for session
app.secret_key = 'super-secret-key'

app.config.update(
    MAIL_SERVER='smtp.office365.com',  # Use 'smtp.office365.com' for Office 365
    MAIL_PORT=587,  # Use port 587 for TLS
    MAIL_USE_TLS=True,  # Use TLS (not SSL)
    MAIL_USERNAME=parameter['outlook_username'],  # Update to match your Outlook username
    MAIL_PASSWORD=parameter['outlook_password']  # Update to match your Outlook password
)
mail = Mail(app)

if parameter['localhost'] == "True":  # Note: 'True' is a string in your JSON
    # Here we are connecting with the database:
    app.config['SQLALCHEMY_DATABASE_URI'] = parameter['local_url']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = parameter['production_url']

db = SQLAlchemy(app)

# Now we are accessing the table from the database which we have to use here Contacts:
class Contacts(db.Model):
    # We have to write same names and types etc that are used in the database table:
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    message = db.Column(db.String(1000), nullable=False)
    date = db.Column(db.DateTime, nullable=True)


class Posts(db.Model):
    # We have to write same names and types etc that are used in the database table:
    sno = db.Column(db.Integer, primary_key=True)
    post_title = db.Column(db.String(100), nullable=False)
    post_desc = db.Column(db.String(1000), nullable=False)
    content=db.Column(db.String(100),nullable=False)
    post_slug = db.Column(db.String(30), nullable=False)
    date = db.Column(db.DateTime, nullable=True)

@app.route('/')
def home():
    # Here we are getting all the posts
    psts=Posts.query.filter_by().all()

    # Finding how many pages will be
    last = math.ceil(len(psts) / int(parameter['no_of_post_on_homepage']))
    # checking the page number from url
    page=(request.args.get('page'))

    # if nothing then we will assign it as first
    if (not str(page).isnumeric()):
        page = 1
    
    page=int(page)
    # Filtring the post acording to the number of post we want to show on single page
    psts = psts[(page-1)*int(parameter['no_of_post_on_homepage']):(page-1)*int(parameter['no_of_post_on_homepage'])+ int(parameter['no_of_post_on_homepage'])]

    # Kind of generating url for buttons...
    if page==1 and last==1:
        prev = "#"
        next = "#"
    elif page==1:
        prev = "#"
        next = "/?page="+ str(page+1)
    elif page==last:
        prev = "/?page="+ str(page-1)
        next = "#"
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page="+ str(page+1)
    return render_template('index.html', passing_params=parameter, passingposts=psts,previous=prev,Next=next)


@app.route("/post/<string:slug_url>", methods=['GET'])

def post(slug_url):
    mypost = Posts.query.filter_by(post_slug=slug_url).first()
    return render_template('post.html', passing_params=parameter,pasing_post=mypost)



@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        '''Add entry to the database'''
        # We are getting this info from the user and through POST request and adding to the table in the database
        enterd_name = request.form.get('Name')
        enterd_email = request.form.get('Email')
        enterd_phone = request.form.get('Phone')
        enterd_message = request.form.get('Message')
        entry = Contacts(name=enterd_name, email=enterd_email, phone=enterd_phone, message=enterd_message, date=datetime.now())
        db.session.add(entry)
        db.session.commit()

        # Use Message class to send email
        msg = Message(
            'New Message From ' + enterd_name,
            sender=parameter['outlook_username'],  # Sender should be your email address
            recipients=[parameter['outlook_username']],  # Make sure recipients is a list
            body=enterd_message + "\n" + enterd_phone
        )
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Error sending email: {e}")

    return render_template('contact.html', passing_params=parameter)



@app.route('/about')
def about():
    return render_template('about.html', passing_params=parameter)


@app.route('/signin',methods=['GET', 'POST'])
def signin():
    psts=Posts.query.filter_by().all()
    # to check if admin is already loggedin:
    if "user" in session and session['user']==parameter['signin_email'] and session['password']==parameter['sigin_password']:
            return render_template("dashboard.html", passing_params=parameter,passingposts=psts)
    
    if request.method=="POST":
        entered_signin_mail=request.form.get('email')
        entered_signin_password=request.form.get('Password')

        if entered_signin_mail==parameter['signin_email'] and entered_signin_password==parameter['sigin_password']:

            # setting session like we do in php
            session['user']=entered_signin_mail
            session['password']=entered_signin_password
            return render_template("dashboard.html", passing_params=parameter,passingposts=psts)
        
        
        
    return render_template('signin.html', passing_params=parameter)


@app.route("/edit/<string:sno>", methods=['GET', 'POST'])

def edit(sno):
    if "user" in session and session['user']==parameter['signin_email'] and session['password']==parameter['sigin_password']:
            if request.method=="POST":
                enterd_title = request.form.get('title')
                enterd_desc = request.form.get('desc')
                enterd_content = request.form.get('content')
                enterd_slug = request.form.get('slug')
                enterd_imgurl = request.form.get('imgurl')
                if(sno=='0'):
                    add_post=Posts(post_title=enterd_title, post_desc=enterd_desc, content=enterd_content, post_slug=enterd_slug, date=datetime.now())
                    db.session.add(add_post)
                    db.session.commit()
                    return redirect('/signin')

                else:
                    mypost = Posts.query.filter_by(sno=sno).first()
                    mypost.post_title = enterd_title
                    mypost.post_desc = enterd_desc
                    mypost.content = enterd_content
                    mypost.post_slug = enterd_slug
                    mypost.date = datetime.now()
                    db.session.commit()
                    return redirect('/signin')

            pst = Posts.query.filter_by(sno=sno).first()
            return render_template('edit.html', passing_params=parameter,pasing_post=pst,serialno=sno)
    

@app.route('/logout')
def logout():
    if "user" in session and session['user']==parameter['signin_email'] and session['password']==parameter['sigin_password']:
        session.pop('user')
        session.pop('password')
        return redirect('/signin')


@app.route("/delete/<string:sno>", methods=['GET'])

def delete(sno):
    if "user" in session and session['user']==parameter['signin_email'] and session['password']==parameter['sigin_password']:
        post=Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
        return redirect('/signin')
if __name__ == '__main__':
    app.run(debug=True)
