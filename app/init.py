from app import db, user_datastore, Book
import datetime

db.drop_all()
db.create_all()

role_librarian = user_datastore.find_or_create_role(name='librarian', description='Librarian')
role_library_admin = user_datastore.find_or_create_role(name='library_admin', description='Library Admin')


admin = user_datastore.create_user(email='admin', password='password',confirmed_at=datetime.datetime.now())
user_datastore.add_role_to_user(admin, role_librarian)
user_datastore.add_role_to_user(admin, role_library_admin)

user = user_datastore.create_user(email='user2', password='password',confirmed_at=datetime.datetime.now())

user = user_datastore.create_user(email='user3', password='password',confirmed_at=datetime.datetime.now())

user = user_datastore.create_user(email='user4', password='password',confirmed_at=datetime.datetime.now())

librarian = user_datastore.create_user(email='librarian', password='password',confirmed_at=datetime.datetime.now())
user_datastore.add_role_to_user(librarian, role_librarian)

brian = user_datastore.create_user(email='brianherb1@gmail.com', password='password',confirmed_at=datetime.datetime.now())


b = Book(title='test_day', author = 'me', ISBN = 1, return_date = datetime.date.today()+datetime.timedelta(days=1), holder=brian)
db.session.add(b)

b = Book(title='test_week', author = 'me', ISBN = 2, return_date = datetime.date.today()+datetime.timedelta(days=7), holder=brian)
db.session.add(b)

b = Book(title='test_overdue', author = 'me', ISBN = 3,  return_date = datetime.date.today()-datetime.timedelta(days=7), holder=brian)
db.session.add(b)

b = Book(title='test', author = 'me', ISBN = 4, return_date = None, holder=librarian)
db.session.add(b)

b = Book(title='test2', author = 'me', ISBN = 5, return_date = None, holder=user)
db.session.add(b)

b = Book(title='test3', author = 'me', ISBN = 6, return_date = None, holder=admin)
db.session.add(b)

b = Book(title='test3', author = 'me', ISBN = 6, return_date = None, holder=admin)
db.session.add(b)

b = Book(title='Moby Dick', author = 'me', ISBN = 6, return_date = None, holder=admin)
db.session.add(b)

b = Book(title='Herman Melville', author = 'me', ISBN = 6, return_date = None, holder=admin)
db.session.add(b)

b = Book(title='user2', author = 'me', ISBN = 6, return_date = None, holder=admin)
db.session.add(b)

b = Book(title='book', author = 'me', ISBN = 6, return_date = None, holder=admin)
db.session.add(b)


db.session.commit()