# openCMS

## An open python CMS webapp generator

This package provides a simple yet effective framework that will create a fully functional python Flask webapp capable of displaying data from a user defined data structure in a really short time. This includes all that is needed to run the app: backend python script, the sqLite database and the jinja templates.

## How it works

1. You create a script using the openCSM classes that defines a webapp
2. You run the script ensuring all the necessary files are there
3. openCSM based on your defined objects generates a backend, database and jinja templates for your webapp.
If you did everything properly it should be ready to run.  

Amazing isn't it? Don't believe what I'm claiming here?
Let's look at an example of how to create a webapp using openCSM:

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
thisApp.addPage(testPage)
thisApp.setHome(testPage)
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
A more detailed usage example you can find [here](./testRender.py) and the result of running that script is in [this folder](./testCSM/).

## Data structure

The dataType class serves as the python representation of a table.
A single dataType may hold a number of fields each with their own attributes(or foreignFields that create foreign keys in the rendering step), and more interestingly may be set as children to each other, which creates a 1:n relation between the dataTypes with the child being on the n end of the relation.
During the rendering step this data structure is translated to a sqLite database, and in theory this structure may be translated to a database completely separately from the rendering process.

## Intended workflow

Naturally you may use this framework for many things, however IMO it's best to use it to simply speed up the development process of a webapp.
Simpler apps may be completed outright using this framework, but more complicated apps utilizing for example weak relationships or m:n relationships in their databases will need to be built up from the fundament this framework provides manually.
But the time savings from simply automating the most repetitive parts of web development cannot be underestimated.

## License

[![CCimg](https://i.creativecommons.org/l/by/4.0/88x31.png)](http://creativecommons.org/licenses/by/4.0/)  
This work is licensed under a [Creative Commons Attribution 4.0 International License](http://creativecommons.org/licenses/by/4.0/).  
