# stores the views and url endpoints for frontend of website
# this is where the standard routes go, i.e. homepage, etc. but NOT login, as it is related to auth

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user #current user used to detect if user is logged in or not

from .__init__ import locationsCollection

views = Blueprint('views', __name__)  # sets up a Blueprint for flask application

#route for the home page
@views.route('/')   #homepage so we use slash '/' and will run the function everytime we go to the '/' route
@login_required     #cannot get to home page unless you are logged in
def home():
    return render_template("home.html", user=current_user)

#route for the submit button on the home page
@views.route('/submit', methods=['POST'])
def submit():
    state = request.form.get('state')
    city = request.form.get('city')
    cityHref = request.form.get('cityHref')
    place = request.form.get('place')
    # cities and states should be in database at this point
    # need to take the state, city, and cityHref and go into the cityHref




    #call fundscraper to build the query to get the coordinates for the city
    #buildMapsPlaceQuery(city, state, place_type) FROM FUNDSCRAPER

    #return f'State: {state}, City: {city}, Href: {cityHref}'

#below routes bring the database states to be used in the frontend
@views.route('/states')
def get_states():
    query = request.args.get('query','')
    states_cursor = locationsCollection.find({"state": {"$regex": query, "$options": "i"}}, {"_id": 0, "state": 1})
    statesList = [state["state"] for state in states_cursor]
    return jsonify(statesList)

@views.route('/cities/<state>')
def get_cities(state):
    stateDocument  = locationsCollection.find_one({"state": state}, {"_id": 0, "cities": 1})
    if not stateDocument or "cities" not in stateDocument:
        return jsonify([])

    cities = stateDocument["cities"]
    city_list = [{"city": city["city"], "href": city.get("href", "")} for city in cities if "city" in city]

    return jsonify(city_list)

# once the above is defined we now need to register these blueprints in the init.py file