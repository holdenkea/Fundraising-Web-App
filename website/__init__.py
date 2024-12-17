#allows us to import the website folder and whatever is inside the init.py
#acts as a package and will run automatically

from flask import Flask

from pymongo.mongo_client import MongoClient
import urllib.parse
from credentials import credentials
from flask_login import LoginManager   
from bson import ObjectId

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

#checks the connection to the database
def check_connection():
    try:
        client.admin.command('ping')
        print("Pinged Fundraiser Project. Successfully connected to MongoDB")
    except Exception as e:
        print("e")

#initializes the flask web app
def create_app():                       
    app = Flask(__name__)

    #encrypts and secures the session data
    app.config['SECRET_KEY'] = credentials.get('SECRET_KEY')   
    app.config['DATABASE_URI'] = uri

    #importing the blueprints that contain the url locations for the application
    from .views import views    
    from .auth import auth     

    #makes '/' the prefix needed to access whatever is inside of views and auth blueprints
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    #imports the User and Place classes from models
    from .models import User,Place 

    check_connection()
    create_users_database()
    create_location_database()

    #how flask redirects user if user is not logged in
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)                

    @login_manager.user_loader
    def load_user(id):
        if id is None or id == 'None':
            return None
        
        try: 
            object_id = ObjectId(str(id))
        except:
            return None

        user_document = usersCollection.find_one({"_id" : ObjectId(str(id))})

        if user_document:
            user = User.documentToUserInst(user_document)
            return user
        else:
            return None
    
    #Scrapes wikipedia page about municipalities wikipedia page   
    #import werkzeug.serving
    #if not werkzeug.serving.is_running_from_reloader():
    #    print("scrapeWiki call")
    #    scrape_wiki_places()

    return app


def create_users_database():
    if usersCollection.name not in user_db.list_collection_names():
        user_db.create_collection("user_collection")

def create_location_database():
    if locationsCollection.name not in location_db.list_collection_names():
        location_db.create_collection("location_collection")

def scrape_wiki_places():
    from .fundscraper import buildWikiQuery
    buildWikiQuery()
