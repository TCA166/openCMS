from openCMS import app, page, dataPage, dataType, field

newApp = app('testCSM') #create the new app object
#create a new page - a generic one with text
homePage = page('Home', 'Welcome to this very demonstrative <b>testCMS</b>')
newApp.addPage(homePage)
newApp.setHome(homePage) # set this page as home
#create a second page, this one holding a datatype with three fields
name = field('Name', filtrable=True, required=True)
surname = field('Surname', filtrable=True)
age = field('Age', unit='yrs')
clients = dataType('Client', [name, surname, age])
clientsPage = dataPage('Clients')
clientsPage.setData(clients)
newApp.addPage(clientsPage)
#create a third page, this one holding a child datatype to the clients datatype
productName = field('Product name')
price = field('Price', htmlType='number', unit='$')
product = dataType('Product', [productName, price])
product = clients.addChild(product)
productPage = dataPage('Products')
productPage.setData(product)
newApp.addPage(productPage)
#create a fourth page, displaying a secret datatype
secret = field('Secret')
secretType = dataType('superSecret', [secret])
secretPage = dataPage('secretPage')
secretPage.setAuthLevel(1)
secretPage.setData(secretType)
newApp.addPage(secretPage)
#finally render and launch
newApp.render()
newApp.launch() #this optional but useful for fast debugging