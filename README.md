# openCMS

## An open python CMS webapp generator

This package provides a simple yet effective interface that will create a fully functional python Flask webapp intended to be used as a CMS(Customer Management System), but in theory may be customized to display anything.

## Usage

Let's generate a simple webapp. Ensure that the static, templates, readyTemplates, addUser.py and appSkeleton.py are next to the openCMS.py

```Python
#first we import the needed classes
from openCMS import app, page, dataPage, field, dataType
#then we create the app object
thisApp = app('testCMS')
#next a generic page object
testPage = page('Home', thisApp.name)
#we then add this page to the app
thisApp.setHome(testPage)
thisApp.addPage(testPage)
#after that let's create a page for displaying sql data
testDataPage = dataPage('Data')
#each dataPage holds a single dataType, and each dataType holds n fields
a = field('text1', filtrable=True)
b = field('text2')
t = dataType('testType', [a, b])
#having created the dataType let's set the dataPage to hold it
testDataPage.setData(t)
thisApp.addPage(testDataPage)
#finally let's render the app
thisApp.render()
```

Quite fast and easy isn't it?  
Then you may customize the end result of the script to your desires, adding new features or changing whatever you want!  
A more detailed usage example you can find [here](./testRender.py)

## How it works

This framework is consists of several files. Most notably the openCMS.py file which contains the classes used for the rendering itself,
appSkeleton.py which contains the backbone backend code that is the appended automatically during rendering by classes in openCMS.py, and the different template templates which are rendered using jinja to form the templates in the rendered app.
Additionally some files are simply copied over to the result directory like the files in readyTemplates, static and the addUser.py utility.

## Page types

This framework has built in support for three types of pages.

- Static pages\\

These are represented by the default page class. These simply display static html content loaded at app render.
The static html content can be loaded from a file using the fromHTML() method.

- Data pages\\

These simply display content within a single sql table. Additionally they contain buttons for interaction with the data.

- Fetch pages\\

These display a bootsrap card deck made up of cards, which are created based on content in a given json file.

## Intended workflow

Naturally you may use this framework for many things, however IMO it's best to use it to simply speed up the development process of a webapp.
Simpler apps may be completed outright using this framework, but more complicated apps utilizing for example weak relationships or m:n relationships in their databases will need to be built up from the fundament this framework provides manually.
But the time savings from simply automating the most repetitive parts of web development cannot be underestimated.

## License

[![CCimg](https://i.creativecommons.org/l/by/4.0/88x31.png)](http://creativecommons.org/licenses/by/4.0/)  
This work is licensed under a [Creative Commons Attribution 4.0 International License](http://creativecommons.org/licenses/by/4.0/).  
