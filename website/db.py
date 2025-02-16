
from pymongo.mongo_client import MongoClient
import urllib.parse
from credentials import credentials

username = urllib.parse.quote_plus(credentials.get('DATABASE_USER'))
password = urllib.parse.quote_plus(credentials.get('DATABASE_PASSWORD'))
cluster = credentials.get('DATABASE_CLUSTER')
identifier = credentials.get('DATABASE_IDENTIFIER')

#credentials for MongoDB
uri = 'mongodb+srv://' + username + ':' + password + '@' + cluster + '.' + identifier + '.mongodb.net/'

client = MongoClient(uri)

#gets all of the users in the database
user_db = client.user_db
usersCollection = user_db["user_collection"]

#gets all of the locations in the database 
location_db = client.location_db
locationsCollection = location_db["location_collection"]

#gets all of the places in the database
place_db = client.place_db
placesCollection = place_db["place_collection"]


#checks the connection to the database
def check_connection():
    try:
        client.admin.command('ping')
        print("Pinged Fundraiser Project. Successfully connected to MongoDB")
    except Exception as e:
        print("e")

def create_users_database():
    if usersCollection.name not in user_db.list_collection_names():
        user_db.create_collection("user_collection")

def create_location_database():
    if locationsCollection.name not in location_db.list_collection_names():
        location_db.create_collection("location_collection")

def create_place_database():
    if placesCollection.name not in place_db.list_collection_names():
        place_db.create_collection("place_collection")

def get_app_config():
    secret_key = credentials.get('SECRET_KEY')
    return secret_key, uri