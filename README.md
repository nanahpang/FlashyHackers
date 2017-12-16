# Meeting Secretary

This repo is the final project of team FlashyHackers in COMSW4156 (Advanced Software Engineering).

## Try online!
Here is our [Meeting Secretary](https://meeting-secretary-188318.appspot.com).

## Technology

* Python3
* Django
* jQuery
* Javascript
* MySQL
* Bootstrap

## Requirement

* (Use virtualenv for python3 will be easier to use and manage)

* Django == 1.10

      pip install django
* MySQL 
    
    Download from [MySQL](https://www.mysql.com/downloads/) website.

* You can use pip3 install -r requirements.txt to install all the dependencies.



## Setup:

### Run locally:

* Use MySQL create database:

      create database MeetingSecretary

* Modify the configuration in settings.py:

        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': 'MeetingSecretary'
                'USER': 'your username',
                'PASSWORD': 'your password',
                'HOST': '',
            } 
        }
    
* Configure the database: 
                    
      python manage.py migrate

* patch the schedule package
      ./patch_script

* Open your command line, and go to the root directory
* Start the server: 
            
      python manage.py runserver
* Open the page 127.0.0.1:8000/login in web browser, then welcome to our Meeting Secretary! 

### Run on Google Cloud: 
* You can refer to this [link](https://cloud.google.com/python/django/flexible-environment) to deploy our meeting secretary on [Google Cloud](https://cloud.google.com/).
    
## Project Iteration:

https://trello.com/flashyhacker

## Other Documents: 

Static analysis : pylint

Continuous Integration & build tool: Travis CI

All reports are stored in 'document' directory.
