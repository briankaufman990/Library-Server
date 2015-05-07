from flask import Flask, render_template, request, url_for, redirect
from os import getcwd
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
from flask_mail import Message
from wtforms import Form, BooleanField, TextField, IntegerField, SubmitField, BooleanField, validators
from flask_wtf.html5 import DateField
from flask.ext.sqlalchemy import SQLAlchemy
import flask.ext.whooshalchemy
from flask_mail import Mail
from flask.ext.security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required, roles_required, current_user
import logging
logging.basicConfig()
    
# Create app
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'even-more-secret-than-that'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['WHOOSH_BASE'] = getcwd()+'/whoosh_index'
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_RECOVERABLE'] = True
app.config['SECURITY_CONFIRMABLE'] = True
app.config['SECURITY_CHANGEABLE'] = True
app.config['SECURITY_PASSWORD_HASH'] = 'pbkdf2_sha512'
app.config['SECURITY_PASSWORD_SALT'] = '$2a$16$Pnn(p$lIgfMagrkO@jGX4SkHqkjblBKPO'
app.config['SECURITY_POST_LOGIN_VIEW'] = '/profile'



app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
#app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'brianhyomin@gmail.com'
app.config['MAIL_PASSWORD'] = 'testpass'
mail = Mail(app)

# Create database connection object
db = SQLAlchemy(app)

# Define models
roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    __searchable__ = ['email']
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(140), unique=True)
    password = db.Column(db.String(140))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    
    books = db.relationship('Book', backref='holder', lazy='dynamic')
    
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
                            
class Book(db.Model):
    __searchable__ = ['title', 'author']

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(140))
    author = db.Column(db.String(140))
    ISBN = db.Column(db.Integer)
    return_date = db.Column(db.Date)
    
flask.ext.whooshalchemy.whoosh_index(app, Book)
flask.ext.whooshalchemy.whoosh_index(app, User)

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


def send_notice():
    
    #sending notifications to users
    
    due_in_week = Book.query.filter_by(return_date= (datetime.date.today()+datetime.timedelta(days=7)) ).all()
    for book in due_in_week:
        msg = Message('Return Date Reminder', sender = 'brianhyomin@gmail.com', recipients=[book.holder.email])
        msg.body = book.title+' is due back at the library in a week. Thank you!'
        with app.app_context():
            mail.send(msg)
        
        
    due_tomorrow = Book.query.filter_by(return_date= (datetime.date.today()+datetime.timedelta(days=1)) ).all()
    for book in due_tomorrow:
        msg = Message('Return Date Reminder', sender = 'brianhyomin@gmail.com', recipients=[book.holder.email])
        msg.body = book.title+' is due back at the library tomorrow. Thank you!'
        with app.app_context():
            mail.send(msg)
    
    overdue = Book.query.filter(Book.return_date < datetime.date.today()).all()
    for book in overdue:
        msg = Message('Overdue Book', sender = 'brianhyomin@gmail.com', recipients=[book.holder.email])
        msg.body = book.title+' is overdue. Please return it!'
        with app.app_context():
            mail.send(msg)
    
    
from apscheduler.triggers.cron import CronTrigger

@app.before_first_request
def schedule_notices():
    sched = BackgroundScheduler()
    sched.start()


    trigger = CronTrigger(day_of_week='*', hour=17)
    sched.add_job(send_notice, trigger)





# Views
@app.route('/profile')
@login_required
def profile():
    user_books = current_user.books.all()
    return render_template('profile.html',user=current_user,books=user_books)
  
    
class SearchBooksForm(Form):
    search = TextField('Title/Author', [validators.Length(min=1, max=35)])    
  
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    library = user_datastore.get_user('admin')
    books=library.books.all()
    form = SearchBooksForm(request.form)
    if request.method == 'POST' and form.validate():
        books = Book.query.whoosh_search('*'+form.search.data+'*').filter_by(user_id=library.id).all()
    return render_template('index.html',user=library,books=books,form=form)

class NewLibrarianForm(Form):
    email = TextField('Email Address', [validators.Length(min=1, max=35)])
    confirm = BooleanField('Confirm Email?')

@login_required
@roles_required('library_admin')   
@app.route('/new_librarian', methods=['GET', 'POST'])
def new_librarian():
    form = NewLibrarianForm(request.form)
    if request.method == 'POST' and form.validate():
        if form.confirm.data:
            new_librarian = user_datastore.create_user(email=form.email.data, password='password',confirmed_at=datetime.datetime.now())
        else:
            new_librarian = user_datastore.create_user(email=form.email.data, password='password')
        role_librarian = user_datastore.find_or_create_role(name='librarian', description='Librarian')
        user_datastore.add_role_to_user(new_librarian, role_librarian)
        db.session.commit()
        return redirect(url_for('profile'))
    return render_template('New_librarian.html', form=form)
    
    
class NewBookForm(Form):
    title = TextField('title', [validators.Length(min=1, max=35)])
    author = TextField('author', [validators.Length(min=1, max=35)])
    ISBN = IntegerField('ISBN', [validators.Length(min=9, max=9)])
    
@app.route('/new_book', methods=['GET','POST'])
@login_required
@roles_required('library_admin')
def new_book():
    form = NewBookForm(request.form)
    if request.method == 'POST' and form.validate():
        b = Book(title=form.title.data, author = form.author.data, ISBN = form.ISBN.data, return_date = None,holder=current_user)
        db.session.add(b)
        db.session.commit()
        return redirect(url_for('profile'))
    return render_template('new_book.html',form=form)

class CheckoutForm(Form):
    email = TextField('User Email', [validators.Length(min=1, max=35)])
    book = TextField('Title/Author', [validators.Length(min=1, max=35)])
    return_date = DateField('return_date',[validators.DataRequired()])
    final = BooleanField('Checkout')
    submit = SubmitField('Submit')


@app.route('/checkout', methods=['GET','POST'])
@login_required
@roles_required('librarian')
def checkout():
    
    form = CheckoutForm(request.form)
    library = user_datastore.get_user('admin')
    finalize=False
    books = library.books.all()
    book = library.books.first()
    users = User.query.filter(User.email!=library.email).all()
    user = User.query.filter(User.email!=library.email).first()
    if request.method == 'POST':
        books = Book.query.whoosh_search('*'+form.book.data+'*').filter_by(user_id=library.id).all()
        book = Book.query.whoosh_search('*'+form.book.data+'*').filter_by(user_id=library.id).first()
        users = User.query.filter(User.email.like('%'+form.email.data+'%'),User.email!=library.email).all()
        user = User.query.filter(User.email.like('%'+form.email.data+'%'),User.email!=library.email).first()
        if form.validate() and user != None and book != None:
            finalize = True
            if form.final.data:
                book.return_date = form.return_date.data
                book.holder = user        
                db.session.commit()
                return redirect(url_for('profile'))
        form.final.data=False
        return render_template('checkout.html',form=form,user=user,book=book,users=users,books=books,finalize=finalize)
    return render_template('checkout.html',form=form,user=user,book=book,users=users,books=books,finalize=finalize)


class ReturnForm(Form):
    email = TextField('User Email', [validators.Length(min=1, max=35)])
    book = TextField('Title/Author', [validators.Length(min=1, max=35)])
    final = BooleanField('Return')
    submit = SubmitField('Submit')


@app.route('/return_book', methods=['GET','POST'])
@login_required
@roles_required('librarian')
def return_book():
    form = CheckoutForm(request.form)
    library = user_datastore.get_user('admin')
    
    users = User.query.filter(User.email!=library.email).all()
    user = User.query.filter(User.email!=library.email).first()
    
    books = user.books.all()
    book = user.books.first()
    
    finalize=False
    
    if request.method == 'POST':
        users = User.query.filter(User.email.like('%'+form.email.data+'%'),User.email!=library.email).all()
        user = User.query.filter(User.email.like('%'+form.email.data+'%'),User.email!=library.email).first()
        books = Book.query.filter_by(user_id=user.id).all()
        book = Book.query.whoosh_search('*'+form.book.data+'*').filter_by(user_id=user.id).first()
        if form.validate() and user != None and book != None:
            finalize = True
            if form.final.data:
                book.return_date = None
                book.holder = library       
                db.session.commit()
                return redirect(url_for('profile'))
        form.final.data=False
        return render_template('return_book.html',form=form,user=user,book=book,users=users,books=books,finalize=finalize)
    return render_template('return_book.html',form=form,user=user,book=book,users=users,books=books,finalize=finalize)



if __name__ == '__main__':
    app.run()
