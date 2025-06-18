import psycopg
from app import login_manager
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, login, password, role):
        self.id = id
        self.login = login
        self.password = password
        self.role = role

@login_manager.user_loader
def load_user(id):
    with psycopg.connect(
        host="localhost",
        port="5432",
        user="postgres",
        password="1111",
        dbname="School") as con:
        cur = con.cursor()
        login = cur.execute('SELECT login '
                                      'FROM "user" '
                                      'WHERE id = %s', (id,)).fetchone()
        password = cur.execute('SELECT password '
                                      'FROM "user" '
                                      'WHERE id = %s', (id,)).fetchone()
        role = cur.execute('SELECT role '
                                      'FROM "user" '
                                      'WHERE id = %s', (id,)).fetchone()
    return User(id, login, password, role)