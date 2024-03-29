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
    return sqlite3.connect(r'main.db')

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

@app.route('/', methods=['GET'])
@app.route('/Home', methods=['GET'])
def home():
    if isAuthorised() == False:
        return render_template('auth.html', encoding='utf-8')
    if isAuthorised(0) == False:
        abort(401)
    return render_template('Home.html', encoding='utf-8')
    
@app.route('/Clients', methods=['GET'])
def Clients():
    if isAuthorised(0) == False:
        abort(401)
    conn = getConn()
    cur = conn.cursor()
    cur.execute('SELECT rowid, * FROM "Client"')
    ClientRows = cur.fetchall()
    return render_template('Clients.html', ClientRows=ClientRows, encoding='utf-8')
    
@app.route('/new/Client', methods=['GET'])
def Client():
    if isAuthorised(0) == False:
        abort(401)
    return render_template('Client.html', encoding='utf-8')
    
@app.route('/new/Client/submit', methods=['POST'])
def ClientSubmit():
    if isAuthorised(0) == False:
        abort(401)
    conn = getConn()
    cur = conn.cursor()
    data = dict(request.form)
    rowRowid = data['Clientrowid-0']
    if rowRowid == '':
        sql = 'INSERT INTO "Client" VALUES (?, ?, ?, ?)'
        cur.execute(sql, (data["ClientName-0"], data["ClientSurname-0"], data["ClientAge-0"], data["Clientuid-0"],))
        ClientlastRowid = cur.lastrowid
    else:
        sql = 'UPDATE "Client" SET Name=?, Surname=?, Age=?, uid=? WHERE rowid=?'
        values = [data["ClientName-0"], data["ClientSurname-0"], data["ClientAge-0"], data["Clientuid-0"],]
        values.append(rowRowid)
        cur.execute(sql, values)
        ClientlastRowid = rowRowid
    
    conn.commit()
    return redirect('/')
    
@app.route('/edit/Client/<rowid>', methods=['GET'])
def ClientEdit(rowid):
    if isAuthorised(0) == False:
        abort(401)
    conn = getConn()
    cur = conn.cursor()
    cur.execute('SELECT rowid, * FROM "Client" WHERE rowid=?', (rowid, ))
    dataClient = cur.fetchall()[0]

    return render_template('Client.html', Clientrowid=rowid, dataClient=dataClient, encoding='utf-8')

@app.route('/copy/Client/<rowid>', methods=['POST'])
def Clientcopy(rowid):
    if isAuthorised(0) == False:
        abort(401)
    conn = getConn()
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = OFF;")
    cur.execute("INSERT INTO Client SELECT * FROM Client WHERE rowid=?", rowid)
    cur.execute("PRAGMA foreign_keys = ON;")

    conn.commit()
    return redirect('/')
    
@app.route('/Products', methods=['GET'])
def Products():
    if isAuthorised(0) == False:
        abort(401)
    conn = getConn()
    cur = conn.cursor()
    cur.execute('SELECT rowid, * FROM "Product"')
    ProductRows = cur.fetchall()
    return render_template('Products.html', ProductRows=ProductRows, encoding='utf-8')
    
@app.route('/new/Product/<rowidClient>', methods=['GET'])
def Product(rowidClient):
    if isAuthorised(0) == False:
        abort(401)
    return render_template('Product.html', rowidClient=rowidClient, encoding='utf-8')
    
@app.route('/new/Product/submit', methods=['POST'])
def ProductSubmit():
    if isAuthorised(0) == False:
        abort(401)
    conn = getConn()
    cur = conn.cursor()
    data = dict(request.form)
    rowRowid = data['Productrowid-0']
    if rowRowid == '':
        sql = 'INSERT INTO "Product" VALUES (?, ?, ?)'
        cur.execute(sql, (data["ProductrowidClient-0"], data["ProductProduct name-0"], data["ProductPrice-0"],))
        ProductlastRowid = cur.lastrowid
    else:
        sql = 'UPDATE "Product" SET Product name=?, Price=? WHERE rowid=?'
        values = [data["ProductrowidClient-0"], data["ProductProduct name-0"], data["ProductPrice-0"],]
        values.append(rowRowid)
        cur.execute(sql, values)
        ProductlastRowid = rowRowid
    
    conn.commit()
    return redirect('/')
    
@app.route('/edit/Product/<rowid>', methods=['GET'])
def ProductEdit(rowid):
    if isAuthorised(0) == False:
        abort(401)
    conn = getConn()
    cur = conn.cursor()
    cur.execute('SELECT rowid, * FROM "Product" WHERE rowid=?', (rowid, ))
    dataProduct = cur.fetchall()[0]

    return render_template('Product.html', Productrowid=rowid, dataProduct=dataProduct, encoding='utf-8')

@app.route('/copy/Product/<rowid>', methods=['POST'])
def Productcopy(rowid):
    if isAuthorised(0) == False:
        abort(401)
    conn = getConn()
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = OFF;")
    cur.execute("INSERT INTO Product SELECT * FROM Product WHERE rowid=?", rowid)
    cur.execute("PRAGMA foreign_keys = ON;")

    conn.commit()
    return redirect('/')
    
@app.route('/secretPage', methods=['GET'])
def secretPage():
    if isAuthorised(1) == False:
        abort(401)
    conn = getConn()
    cur = conn.cursor()
    cur.execute('SELECT rowid, * FROM "superSecret"')
    superSecretRows = cur.fetchall()
    return render_template('secretPage.html', superSecretRows=superSecretRows, encoding='utf-8')
    
@app.route('/new/superSecret', methods=['GET'])
def superSecret():
    if isAuthorised(1) == False:
        abort(401)
    return render_template('superSecret.html', encoding='utf-8')
    
@app.route('/new/superSecret/submit', methods=['POST'])
def superSecretSubmit():
    if isAuthorised(1) == False:
        abort(401)
    conn = getConn()
    cur = conn.cursor()
    data = dict(request.form)
    rowRowid = data['superSecretrowid-0']
    if rowRowid == '':
        sql = 'INSERT INTO "superSecret" VALUES (?)'
        cur.execute(sql, (data["superSecretSecret-0"],))
        superSecretlastRowid = cur.lastrowid
    else:
        sql = 'UPDATE "superSecret" SET Secret=? WHERE rowid=?'
        values = [data["superSecretSecret-0"],]
        values.append(rowRowid)
        cur.execute(sql, values)
        superSecretlastRowid = rowRowid
    
    conn.commit()
    return redirect('/')
    
@app.route('/edit/superSecret/<rowid>', methods=['GET'])
def superSecretEdit(rowid):
    if isAuthorised(1) == False:
        abort(401)
    conn = getConn()
    cur = conn.cursor()
    cur.execute('SELECT rowid, * FROM "superSecret" WHERE rowid=?', (rowid, ))
    datasuperSecret = cur.fetchall()[0]

    return render_template('superSecret.html', superSecretrowid=rowid, datasuperSecret=datasuperSecret, encoding='utf-8')

@app.route('/copy/superSecret/<rowid>', methods=['POST'])
def superSecretcopy(rowid):
    if isAuthorised(1) == False:
        abort(401)
    conn = getConn()
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = OFF;")
    cur.execute("INSERT INTO superSecret SELECT * FROM superSecret WHERE rowid=?", rowid)
    cur.execute("PRAGMA foreign_keys = ON;")

    conn.commit()
    return redirect('/')
    
@app.route('/Orders', methods=['GET'])
def Orders():
    if isAuthorised(0) == False:
        abort(401)
    conn = getConn()
    cur = conn.cursor()
    cur.execute('SELECT rowid, * FROM "order"')
    orderRows = cur.fetchall()
    cur.execute('SELECT rowid, * FROM "Products"')
    ProductsRows = cur.fetchall()
    return render_template('Orders.html', ProductsRows=ProductsRows, orderRows=orderRows, encoding='utf-8')
    
@app.route('/new/order', methods=['GET'])
def order():
    if isAuthorised(0) == False:
        abort(401)
    return render_template('order.html', encoding='utf-8')
    
@app.route('/new/order/submit', methods=['POST'])
def orderSubmit():
    if isAuthorised(0) == False:
        abort(401)
    conn = getConn()
    cur = conn.cursor()
    data = dict(request.form)
    rowRowid = data['orderrowid-0']
    if rowRowid == '':
        sql = 'INSERT INTO "order" VALUES (?)'
        cur.execute(sql, (data["ordername-0"],))
        orderlastRowid = cur.lastrowid
    else:
        sql = 'UPDATE "order" SET name=? WHERE rowid=?'
        values = [data["ordername-0"],]
        values.append(rowRowid)
        cur.execute(sql, values)
        orderlastRowid = rowRowid
    
    i = 0
    while 'Productsrowid' + '-' + str(i) in data.keys():
        fields = ('rowidorder', 'name', 'count')
        values = [orderlastRowid if f=='rowidorder' else data["Products" + f + '-' + str(i)] for f in fields]
        rowRowid = data['Productsrowid-' + str(i)]
        if rowRowid == '':
            sql = 'INSERT INTO "Products" VALUES (?, ?, ?)'
            cur.execute(sql, values)
            ProductslastRowid = cur.lastrowid
        else:
            sql = 'UPDATE "Products" SET name=?, count=? WHERE rowid=?'
            values.pop(0)
            values.append(rowRowid)
            cur.execute(sql, values)
            ProductslastRowid = rowRowid
        i += 1
    
    
    conn.commit()
    return redirect('/')
    
@app.route('/edit/order/<rowid>', methods=['GET'])
def orderEdit(rowid):
    if isAuthorised(0) == False:
        abort(401)
    conn = getConn()
    cur = conn.cursor()
    cur.execute('SELECT rowid, * FROM "order" WHERE rowid=?', (rowid, ))
    dataorder = cur.fetchall()[0]

    cur.execute('SELECT rowid, * FROM "Products" WHERE rowidorder=?', (dataorder[0], ))
    dataProducts = cur.fetchall()

    return render_template('order.html', orderrowid=rowid, dataorder=dataorder, dataProducts=dataProducts, encoding='utf-8')

@app.route('/copy/order/<rowid>', methods=['POST'])
def ordercopy(rowid):
    if isAuthorised(0) == False:
        abort(401)
    conn = getConn()
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = OFF;")
    cur.execute("INSERT INTO order SELECT * FROM order WHERE rowid=?", rowid)
    cur.execute("PRAGMA foreign_keys = ON;")

    conn.commit()
    return redirect('/')
    
@app.route('/jsonDisplay', methods=['GET'])
def jsonDisplay():
    if isAuthorised(0) == False:
        abort(401)
    with open('cards.json', 'r') as f:
        data = json.load(f)
        return render_template('jsonDisplay.html', json=data, encoding='utf-8')
    
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
