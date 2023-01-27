import sqlite3
import os
import jinja2
import io
import shutil

environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(os.path.realpath(__file__)) + '\\templates'))

sqliteTypes = ['INTEGER', 'TEXT', 'BLOB', 'REAL', 'NUMERIC']

#here a whole bunch of python code templates to add to the skeleton file as needed

homePageCodeStart = """
@app.route('/', methods=['GET'])
@app.route('/%s', methods=['GET'])
def home():
    if isAuthorised() == False:
        return render_template('auth.html', encoding='utf-8')"""

normalPageCodeStart = """
@app.route('/%s', methods=['GET'])
def %s():
    if isAuthorised() == False:
        abort(401)"""

dataPageCode = """
    conn = getConn()
    cur = conn.cursor()
    cur.execute('SELECT rowid, * FROM %s')
    data = cur.fetchall()
    return render_template('%s.html', rows=data, encoding='utf-8')
    """

genericPageCode = """
    return render_template('%s.html', encoding='utf-8')
    """

fetchPageCode = """
    with open('%s', 'r') as f:
        data = json.load(f)
        return render_template('%s.html', json=data, encoding='utf-8')
    """

postPageCodeStart = """
@app.route('/%s', methods=['POST'])
def %s():
    if isAuthorised() == False:
        abort(401)"""

submitNewCode = """
    conn = getConn()
    cur = conn.cursor()
    data = dict(request.form)
    rowid = data['rowid']
    data.pop('rowid', None)
    if rowid == '':
        placeholders = ', '.join('?' * len(list(data.values())))
        sql = 'INSERT INTO %s VALUES ({})'.format(placeholders)
        cur.execute(sql, list(data.values()))
    else:
        sets = []
        for key in data:
            sets.append(key + ' = ?')
        sql = 'UPDATE %s SET {} WHERE rowid=?'.format(', '.join(sets))
        cur.execute(sql, list(data.values()).append(rowid))
    conn.commit()
    return redirect('/')
"""

getPageCodeStart = """
@app.route('/%s', methods=['GET'])
def %s(%s):
    if isAuthorised() == False:
        abort(401)"""

editCode = """
    return render_template('%s.html', rowid=rowid, encoding='utf-8')
"""

codeFooter = """
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
"""

#classes and the associated code

class field:
    """A field that is held by a dataType"""
    def __init__(self, name:str, fieldType:str = 'TEXT', unit:str = '', filtrable:bool = False, required:bool = False) -> None:
        if fieldType not in sqliteTypes:
            raise ValueError('Provided fieldType %s doesn\'t exist in sqlite.' % fieldType)
        self.name = name
        self.fieldType = fieldType
        self.unit = unit
        self.filtrable = filtrable
        self.required = required

class dataType:
    """A data type that will be stored in the CSM. Each dataType has it's own table in the db and holds a set amount of fields"""
    def __init__(self, name:str, fields:list[field] = None) -> None:
        self.name = name
        if fields != None and isinstance(fields, list):
            self.fields = fields
        else:
            self.fields = []
        self.children = []
        self.isChild = False

    def addField(self, field:field) -> None:
        """Adds the given field to this datatype"""
        self.fields.append(field)
    
    def addChild(self, child:'dataType') -> None:
        """Sets the provided datatype as a child to this datatype"""
        self.children.append(child)
        child.isChild = True

    def render(self, pages:list['page'], pythonFile:io.FileIO = None) -> None:
        """Creates the neccesary endpoints and html templates for this dataType"""
        template = environment.get_template('newTemplate.html')
        content = template.render(pages = pages, data = self)
        with open('./templates/%s.html' % self.name, 'w') as f:
            f.write(content)
        if pythonFile != None:
            pythonFile.write(normalPageCodeStart % ('new/%s' % self.name, self.name))
            pythonFile.write(genericPageCode % self.name)

            pythonFile.write(postPageCodeStart % ('new/%s/submit' % self.name, self.name + 'Submit'))
            pythonFile.write(submitNewCode % (self.name, self.name))

            pythonFile.write(getPageCodeStart % ('edit/%s/<rowid>' % self.name, self.name + 'Edit', 'rowid'))
            pythonFile.write(editCode % self.name)

class page:
    """A page in the CSM"""
    def __init__(self, name:str, htmlContent:str = 'Hello World'):
        self.name = name
        self.home = False
        self.htmlContent = htmlContent

    def render(self, pages:list['page'], pythonFile:io.FileIO = None, home:bool = False, ) -> None:
        """Creates this page's template and writes the appropriate code to the pythonFile"""
        template = environment.get_template('genericTemplate.html')
        content = template.render(page=self, pages=pages, htmlContent=self.htmlContent)
        with open('./templates/%s.html' % self.name, 'w') as f:
            f.write(content)
        if pythonFile != None:
            if home:
                pythonFile.write(homePageCodeStart % self.name)
            else:
                pythonFile.write(normalPageCodeStart % (self.name) * 2)
            pythonFile.write(genericPageCode % self.name)

class dataPage(page):
    """Page that displays a table with all the data from the correspoding db table."""
    def setData(self, dataType:dataType) -> None:
        """Sets which datatype this page should display"""
        self.dataType = dataType

    def render(self, pages:list['page'], pythonFile:io.FileIO = None, home:bool = False) -> None:
        """Creates this page's template"""
        template = environment.get_template('dataTemplate.html')
        content = template.render(page=self, pages=pages, data=self.dataType)
        with open('./templates/%s.html' % self.name, 'w') as f:
            f.write(content)
        if pythonFile != None:
            if home:
                pythonFile.write(homePageCodeStart % self.name)
            else:
                pythonFile.write(normalPageCodeStart % (self.name, self.name))
            pythonFile.write(dataPageCode % (self.dataType.name, self.name))
        self.dataType.render(pages, pythonFile)

class fetchPage(page):
    """Page that fetches contents of a json file and displays them once loaded"""
    def setSource(self, filename:str):
        """Sets the provided filename as the source json file"""
        self.filename = filename

    def render(self, pages:list['page'], pythonFile:io.FileIO = None, home:bool = False) -> None:
        """Creates this page's template and writes the appropriate code to the pythonFile"""
        template = environment.get_template('fetchTemplate.html')
        content = template.render(page=self, pages=pages)
        with open('./templates/%s.html' % self.name, 'w') as f:
            f.write(content)
        if pythonFile != None:
            if home:
                pythonFile.write(homePageCodeStart % self.name)
            else:
                pythonFile.write(normalPageCodeStart % (self.name) * 2)
            pythonFile.write(fetchPageCode % (self.filename, self.name))

class db:
    """Database of a CSM app"""
    def __init__(self, filename:str = 'main.db') -> None:
        conn = sqlite3.connect(filename)
        self.conn = conn
        try:
            conn.execute('CREATE TABLE "users" ( "login" TEXT NOT NULL UNIQUE, "pass" TEXT NOT NULL, "salt" TEXT, "auth" INTEGER)')
        except sqlite3.OperationalError:
            print("DB is already here.")
        conn.commit()
        self.filename = filename

    def addData(self, dataType:dataType) -> None:
        """Creates the needed table for the dataType in the db"""
        cur = self.conn.cursor()
        sql = 'CREATE TABLE "%s" ( %s )'
        sqlInner = []
        for field in dataType.fields:
            if field is dataType:
                sqlInner.append('"%s" TEXT' % field.name)
            else:
                sqlInner.append('"%s" %s' % (field.name, field.fieldType))
        sql = sql % (dataType.name, ','.join(sqlInner))
        try:
            cur.execute(sql)
        except sqlite3.OperationalError:
            pass
        self.conn.commit()

class app:
    """A CSM app"""
    def __init__(self, name:str) -> None:
        self.name = name
        os.makedirs('./%s/templates' % self.name, exist_ok=True)
        os.chdir('./%s' % self.name)
        self.db = db("%s\main.db" % os.getcwd()) #
        self.pages = []
        self.home = None

    def addPage(self, page:page) -> None:
        """Adds the page to the app"""
        self.pages.append(page)

    def setHome(self, page:page) -> None:
        """Sets the given page as home"""
        self.home = page

    def render(self) -> None:
        """Creates the app"""
        print("Starting app render...")
        shutil.copytree('../readyTemplates', './templates', dirs_exist_ok=True)
        shutil.copytree('../static', './static', dirs_exist_ok=True)
        shutil.copy('../addUser.py', './addUser.py', follow_symlinks=True)
        with open('../appSkeleton.py', 'r') as f:
            skeleton = f.read()
        with open('./app.py', 'w') as f:
            f.write(skeleton % os.path.basename(self.db.filename))
            for page in self.pages:
                if isinstance(page, dataPage):
                    self.db.addData(page.dataType)
                page.render(self.pages, f, page == self.home)
            f.write(codeFooter)
        self.db.conn.close()

if __name__ == '__main__':
    thisApp = app('testCSM')
    testPage = page('Home', 'Welcome')
    testDataPage = dataPage('Data')
    a = field('text1', filtrable=True)
    b = field('text2')
    t = dataType('testType', [a, b])
    testDataPage.setData(t)
    thisApp.setHome(testPage)
    thisApp.addPage(testPage)
    thisApp.addPage(testDataPage)
    thisApp.render()
