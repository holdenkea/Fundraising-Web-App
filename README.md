## Table of Contents
- [About](#about)
- [Getting Started](#getting-started)
- [Running](#running-the-program)
- [Feature Demo](#Feature Demo)
  - [Login Page](#login-page)
    - 
  - [Backend](#backend)
  - [Database](#database)

## About
Welcome to my Fundraising Web App repository! This web application utilizes my Google Maps Web Crawler that scrapes business data, checks if they offer fundraising opportunities, and outputs the results on a Flask based web app. This project was inspired by my role in the Filipino American Association at SSU, where I was in charge of the Fundraising Operations. A lot of the responsibility required either cold calling places and asking if they offered fundraising, or looking through every single restaurant's website for keywords like "Community," "Fundraising," "Foundations," etc, so I wanted a way to automate this process.

The year I started this project was the semester of my Database management class. I originally had a Selenium-Grid based web crawler that populated my MongoDB cluster, but that required a lot of overhead and wasn't fast enough, so I moved onto using concurrent asynchronous functions and Playwright. 

## Getting Started
```
# build docker image
docker-compose build

# start docker image
docker-compose up  
```
## Running the Program
This is currently a local application and is set up for port 5000.

Visit http://localhost:5000

## Feature Demo

### Signing Up

### User Info in Database

### Logging In

### Fundraising Search


