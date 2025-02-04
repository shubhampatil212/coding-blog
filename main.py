from flask import Flask, redirect, render_template, request, session, url_for  # Import request for form handling
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from flask_mail import Mail
import json, math

local_server = True
with open('templates/config.json', 'r') as c:
    params = json.load(c)["params"]


app = Flask(__name__)
app.secret_key = "super secret key"

app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']
)
mail = Mail(app)


if local_server:
    app.config["SQLALCHEMY_DATABASE_URI"] = params["local_uri"]
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params["prod_uri"]
db = SQLAlchemy(app)

class Contacts(db.Model):
    sno: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_num: Mapped[str] = mapped_column(String(15), nullable=False)
    msg: Mapped[str] = mapped_column(String(500), nullable=False)
    date: Mapped[str] = mapped_column(String(50), nullable=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False)

class Post(db.Model):
    sno: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    tagline: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(15), nullable=False)
    content: Mapped[str] = mapped_column(String(500), nullable=False)
    date: Mapped[str] = mapped_column(String(50), nullable=True)
    # email: Mapped[str] = mapped_column(String(100), nullable=False)


@app.route("/dashboard", methods=['GET','POST'])
def dashboard():        
    if ('user' in session and session['user']==params['admin_user']):
        posts = Post.query.all()
        return render_template('dashboard.html', params=params, posts = posts)
    
    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username==params['admin_user'] and userpass==params['admin_password']):
            posts = Post.query.all()
            session['user'] = username
            return render_template('dashboard.html',params=params, posts=posts)
        
    return render_template("login.html",params=params)

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/dashboard")

@app.route("/delete/<string:sno>", methods=['GET', 'POST'])
def delete(sno):
    if ('user' in session and session['user']==params['admin_user']):
        posts = Post.query.filter_by(sno=sno).first()
        db.session.delete(posts)
        db.session.commit()
    return redirect("/dashboard")
    
# @app.route("/")
# def home():
#     posts = Post.query.filter_by().all()[0:params['no_of_posts']]
#     return render_template('index.html', params=params, posts=posts)

#Check later this block
@app.route("/")
def home():
    posts = Post.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])]
    if page==1:
        prev = "#"
        next = "/?page="+ str(page+1)
    elif page==last:
        prev = "/?page="+ str(page-1)
        next = "#"
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page="+ str(page+1)
    
    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)

@app.route("/about")
def about():
    return render_template("about.html",params=params)

@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Post.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)

@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if request.method == 'POST':
        '''Add entry to the databases'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry1 = Contacts(name = name, phone_num = phone, msg = message, email = email, date= datetime.now())
        db.session.add(entry1)
        db.session.commit()
        mail.send_message('New message from ' + name,
                          sender=email,
                          recipients=[params['gmail-user']],
                          reply_to=email,
                          body=f"{message} \nPhone:- {phone}"
                          )
    return render_template("contact.html", params=params)

@app.route("/post")
def post_list():
    posts = Post.query.filter_by().all()
    return render_template('post_list.html', params=params, posts=posts)

@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):
    if "user" in session and session['user']==params['admin_user']:
        if request.method=="POST":
            title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            date = datetime.now()
        
            if sno=='0':
                try:
                    post = Post(title=title, tagline=tline, slug=slug, content=content, date=date)
                    db.session.add(post)
                    db.session.commit()
                    # return redirect(f'/post/post-{slug}')
                    return redirect(f'/dashboard')
                except Exception as e:
                    print("Error adding post:", e)
                    db.session.rollback()
                    return "Error adding post"
            else:
                post = Post.query.filter_by(sno=sno).first()
                post.title = title   
                post.tagline = tline   
                post.slug = slug 
                post.content= content   
                # post.title = title
                db.session.commit()
                return redirect(f'/dashboard')
                # return redirect(sno)   
            
    post = Post.query.filter_by(sno=sno).first()
    return render_template('edit.html', params=params, post=post)
 
app.run(debug=True)

