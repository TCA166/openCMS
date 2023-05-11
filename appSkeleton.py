from flask import Flask, render_template, jsonify, request, redirect, url_for, session, abort, send_from_directory, logging
from werkzeug.utils import secure_filename
import sqlite3
import os
import addUser
import json

#This app was generated using the openCSM framework for python
#You can find it here https://github.com/TCA166/openCMS

app = Flask(__name__)

# Make the WSGI interface available at the top level so wfastcgi can get it.
wsgi_app = app.wsgi_app

app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

def getConn():
    """Returns the connected database"""
    return sqlite3.connect(r'%s')

def isAuthorised(level:int=0):
    """Returns True or False depending on if the frontend (session) is authorised"""
    #Authorisation is binary here. Logging in simply sets an encrypted cookie with True in it.
    try:
        if session['authorised'] == False:
            return False
        else:
            if level <= session['level']:
                return True
            else:
                return False
    except KeyError: #there isn't even a key here - the user is unauthorised
        return False

@app.errorhandler(404)
def notFound(e):
    return render_template('404.html'), 404
@app.errorhandler(401)
def authFailed(e):
    return render_template('401.html'), 401
@app.errorhandler(500)
def serverError(e):
    return render_template('500.html'), 500

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
        cur.execute('SELECT auth FROM users WHERE login=? AND pass=?', (login, key))
        auth = cur.fetchall()[0][0]
        session['level'] = auth
    return redirect(url_for('home'))

@app.route('/logout', methods=['GET'])
def logout():
    session['authorised'] = False
    session['level'] = None
    return redirect(url_for('home'))
