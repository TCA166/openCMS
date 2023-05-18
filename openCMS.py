import sqlite3
import os
import jinja2
import io
import shutil

environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(os.path.realpath(__file__)) + '\\templates'))

def __renderTable(dataType:'dataType', showBtn:bool) -> str:
    template = environment.get_template('tableTemplate.html')
    content = template.render(data = dataType, showBtn=showBtn)
    return content

def __renderTableInput(dataType:'dataType', showBtn:bool) -> str:
    template = environment.get_template('tableInputTemplate.html')
    content = template.render(data = dataType, showBtn=showBtn)
    return content

def __isField(object) -> bool:
    return isinstance(object, field) or isinstance(object, foreignField)

def __getIndexWhereName(name:str, list:list['field']) -> int:
    for idx, item in enumerate(list):
        if item.name == name:
            return idx + 1

#so that's something cool: we import python functions into jinja
environment.globals['renderTable'] = __renderTable
environment.globals['isField'] = __isField
environment.globals['getIndexWhereName'] = __getIndexWhereName
environment.globals['renderTableInput'] = __renderTableInput

sqliteTypes = ('INTEGER', 'TEXT', 'BLOB', 'REAL', 'NUMERIC')

inputType = ('checkbox', 'color', 'date', 'email', 'file', 'image', 'number', 'password', 'range', 'text', 'tel')

#here a whole bunch of python code templates to add to the skeleton file as needed
#the idea behind these is that they are structured to act as building blocks

#beginning of the backend code for the homepage
homePageCodeStart = """
@app.route('/', methods=['GET'])
@app.route('/%s', methods=['GET'])
def home():
    if isAuthorised() == False:
        return render_template('auth.html', encoding='utf-8')"""

#start of backend code for a generic static page with no path args
normalPageCodeStart = """
@app.route('/%s', methods=['GET'])
def %s():"""

#-|- but with path args
argsPageCodeStart = """
@app.route('/%s', methods=['GET'])
def %s(%s):"""

#code needed in the dataPage backend
dataPageCode = """
    conn = getConn()
    cur = conn.cursor()"""

#backend code that does a SELECT
sqlFetchCode = """
    cur.execute('SELECT rowid, * FROM "%s"')
    %sRows = cur.fetchall()"""

#code that ends backend code for a generic page
genericPageCode = """
    return render_template('%s.html', encoding='utf-8')
    """

#-|- but also can fill in jinja variables 
argsPageCode = """
    return render_template('%s.html', %s, encoding='utf-8')
    """

#main backend code for a fetch page sure
fetchPageCode = """
    with open('%s', 'r') as f:
        data = json.load(f)
        return render_template('%s.html', json=data, encoding='utf-8')
    """

#generic code for a POST page
postPageCodeStart = """
@app.route('/%s', methods=['POST'])
def %s():"""

#start of the code for a submit endpoint
submitNewCodeStart = """
    conn = getConn()
    cur = conn.cursor()
    data = dict(request.form)"""

#code for handling the submission of a non multi Row datatype
submitTypeCode = """
    rowRowid = data['%srowid-0']
    if rowRowid == '':
        sql = 'INSERT INTO "%s" VALUES (%s)'
        cur.execute(sql, (%s,))
        %slastRowid = cur.lastrowid
    else:
        sql = 'UPDATE "%s" SET %s WHERE rowid=?'
        values = [%s,]
        values.append(rowRowid)
        cur.execute(sql, values)
        %slastRowid = rowRowid
    """

#code for handling the submission of multi Row datatype
submitMultiRowCode = """
    i = 0
    while '%srowid' + '-' + str(i) in data.keys():
        fields = (%s)
        values = [%slastRowid if f=='rowid%s' else data["%s" + f + '-' + str(i)] for f in fields]
        rowRowid = data['%srowid-' + str(i)]
        if rowRowid == '':
            sql = 'INSERT INTO "%s" VALUES (%s)'
            cur.execute(sql, values)
            %slastRowid = cur.lastrowid
        else:
            sql = 'UPDATE "%s" SET %s WHERE rowid=?'
            values.pop(%d)
            values.append(rowRowid)
            cur.execute(sql, values)
            %slastRowid = rowRowid
        i += 1
    
    """

#end of the code for the submit endpoint
submitNewCodeEnd = """
    conn.commit()
    return redirect('/')
    """

#code serving the edit endpoint
editCodeStart = """
    conn = getConn()
    cur = conn.cursor()
    cur.execute('SELECT rowid, * FROM "%s" WHERE rowid=?', (rowid, ))
    data%s = cur.fetchall()[0]
"""

fetchSpecificCode = """
    cur.execute('SELECT rowid, * FROM "%s" WHERE %s=?', (data%s[%d], ))
    data%s = cur.fetchall()
"""

editCodeEnd = """
    return render_template('%s.html', %srowid=rowid, %s, encoding='utf-8')
"""

#code for calling the isAuthorised function
authCheck = """
    if isAuthorised(%s) == False:
        abort(401)"""

#static code that is appended once at the bottom of the backend code
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
    def __init__(self, name:str, fieldType:str = 'TEXT', htmlType:str = 'text', unit:str = '', filtrable:bool = False, required:bool = False) -> None:
        if fieldType not in sqliteTypes or htmlType not in inputType:
            raise ValueError('Provided fieldType %s doesn\'t exist in sqlite.' % fieldType)
        if 'TABLE' in name:
            raise ValueError('Invalid field name')
        self.name = name
        self.fieldType = fieldType
        self.unit = unit
        self.filtrable = filtrable
        self.required = required # NOT NULL
        self.unique = False
        self.htmlType = htmlType
        self.hidden = False
        self.displayName = name

    def setDisplayName(self, name:str) -> None:
        """Sets the display name to the given name"""
        self.displayName = name

    def resetDisplayName(self) -> None:
        """Resets the display name to the normal name"""
        self.displayName = self.name

    def setUnique(self, isUnique:bool) -> None:
        """Sets the unique property"""
        self.unique = isUnique

class foreignField(field):
    """A field referencing a field in a different table. Creates a foreign key in SQL"""
    def __init__(self, referencedField:field, referencedTable:'dataType') -> None:
        if referencedField not in referencedTable.fields:
            raise ValueError("referencedField doesn't belong to referencedTable")
        self.name = referencedField.name
        self.fieldType = referencedField.fieldType
        self.unit = referencedField.unit
        self.filtrable = referencedField.filtrable
        self.required = referencedField.required
        self.htmlType = referencedField.htmlType
        self.referencedField = referencedField
        self.referencedTable = referencedTable
        self.hidden = False
        self.unique = False

class dataType:
    """A data type that will be stored in the CSM. Each dataType has it's own table in the db and holds a set amount of fields"""
    def __init__(self, name:str, fields:list[field] = None) -> None:
        if ' ' in name:
            raise ValueError('dataType names cannot contain names')
        self.name = name
        if fields != None:
            if not isinstance(fields, list):
                raise TypeError('The provided fields is not a list, but a %s' % fields.__class__.__name__)
            self.fields = fields
        else:
            self.fields = []
        self.children = []
        self.isChild = False
        self.parentName = ''
        self.primary = None #None = rowid
        self.displayName = name

    def getForeignField(self, referencedField:field) -> foreignField:
        """Returns a new foreign field object created based on the given field"""
        if referencedField not in self.fields:
            raise ValueError("Given referencedField doesn't belong to this dataType")
        return foreignField(referencedField, self)

    def getPrimaryForeignField(self) -> foreignField:
        """Returns a foreign field object based on the primary key or if that is None based on the rowid column"""
        if len(self.fields) < 1:
            raise ValueError("There are no fields assigned to this dataType")
        if self.primary != None:
            return foreignField(self.fields[self.fields.index(self.primary)], self)
        else:
            #we are going to work around our own restrictions
            rowidField = foreignField(self.fields[0], self)
            rowidField.name = 'rowid' + self.name
            rowidField.htmlType = 'text'
            rowidField.fieldType = 'INTEGER'
            rowidField.filtrable = True
            rowidField.required = True
            rowidField.setDisplayName(self.name)
            return rowidField

    def setPrimary(self, newPrimary:field) -> None:
        """Sets the provided newPrimary field as the primary key of this dataType. newPrimary must be already a field in this dataType"""
        if newPrimary == None: #we must allow the user to reset the primary key to default
            self.primary = newPrimary
        if newPrimary not in self.fields:
            raise ValueError("Provided newPrimary field doesn't belong in this dataType")
        if isinstance(self.primary, foreignField) and self.isChild:
            raise Exception("This dataType is a child and changing primary fields for children is forbidden")
        self.primary = newPrimary    
        newPrimary.unique = True
        if self.fields[0] != newPrimary: #swap the first field in the list with the new Primary one
            self.fields.remove(newPrimary)
            self.fields.insert(0, newPrimary)

    def addField(self, newField:field) -> None:
        """Adds the given field to this datatype"""
        if not isinstance(newField, field):
            raise TypeError('The provided newField is not a field, but a %s' % newField.__class__.__name__)
        if newField in self.fields:
            raise ValueError("Duplicate fields")
        self.fields.append(newField)

    def addDataField(self, newDataField:'dataType') -> None:
        if not isinstance(newDataField, dataType):
            raise TypeError('The provided newDataField is not a dataType, but a %s' % newDataField.__class__.__name__)
        pForeign = self.getPrimaryForeignField()
        pForeign.hidden = True
        newDataField.addField(pForeign)
        newDataField.setPrimary(pForeign)
        pForeign.unique = False
        self.fields.append(newDataField)
        newDataField.isChild = True

    def addChild(self, child:'dataType') -> None:
        """Sets the provided datatype as a child to this datatype"""
        if not isinstance(child, dataType):
            raise TypeError('The provided child is not a dataType, but a %s' % child.__class__.__name__)
        if child in self.children:
            raise ValueError('The provided child is already a child')
        self.children.append(child)
        for childField in child.fields:
            if childField.name == self.name:
                raise ValueError('Overlapping field names %s while attemting to addChild(). Field names of children cannot be named the same as the parent dataType' % self.name)
        newField = self.getPrimaryForeignField()
        child.addField(newField)
        child.setPrimary(newField)
        child.parentName = child.primary.name
        child.isChild = True
        #return child

    #i have decided that the submit code is now so comploicated and convoluted
    #it now needs it's own recursive function :)
    def __submitCodeFromClass(self, multiRow:bool=False) -> str:
        """Recursive method for generating code in the middle of the submit backend from a datatype"""
        code = ""
        plainFields = [f for f in self.fields if not isinstance(f, dataType)]
        SQLplaceholder = ', '.join('?' * len(plainFields))
        SQLupdatePlaceholder = ', '.join(('%s=?' % f.name for f in plainFields if not (isinstance(f, field) and self.primary==f)))
        if not multiRow:
            SQLvalueGetter = ', '.join(('data["%s%s-0"]' % (self.name, f.name) for f in plainFields))
            code += submitTypeCode % (self.name, self.name, SQLplaceholder, SQLvalueGetter, self.name, self.name, SQLupdatePlaceholder,
                                    SQLvalueGetter, self.name)
        else:
            code += submitMultiRowCode % (self.name, ', '.join(("'%s'" % f.name for f in self.fields if not isinstance(f, dataType))),
                                         self.primary.referencedTable.name, self.primary.referencedTable.name, self.name, self.name,
                                          self.name, SQLplaceholder, self.name, self.name, SQLupdatePlaceholder, self.fields.index(self.primary),
                                          self.name)
        for t in (t for t in self.fields if isinstance(t, dataType)):
            code += t.__submitCodeFromClass(dataType in (f.__class__ for f in self.fields))
        return code

    def __editCodeFromClass(self) -> str:
        """Recursive method for generating backend code for the edit endpoint from a datatype.\\
            Note the fact that this is not meant to operate on the primary datatype of a datapage, but it's field-children"""
        if self.primary.name == 'rowid' and self.primary.referencedField!=self.primary.name:
            code = fetchSpecificCode % (self.name, self.primary.name, self.primary.referencedTable.name, 0, self.name)
        else:
            code = fetchSpecificCode % (self.name, self.primary.name, self.primary.referencedTable.name, 
                                    self.primary.referencedTable.fields.index(self.primary.referencedField),
                                    self.name)
        for t in (t for t in self.fields if isinstance(t, dataType)):
            code += t.__editCodeFromClass()
        return code 

    def __generateValuePasser(self) -> list:
        """Recursive method generating a line of code that passes the variables to render_template"""
        valuePasser = ["data%s=data%s" % (self.name, self.name)]
        for t in (t for t in self.fields if isinstance(t, dataType)):
            valuePasser += t.__generateValuePasser()
        return valuePasser

    def render(self, pages:list['page'], pythonFile:io.FileIO = None, authLevel:int=0) -> None:
        """Creates the neccesary endpoints and html templates for this dataType"""
        template = environment.get_template('newTemplate.html')
        content = template.render(pages = pages, data = self, pk = self.getPrimaryForeignField().name)
        with open('./templates/%s.html' % self.name, 'w') as f:
            f.write(content)
        if pythonFile != None:
            #show form
            if self.isChild:
                pythonFile.write(argsPageCodeStart % ('new/%s/<%s>' % (self.name, self.parentName), self.name, self.parentName))
                pythonFile.write(authCheck % authLevel)
                pythonFile.write(argsPageCode % (self.name, '%s=%s' % (self.parentName, self.parentName)))
            else:
                pythonFile.write(normalPageCodeStart % ('new/%s' % self.name, self.name))
                pythonFile.write(authCheck % authLevel)
                pythonFile.write(genericPageCode % self.name)
            #submit form
            pythonFile.write(postPageCodeStart % ('new/%s/submit' % self.name, self.name + 'Submit'))
            pythonFile.write(authCheck % authLevel)
            pythonFile.write(submitNewCodeStart)
            pythonFile.write(self.__submitCodeFromClass())
            pythonFile.write(submitNewCodeEnd)
            #edit form
            pythonFile.write(argsPageCodeStart % ('edit/%s/<rowid>' % self.name, self.name + 'Edit', 'rowid'))
            pythonFile.write(authCheck % authLevel)
            pythonFile.write(editCodeStart % (self.name, self.name))
            for t in (t for t in self.fields if isinstance(t, dataType)):
                pythonFile.write(t.__editCodeFromClass())
            pythonFile.write(editCodeEnd % (self.name, self.name, ', '.join(self.__generateValuePasser())))

class page:
    """A static page in the CSM with preset content"""
    def __init__(self, name:str, htmlContent:str = '', footerContent:str = ''):
        if ' ' in name:
            raise ValueError("Page names cannot contain spaces")
        self.name = name
        self.home = False
        self.htmlContent = htmlContent
        self.footerContent = footerContent
        self.authLevel = 0

    def render(self, pages:list['page'], pythonFile:io.FileIO = None, home:bool = False) -> None:
        """Creates this page's template and writes the appropriate code to the pythonFile"""
        template = environment.get_template('genericTemplate.html')
        content = template.render(page=self, pages=pages, htmlContent=self.htmlContent, footerContent=self.footerContent)
        with open('./templates/%s.html' % self.name, 'w') as f:
            f.write(content)
        if pythonFile != None:
            if home:
                pythonFile.write(homePageCodeStart % self.name)
            else:
                pythonFile.write(normalPageCodeStart % (self.name) * 2)
            pythonFile.write(authCheck % self.authLevel)
            pythonFile.write(genericPageCode % self.name)

    def setAuthLevel(self, level:int) -> None:
        """Sets this page's min authority level. By default 0"""
        self.authLevel = level

    def fromHTML(self, filename:str) -> None:
        """Sets this page's html content to be the same as the contents of the file under the provided filename"""
        with open(filename, 'r') as f:
            self.htmlContent = f.read()

    def fromHTML(self, file:io.FileIO) -> None:
        """Sets this page's html content to be the same as the contents of the provided file"""
        self.htmlContent = file.read()

    def toPage(self) -> 'page':
        """Returns a new page object generated with this one's attributes"""
        return page(self.name, self.htmlContent, self.footerContent)

class dataPage(page):
    """Page that displays a table with all the data from the correspoding db table."""
    def setData(self, newDataType:dataType) -> None:
        """Sets which datatype this page should display"""
        if not isinstance(newDataType, dataType):
            raise TypeError('The provided newDataType is not a dataType, but a %s' % newDataType.__class__.__name__)
        self.dataType = newDataType

    def render(self, pages:list['page'], pythonFile:io.FileIO = None, home:bool = False) -> None:
        """Creates this page's template"""
        template = environment.get_template('dataTemplate.html')
        content = template.render(page=self, pages=pages, data=self.dataType, footerContent=self.footerContent)
        with open('./templates/%s.html' % self.name, 'w') as f:
            f.write(content)
        if pythonFile != None:
            if home:
                pythonFile.write(homePageCodeStart % self.name)
            else:
                pythonFile.write(normalPageCodeStart % (self.name, self.name))
            pythonFile.write(authCheck % self.authLevel)
            dataTypeFields = [f for f in self.dataType.fields if isinstance(f, dataType)]
            t = ['%sRows=%sRows' % (f.name, f.name) for f in dataTypeFields]
            t.append('%sRows=%sRows' % (self.dataType.name, self.dataType.name))
            pythonFile.write(dataPageCode)
            pythonFile.write(sqlFetchCode % (self.dataType.name, self.dataType.name))
            for f in dataTypeFields:
                pythonFile.write(sqlFetchCode % (f.name, f.name))
            pythonFile.write(argsPageCode % (self.name, ', '.join(t)))
        self.dataType.render(pages, pythonFile, self.authLevel)

class fetchPage(page):
    """Page that fetches contents of a json file and displays it as cards once loaded.\\
        The json should be a list of items with each item having these keys:
            -header: text to display into a card header
            -img: a link to an image that can be interpreted by the browser
            -title: a title of the card
            -content: the text to be displayed on the card
            -href: link at the bottom of the card pointing to the read more location
        All other keys will be interpreted as elements to be displayed in a bootsrap list group"""
    
    def setSource(self, filename:str) -> None:
        """Sets the provided filename as the source json file"""
        if not isinstance(filename, str):
            raise TypeError('The provided filename is not string')
        self.filename = filename

    def render(self, pages:list['page'], pythonFile:io.FileIO = None, home:bool = False) -> None:
        """Creates this page's template and writes the appropriate code to the pythonFile"""
        template = environment.get_template('fetchTemplate.html')
        content = template.render(page=self, pages=pages, footerContent=self.footerContent)
        with open('./templates/%s.html' % self.name, 'w') as f:
            f.write(content)
        if pythonFile != None:
            if home:
                pythonFile.write(homePageCodeStart % self.name)
            else:
                pythonFile.write(normalPageCodeStart % (self.name, self.name))
            pythonFile.write(authCheck % self.authLevel)
            pythonFile.write(fetchPageCode % (self.filename, self.name))

class db:
    """Database of a CSM app"""
    def __init__(self, filename:str = 'main.db'):
        conn = sqlite3.connect(filename)
        self.conn = conn
        try:
            #conn.execute('DROP TABLE IF EXISTS users')
            conn.execute('CREATE TABLE "users" ( "login" TEXT NOT NULL UNIQUE, "pass" TEXT NOT NULL, "salt" TEXT, "auth" INTEGER)')
        except sqlite3.OperationalError:
            print("DB is already here.")
        conn.commit()
        self.filename = filename

    def addData(self, newDataType:dataType) -> None:
        """Creates the needed table for the dataType in the db"""
        if not isinstance(newDataType, dataType):
            raise TypeError('Provided newDataType is not dataType but %s' % newDataType.__class__.__name__)
        cur = self.conn.cursor()
        cur.execute('DROP TABLE IF EXISTS "%s"' % newDataType.name)
        sql = 'CREATE TABLE "%s" ( %s )'
        sqlInner = []
        sqlEnd = []
        for field in newDataType.fields:
            if isinstance(field, dataType):
                #sqlInner.append('"%sTABLE" TEXT' % field.name)
                self.addData(field)
            else:
                sqlInner.append('"%s" %s' % (field.name, field.fieldType))
            if isinstance(field, foreignField):
                sqlEnd.append('FOREIGN KEY(%s) REFERENCES "%s"(%s)' % (field.name, field.referencedTable.name, field.referencedField.name))
        if newDataType.primary != None:
            #ok so this might seem weird... but is necessary
            #the logic is simple. 
            #If unique isnt True (its set by default when something is set as primary) then It's a user intervention
            #to make the rendering think its primary but not be in SQL
            if newDataType.primary.unique != False:
                sqlEnd.append('PRIMARY KEY("%s")' % newDataType.primary.name)
        sqlInner += sqlEnd
        sql = sql % (newDataType.name, ','.join(sqlInner))
        try:
            cur.execute(sql)
        except sqlite3.OperationalError as e:
            print(e)
            print(sql)
        self.conn.commit()

class app:
    """A CSM app"""
    def __init__(self, name:str):
        self.name = name
        os.makedirs('./%s/templates' % self.name, exist_ok=True)
        os.chdir('./%s' % self.name)
        self.db = db("%s\main.db" % os.getcwd()) #initialise the database
        self.pages = []
        self.home = None
        self.footer = ''

    def addPage(self, newPage:page) -> None:
        """Adds the page to the app"""
        if not isinstance(newPage, page):
            raise TypeError('Provided newPage is not a page but %s' % newPage.__class__.__name__)
        if newPage in self.pages:
            raise Exception('Page %s already is assigned to this app' % newPage.name)
        self.pages.append(newPage)

    def setHome(self, newPage:page) -> None:
        """Sets the given page as home"""
        if not isinstance(newPage, page):
            raise TypeError('Provided newPage is not a page but %s' % newPage.__class__.__name__)
        if newPage not in self.pages:
            raise Exception('Page %s is not assigned to %s app' % (newPage.name, self.name))
        self.home = newPage

    def setFooter(self, footer:str) -> None:
        """Sets this app's global footer that will be present in every page unless a page's footerContent attribute has length > 0"""
        self.footer = footer

    def render(self) -> None:
        """Creates the app"""
        if self.home == None:
            self.home = self.pages[0]
        print('Starting app render...')
        shutil.copytree('../readyTemplates', './templates', dirs_exist_ok=True)
        shutil.copytree('../static', './static', dirs_exist_ok=True)
        shutil.copy('../addUser.py', './addUser.py', follow_symlinks=True)
        with open('../appSkeleton.py', 'r') as f:
            skeleton = f.read()
        with open('./app.py', 'w') as f:
            f.write(skeleton % os.path.basename(self.db.filename))
            for page in self.pages:
                if len(page.footerContent) == 0:
                    page.footerContent = self.footer
                if isinstance(page, dataPage):
                    self.db.addData(page.dataType)
                elif isinstance(page, fetchPage):
                    if not os.path.isfile(page.filename):
                        with open(page.filename, 'w') as s: #create the source file
                            s.write('{}')
                page.render(self.pages, f, page == self.home)
            f.write(codeFooter)
        self.db.conn.close()
        print('App rendered')

    def launch(self, process:str = 'python') -> None:
        """Launches the app"""
        os.system("%s ./app.py" % process)
