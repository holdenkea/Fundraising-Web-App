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

uri = 'mongodb+srv://' + username + ':' + password + '@' + cluster + '.' + identifier + '.mongodb.net/'
client = MongoClient(uri)

user_db = client.user_db
usersCollection = user_db["user_collection"]

location_db = client.location_db
locationsCollection = location_db["location_collection"]

def check_connection():
    try:
        client.admin.command('ping')
        print("Pinged Fundraiser Project. Successfully connected to MongoDB")
    except Exception as e:
        print("e")

def create_app():                       #how flask is initialized
    app = Flask(__name__)
    app.config['SECRET_KEY'] = credentials.get('SECRET_KEY')   #for encrypting and securing session data
    app.config['DATABASE_URI'] = uri

    from .views import views    #telling flask that we have blueprints that have different urls for application
    from .auth import auth      #same for auth

    app.register_blueprint(views, url_prefix='/') #to access whatever is inside of views, it needs to be prefixed by whatever
                                                  #is assigned to url_prefix, slash means no prefix
    app.register_blueprint(auth, url_prefix='/')

    from .models import User,Place #to make sure we load models.py before we initialize and find database

    check_connection()
    create_users_database()
    create_location_database()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'    #where flask redirects user if user is not logged in
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
    
    # Uncomment below to scrape wikipedia page about municipalities wikipedia page   
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
