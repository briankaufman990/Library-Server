from flask import Flask, render_template, request, url_for, redirect
from apscheduler.schedulers.background import BackgroundScheduler
from wtforms import Form, BooleanField, TextField, IntegerField, validators
from flask_wtf.html5 import DateField
from flask.ext.sqlalchemy import SQLAlchemy
import flask.ext.whooshalchemy
from flask_mail import Mail
from flask.ext.security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required, roles_required, current_user
    
# Create app
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'even-more-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['WHOOSH_BASE'] = 'whoosh_index'
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_RECOVERABLE'] = True
#app.config['SECURITY_CONFIRMABLE'] = True
app.config['SECURITY_CHANGEABLE'] = True
#app.config['SECURITY_PASSWORD_HASH'] = 'bcrypt'


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
    __searchable__ = ['email']  # these fields will be indexed by whoosh
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    
    books = db.relationship('Book', backref='holder', lazy='dynamic')
    
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
                            
class Book(db.Model):
    __searchable__ = ['title', 'author']  # these fields will be indexed by whoosh

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(140))
    author = db.Column(db.String(140))
    ISBN = db.Column(db.Integer)
    return_date = db.Column(db.Date)

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


def schedule_notices():
     t = dt.combine(dt.now() + datetime.timedelta(days=1), daily_time)
     scheduler.enterabs(time.mktime(t.timetuple()), 1, do_something_again, ('Running again',))

@app.before_first_request
scheduler = sched.scheduler(time.time, time.sleep)
    


# Views
@app.route('/profile')
@login_required
def profile():
    user_books = current_user.books.all()
    if current_user.has_role('library_admin'):
        return render_template('admin.html',user=current_user,books=user_books,logged_in=True)
    if current_user.has_role('librarian'):
        return render_template('librarian.html',user=current_user,books=user_books,logged_in=True)
    
    return render_template('profile.html',user=current_user,books=user_books,logged_in=True)
  
    
class SearchBooksForm(Form):
    search = TextField('Title/Author', [validators.Length(min=1, max=35)])    
  
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    logged_in = True
    if not current_user.is_authenticated():
        logged_in = False
    library = user_datastore.get_user('admin')
    books=library.books.all()
    
    form = SearchBooksForm(request.form)
    if request.method == 'POST' and form.validate():
        books = Book.query.whoosh_search('*'+form.search.data+'*').filter_by(user_id=library.id).all()
    return render_template('index.html',user=library,books=books,form=form,logged_in=logged_in)

class PromoteLibrarianForm(Form):
    email = TextField('Email Address', [validators.Length(min=1, max=35)])

@login_required
@roles_required('library_admin')   
@app.route('/promote_librarian', methods=['GET', 'POST'])
def promote_librarian():
    form = PromoteLibrarianForm(request.form)
    if request.method == 'POST' and form.validate():
        new_librarian = user_datastore.get_user(form.email.data)
        role_librarian = user_datastore.find_or_create_role(name='librarian', description='Librarian')
        user_datastore.add_role_to_user(new_librarian, role_librarian)
        db.session.commit()
        return redirect(url_for('profile'))
    return render_template('promote_librarian.html', form=form,logged_in=True)
    
    
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
    return render_template('new_book.html',form=form,logged_in=True)
    

class CheckoutForm(Form):
    email = TextField('email', [validators.Length(min=1, max=35)])
    ISBN = TextField('ISBN', [validators.Length(min=1, max=35)])
    return_date = DateField('return_date')
    
@app.route('/checkout', methods=['GET','POST'])
@login_required
@roles_required('librarian')
def checkout():
    form = CheckoutForm(request.form)
    if request.method == 'POST' and form.validate():
        user = user_datastore.get_user(form.email.data)
        book = Book.query.filter_by(ISBN=form.ISBN.data).first()
        book.return_date = form.return_date.data
        book.holder = user
        
        db.session.commit()
        return redirect(url_for('profile'))
    return render_template('checkout.html',form=form,logged_in=True)
    
class ReturnForm(Form):
    email = TextField('email', [validators.Length(min=1, max=35)])
    ISBN = TextField('ISBN', [validators.Length(min=1, max=35)])

@app.route('/return_book', methods=['GET','POST'])
@login_required
@roles_required('librarian')
def return_book():
    form = CheckoutForm(request.form)
    if request.method == 'POST' and form.validate():
        library = user_datastore.get_user('admin')
        
        user = user_datastore.get_user(form.email.data)
        book = user.books.all()
        #book = Book.query.filter_by(ISBN=form.ISBN.data).first()
        
        book.holder = library
        db.session.commit()
        return redirect(url_for('profile',logged_in=True))
    return render_template('return_book.html',form=form,logged_in=True)
    
@app.route('/show_users_books', methods=['GET','POST'])
@login_required
@roles_required('librarian')
def show_users_books():
    form = CheckoutForm(request.form)
    if request.method == 'POST' and form.validate():
        library = user_datastore.get_user('admin')
        
        user = user_datastore.get_user(form.email.data)
        books = user.books.all()
        return render_template('users_books.html',user=user,books=books,logged_in=True)
    return render_template('users_books.html', logged_in=True)


if __name__ == '__main__':
    app.run()
