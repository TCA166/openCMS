import sqlite3
import hashlib
import os

def hash(password, salt):
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return key

def addUser(login, password):
    salt = os.urandom(32)
    password = hash(password, salt)
    conn = sqlite3.connect('main.db')
    cur = conn.cursor()
    cur.execute('INSERT INTO użytkownicy VALUES (?, ?, ?)', (login, password, salt))
    conn.commit()

if __name__ == '__main__':
    print('Welcome to the backend user adding utility.')
    login = input('New user login:')
    password = input('New user password:')
    addUser(login, password)
