from app import db, user_datastore, Book

db.drop_all()
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