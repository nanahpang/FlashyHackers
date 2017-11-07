# Meeting Secretary

This repo is the final project of team FlashyHackers in COMSW4156 (Advanced Software Engineering).

## Technology

* Python3
* Django >= 1.10
* jQuery
* Javascript
* MySQL

## Requirement

* Django >= 1.10

      pip install django
      
* Some packages:

      pip install simplejson
      pip install django-scheduler
      pip install django-bower
      pip install directmessages

* MySQL 
    
    Download from [MySQL Website](https://www.mysql.com/downloads/).
    
## Setup:

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

## Running:
* Open your command line, and go to the root directory
* Start the server: 
            
      python manage.py runserver
* Open the page 127.0.0.1:8000/login in web browser, then welcome to our Meeting Secretary! 
    
## Project Iteration:

https://trello.com/flashyhacker
