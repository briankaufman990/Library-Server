from flask import Flask, render_template, request, url_for, redirect
from wtforms import Form, BooleanField, TextField, IntegerField, DateField, PasswordField, validators
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required, roles_required, current_user

# Create app
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'super-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_RECOVERABLE'] = True

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
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    
    books = db.relationship('Book', backref='holder', lazy='dynamic')
    
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
                            
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(140))
    author = db.Column(db.String(140))
    ISBN = db.Column(db.Integer)
    return_date = db.Column(db.DateTime)

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Create a user to test with
@app.before_first_request
def create_users():
    db.create_all()
    
    role_librarian = user_datastore.find_or_create_role(name='librarian', description='Librarian')
    role_user = user_datastore.find_or_create_role(name='library-user', description='Library User')
    role_library_admin = user_datastore.find_or_create_role(name='library_admin', description='Library Admin')
    
    
    admin = user_datastore.create_user(email='admin', password='password')
    user_datastore.add_role_to_user(admin, role_librarian)
    user_datastore.add_role_to_user(admin, role_library_admin)
    
    user = user_datastore.create_user(email='user', password='password')
    user_datastore.add_role_to_user(user, role_user)
    
    librarian = user_datastore.create_user(email='librarian', password='password')
    user_datastore.add_role_to_user(librarian, role_librarian)
    
    
    b = Book(title='test', author = 'me', ISBN = 1, return_date = None,holder=admin)
    db.session.add(b)
    
    b = Book(title='test2', author = 'me', ISBN = 2, return_date = None,holder=user)
    db.session.add(b)
    
    b = Book(title='test3', author = 'me', ISBN = 3, return_date = None,holder=admin)
    db.session.add(b)
    
    b = Book(title='test4', author = 'me', ISBN = 4, return_date = None,holder=librarian)
    db.session.add(b)
    
    b = Book(title='test5', author = 'me', ISBN = 5, return_date = None,holder=user)
    db.session.add(b)
    
    db.session.commit()
    
    db.session.commit()

# Views
@app.route('/')
@app.route('/index')
@login_required
def home():
    user_books = current_user.books.all()
    return render_template('index.html',user=current_user,books=user_books)
    

@app.route('/library')
def library():
    library = user_datastore.get_user('admin')
    return render_template('index.html',user=library,books=library.books.all())
    
@app.route('/admin')
@login_required
@roles_required('library_admin')
def admin():
    return render_template('admin.html')


class PromoteLibrarianForm(Form):
    email = TextField('Email Address', [validators.Length(min=6, max=35)])

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
        return url_for('admin.html')
    return render_template('promote_librarian.html', form=form)
    
    
class NewBookForm(Form):
    title = TextField('Title', [validators.Length(min=6, max=35)])
    author = TextField('Author', [validators.Length(min=6, max=35)])
    isbn = IntegerField('ISBN', [validators.Length(min=6, max=35)])
    
@app.route('/new_book')
@login_required
@roles_required('library_admin')
def new_book():
    form = NewBookForm(request.form)
    if request.method == 'POST' and form.validate():
        b = Book(title=form.title.data, author = form.author.data, ISBN = form.ISBN.data, return_date = None,holder=current_user)
        db.session.add(b)
        db.session.commit()
        return url_for('admin.html')
    return render_template('promote_librarian.html', form=form)
    return render_template('new_book.html')
    

class CheckoutForm(Form):
    email = TextField('email', [validators.Length(min=6, max=35)])
    ISBN = IntegerField('ISBN', [validators.Length(min=6, max=35)])
    return_date = DateField('return_date', [validators.Length(min=6, max=35)])
    
@app.route('/checkout')
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
        return url_for('index.html')
    return render_template('promote_librarian.html', form=form)
    return render_template('checkout.html')
    
class ReturnForm(Form):
    email = TextField('email', [validators.Length(min=6, max=35)])
    ISBN = IntegerField('ISBN', [validators.Length(min=6, max=35)])
    
@app.route('/return_book')
@login_required
@roles_required('librarian')
def return_book():
    form = CheckoutForm(request.form)
    if request.method == 'POST' and form.validate():
        library = user_datastore.get_user('admin')
        
        user = user_datastore.get_user(form.email.data)
        book = Book.query.filter_by(ISBN=form.ISBN.data).first()
        
        book.holder = library
        
        db.session.commit()
        return url_for('index.html')
    return render_template('checkout.html', form=form)
    
@app.route('/test')
@login_required
@roles_required('librarian')
def test():
    library = user_datastore.get_user('admin')
        
    user = user_datastore.get_user('user')
    book = user.subquery.filter_by(1).first()
        
    book.holder = library
        
    db.session.commit()
        
    print book.holder
    return render_template('index.html',user=library,books=library.books.all())


if __name__ == '__main__':
    app.run()
