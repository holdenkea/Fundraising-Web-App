## Table of Contents
- [About](#about)
- [Getting Started](#getting-started)
- [Running](#running-the-program)
- [Features](#feature-demo)
  - [Signing Up](#signing-up)
  - [Logging In and Search Form](#logging-in-and-search-form)
  - [Fundraising Search Results](#fundraising-search-results)
  - [Verifying Results](#verifying-results)
  - [Database Structure](#database-structure)

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

Visit http://localhost:5000 after running docker-compose up.

## Feature Demo

### Signing Up

https://github.com/user-attachments/assets/fae4a31c-a879-412e-8bb7-84815dea74af

### Logging In and Search Form

https://github.com/user-attachments/assets/feed040e-dc48-4e2d-beef-3f27594f5ae0

### Fundraising Search Results

https://github.com/user-attachments/assets/65df222f-3f2c-4de6-b335-79bdfb8ec675

### Verifying Results 

https://github.com/user-attachments/assets/7391236a-9d4f-490d-b370-9b55ccc884bc

### Database Structure
To get the information for the dropdown menus of cities and states, I made a seprate web crawler to get the Wikipedia city and state information. Below is an example of a document in my database, which holds a list of cities for each state, and the wikipedia link I got them from.

![Example Document in Database](https://github.com/user-attachments/assets/16849d3f-db83-4c56-a8bc-2fadb4405c72)

