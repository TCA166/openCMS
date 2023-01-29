# openCMS

## An open python CMS webapp generator

This package provides a simple yet effective interface that will create a fully functional python Flask webapp intended to be used as a CMS(Customer Management System), but in theory may be customised to display anything.

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
Then you may customise the end result of the script to your desires, adding new features or changing whatever you want!  
A more detailed usage example you can find [here](./testRender.py)
  
