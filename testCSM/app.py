from flask import Flask, render_template, jsonify, request, redirect, url_for, session, abort, send_from_directory, logging
from werkzeug.utils import secure_filename
import sqlite3
import os
import addUser
import json

app = Flask(__name__)

# Make the WSGI interface available at the top level so wfastcgi can get it.
wsgi_app = app.wsgi_app

app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

def getConn():
    """Returns the connected database"""
    return sqlite3.connect(r'main.db')

def isAuthorised():
    """Returns True or False depending on if the frontend (session) is authorised"""
    #Authorisation is binary here. Logging in simply sets an encrypted cookie with True in it.
    try:
        if session['authorised'] == False:
            return False
        else:
            return True
    except KeyError: #there isn't even a key here - the user is unauthorised
        return False

@app.errorhandler(404)
def notFound(e):
    return render_template('404.html', ), 404
@app.errorhandler(401)
def authFailed(e):
    return render_template('401.html', ), 401
@app.errorhandler(500)
def serverError(e):
    return render_template('500.html', ), 500

@app.route('/login', methods=['POST'])
def login():
    conn = getConn()
    cur = conn.cursor()
    login = request.form['login']
    password = request.form['pass']
    cur.execute('SELECT salt FROM users WHERE login=?', (login,))
    try:
        salt = cur.fetchall()[0][0]
    except IndexError:
        return redirect(url_for('home'))
    key = addUser.hash(password, salt)
    cur.execute('SELECT EXISTS(SELECT * FROM users WHERE login=? AND pass=?)', (login, key))
    exists = cur.fetchall()[0][0]
    if exists == 1:
        session['authorised'] = True
    return redirect(url_for('home'))

@app.route('/', methods=['GET'])
@app.route('/Home', methods=['GET'])
def home():
    if isAuthorised() == False:
        return render_template('auth.html', encoding='utf-8')
    return render_template('Home.html', encoding='utf-8')
    
@app.route('/Data', methods=['GET'])
def Data():
    if isAuthorised() == False:
        abort(401)
    conn = getConn()
    cur = conn.cursor()
    cur.execute('SELECT rowid, * FROM testType')
    data = cur.fetchall()
    return render_template('Data.html', rows=data, encoding='utf-8')
    
@app.route('/new/testType', methods=['GET'])
def testType():
    if isAuthorised() == False:
        abort(401)
    return render_template('testType.html', encoding='utf-8')
    
@app.route('/new/testType/submit', methods=['POST'])
def testTypeSubmit():
    if isAuthorised() == False:
        abort(401)
    conn = getConn()
    cur = conn.cursor()
    data = dict(request.form)
    rowid = data['rowid']
    data.pop('rowid', None)
    if rowid == '':
        placeholders = ', '.join('?' * len(list(data.values())))
        sql = 'INSERT INTO testType VALUES ({})'.format(placeholders)
        cur.execute(sql, list(data.values()))
    else:
        sets = []
        for key in data:
            sets.append(key + ' = ?')
        sql = 'UPDATE testType SET {} WHERE rowid=?'.format(', '.join(sets))
        print(sql)
        cur.execute(sql, list(data.values()).append(rowid))
    conn.commit()
    return redirect('/')

@app.route('/edit/testType/<rowid>', methods=['GET'])
def testTypeEdit(rowid):
    if isAuthorised() == False:
        abort(401)
    return render_template('testType.html', rowid=rowid, encoding='utf-8')

if __name__ == '__main__':
    import os
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError: 
        PORT = 5555
    debug = False
    app.run(HOST, PORT, debug=debug)
