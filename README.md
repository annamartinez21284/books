# Project 1

Web Programming with Python and JavaScript

## Description

This is a very simple book review site for CS50Web written in Python/Flask that uses raw SQL (Postgres),
makes an API call to Goodreads and grants users API access via a GET request.
Full details: https://docs.cs50.net/web/2020/x/projects/1/project1.html

The main files used are:
* application.py - contains the application
* create.py - creates the schema (in my case hosted on Heroku)
* import. py - needs to be run to upload the books.csv file into the database, once created
* all the html-templates in the templates directory, enhanced with a simple css file and Bootstrap
* helpers.py - contains a function that ensures users are logged in when needed
