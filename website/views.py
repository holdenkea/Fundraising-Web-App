# stores the views and url endpoints for frontend of website
# this is where the standard routes go, i.e. homepage, etc. but NOT login, as it is related to auth

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user #current user used to detect if user is logged in or not
from .scrape_google_places import google_main
import asyncio


# from website.fundscraper import placeOptions, buildMapsPlaceQuery
from website.scrape_google_places import placeOptions
from . import db

views = Blueprint('views', __name__)  # sets up a Blueprint for flask application

#route for the home page
@views.route('/')   #homepage so we use slash '/' and will run the function everytime we go to the '/' route
@login_required     #cannot get to home page unless you are logged in
def home():
    return render_template("home.html", user=current_user, places=placeOptions)

#route for the submit button on the home page
@views.route('/submit', methods=['POST'])
def submit():
    state = request.form.get('state')
    city = request.form.get('city')
    place = request.form.get('place')

    #call buildMapsPlaceQuery in fundscraper
    # buildMapsPlaceQuery(city, state, place) 

    # call scrape_maps_places function in scrape_google_places
    asyncio.run(google_main(city, state, place))

    exit(3)
    #return f'State: {state}, City: {city}, Href: {cityHref}'

#below routes bring the database states to be used in the frontend
@views.route('/states')
def get_states():
    query = request.args.get('query','')
    states_cursor = db.locationsCollection.find({"state": {"$regex": query, "$options": "i"}}, {"_id": 0, "state": 1})
    statesList = [state["state"] for state in states_cursor]
    statesList.sort()

    return jsonify(statesList)

@views.route('/cities/<state>')
def get_cities(state):
    stateDocument  = db.locationsCollection.find_one({"state": state}, {"_id": 0, "cities": 1})
    print(stateDocument)

    if not stateDocument or "cities" not in stateDocument:
        return jsonify([])

    cities = stateDocument["cities"]
    cities = sorted(cities)

    city_list = [{"city": city} for city in cities]

    return jsonify(city_list)

# once the above is defined we now need to register these blueprints in the init.py file