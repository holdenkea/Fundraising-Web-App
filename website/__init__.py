#allows us to import the website folder and whatever is inside the init.py
#acts as a package and will run automatically

from flask import Flask
from flask_login import LoginManager   
from bson import ObjectId
from .models import User
from . import db
from .scrape_wiki_cities import wiki_main
from .scrape_google_places import google_main
import asyncio

#initializes the flask web app
def create_app():                       
    app = Flask(__name__)

    secret_key, database_uri = db.get_app_config()

    #encrypts and secures the session data
    app.config['SECRET_KEY'] = secret_key  
    app.config['DATABASE_URI'] = database_uri

    #importing the blueprints that contain the url locations for the application
    from .views import views    
    from .auth import auth     

    #makes '/' the prefix needed to access whatever is inside of views and auth blueprints
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    db.check_connection()
    db.create_users_database()
    db.create_location_database()
    db.create_place_database()

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

        user_document = db.usersCollection.find_one({"_id" : ObjectId(str(id))})

        if user_document:
            user = User.documentToUserInst(user_document)
            return user
        else:
            return None
    
    #Scrapes wikipedia page about municipalities wikipedia page   
    #import werkzeug.serving
    #if not werkzeug.serving.is_running_from_reloader():
    #    print("scrapeWiki call")
    #    scrape_wiki_locations()
    
    return app

def scrape_wiki_locations():
    asyncio.run(wiki_main())
