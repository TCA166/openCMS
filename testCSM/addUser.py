import sqlite3
import hashlib
import os

def hash(password:'ReadeableBuffer', salt:'ReadeableBuffer') -> bytes:
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return key

def addUser(login:str, password:str, auth:int) -> None:
    salt = os.urandom(32)
    password = hash(password, salt)
    conn = sqlite3.connect('main.db')
    cur = conn.cursor()
    cur.execute('INSERT INTO users VALUES (?, ?, ?, ?)', (login, password, salt, auth))
    conn.commit()

if __name__ == '__main__':
    print('Welcome to the backend user adding utility.')
    login = input('New user login:')
    password = input('New user password:')
    auth = input('Input new user authority level:')
    addUser(login, password, int(auth))
