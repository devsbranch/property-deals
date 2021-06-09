# Property Deals  

[![JavaScript Style Guide: Good Parts](https://img.shields.io/badge/code%20style-goodparts-brightgreen.svg?style=flat)](https://github.com/dwyl/goodparts "JavaScript The Good Parts")
[![Build Status](https://travis-ci.org/{ORG-or-USERNAME}/{REPO-NAME}.png?branch=master)](https://travis-ci.org/{ORG-or-USERNAME}/{REPO-NAME})
[![Join the chat at https://gitter.im/{ORG-or-USERNAME}/{REPO-NAME}](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/property-deals/?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

The purpose of this application is to provide a platform  where 
people can post properties for sale or rent e.g Houses.



## Getting Started 🚀

These instructions will get you a copy of the project up and running on your local machine.

### Prerequisites 📋

You'll need [Git](https://git-scm.com) and [Python](https://www.python.org/downloads/) (which comes with `pip`) installed on your computer.

```
python@3.6.0 or higher
pip@20.0 or higher
git@2.20.0 or higher
```

---

## How To run application 🔧

#### Don't forget to create a virtual environment and activate.

From your command line, first clone property-deals:
### This command works on Linux and Mac and Windows

```bash
# Clone this repository
git clone https://github.com/devsbranch/property-deals.git

# Go into the repository
cd property-deals
```

Then you can install the dependencies using PIP:

### On Linux and Mac
```bash
# Install dependencies
$ pip3 install -r requirememts.txt

# Start development server
$ python3 run.py
```

### On Windows
Use Powershell, Command Prompt or Windows Terminal

```bash
# Install dependencies
PS> pip install -r requirememts.txt

# Start development server
PS> python run.py

```

##Setting Up the Database
Once you run the application for the first time, it will automatically create an SQlite database file if that's what is configured. 
Otherwise, you have to create a database. A Postgres database is preferred but feel free to use whichever you want.


### Connection String
In your application, you have to configure the flask application to use the Postgres database.
Your connection string format should be like this: 
`postgresql+psycopg2://<user>:<password>@<host>:<port>/<database>`
You have to set a password for connecting to Postgres or else Valentina Studio won't connect.
Here is an example on a connection string `postgresql+psycopg2://postgres:postgres@localhost:5432/property_deals`


##### To start using the app, start the server has and go to this url `http://localhost:5000/` and you will see the website running on a Development Server and will show you the index/home page. Click on register to sign up.
![](docs/images/register.png)

##### Fill in your login credentials you used to sign up and click login.
![](docs/images/login.png)

#####
Once logged in you can browse through the application and test some features. You can open a PR for some features you think should be added.


## Technologies used 🛠️
- [Flask](https://flask.palletsprojects.com/en/1.1.x/) - A Python Web Development Framework
- [PostgreSQL](https://www.postgresql.org/about/) - PostgreSQL is a free and open-source relational database management system system that uses and extends the SQL language combined with many 
  features that safely store and scale the most complicated data workloads.

## Features
- DBMS: SQLite, PostgreSQL (production) 
- DB Tools: SQLAlchemy ORM, Flask-Migrate (schema migrations)
- Session-Based authentication (via **flask_login**), Forms validation
- Deployment scripts: Docker, Gunicorn / Nginx, Heroku

## Authors

- [**Jachin Manda**](https://github.com/Jachin-Manda) (Lead Developer)
- [**Alison Mukoma**](https://github.com/sonlinux)

## Status
Still under development
