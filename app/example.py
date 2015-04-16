from flask import Flask, render_template
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required, roles_required

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
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
                            
class Books(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140))
    author = db.Column(db.String(140))
    ISBN = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Create a user to test with
@app.before_first_request
def create_user():
    db.create_all()
    
    role_librarian = user_datastore.find_or_create_role(name='librarian', description='Librarian')
    role_user = user_datastore.find_or_create_role(name='library-user', description='Library User')
    role_admin = user_datastore.find_or_create_role(name='admin', description='Admin')
    
    user = user_datastore.create_user(email='user', password='password')
    user_datastore.add_role_to_user(user, role_user)
    
    librarian = user_datastore.create_user(email='librarian', password='password')
    user_datastore.add_role_to_user(librarian, role_librarian)
    
    admin = user_datastore.create_user(email='admin', password='password')
    user_datastore.add_role_to_user(admin, role_librarian)
    user_datastore.add_role_to_user(admin, role_admin)
    
    db.session.commit()

# Views
@app.route('/')
@app.route('/index')
@login_required
def home():
    return render_template('index.html')
    
@app.route('/admin')
@login_required
@roles_required('admin')
def admin():
    return render_template('admin.html')
    
@app.route('/new_librarian')
@login_required
@roles_required('admin')
def new_librarian():
    return render_template('register_librarian.html')
    
@app.route('/new_book')
@login_required
@roles_required('admin')
def new_book():
    return render_template('add_book.html')

@app.route('/test')
@roles_required('librarian')
def test():
    return render_template('test.html')

if __name__ == '__main__':
    app.run()