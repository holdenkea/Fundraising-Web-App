from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import urllib3
import time
from time import sleep

from .models import Place
from .__init__ import usersCollection, locationsCollection

from pymongo.mongo_client import MongoClient

from concurrent.futures import ThreadPoolExecutor, as_completed # allows us to use a context manager to give our run function to
# **********************************************************************************************************
# Used to set the browser options, in this case for the Chrome Webdriver
# **********************************************************************************************************
def setOptionsForBrowser():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.page_load_strategy = 'normal' # normal is waiting until entire webpage like CSS, images, frames, are loaded
                                          # there is also eager, meaning DOM is accessable and ready to interact
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    max_retries = 5
    for attempt in range(max_retries):
        try:
            browser = webdriver.Remote(
                command_executor="http://selenium-hub:4444/wd/hub", # Correct endpoint for WebDriver
                options=options
            )
            break  # Exit the loop if successful
        except urllib3.exceptions.MaxRetryError as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            sleep(10)  # Wait for 10 seconds before retrying
    else:
        print("All attempts to connect to the Selenium Hub failed.")
        return
    
    return browser

# **********************************************************************************************************
# Below functions used for finding fundraising opportunities near someone  
# functions: buildPlaceQuery, scrapePlaceData
#   buildPlaceQuery-takes a city, state, and placeRequested and builds the correct URL for google maps                
#       - also calls scrapePlaceData and passes it the built URL, city, state, and type of place requested
#   scrapePlaceData-gets the name and URL of every Place near the requested area
# **********************************************************************************************************

# restaurants, things to do, dessert/cafe/boba/bakery are all places that can be requested
def buildMapsPlaceQuery(city, state):
    placeOptions = [
        "restaurants",
        "dessert",
        "things+to+do"
    ]

    for place in placeOptions:
        queryURL = f"https://www.google.com/maps/search/{place}+near+{city}+{state}"
       
        #add concurrency here
        getAllPlacesNearby(queryURL, city, state)

def getAllPlacesNearby(queryURL, city, state):
    browser = setOptionsForBrowser()
    browser.get(queryURL)

# scrape all businesses in area with selenium
# and get the list of all websites in the area

# list of all websites
# for website in websites

# if website uses javascript
#   scrape using selenium
# else
#   scrape using something else

# **********************************************************************************************************
# Below functions used to scrape Wikipedia for all municipalities by state
#   - this data is later used for the autofill dropdown menu on the frontend which filters by state and city
# Not called every time app is ran
# **********************************************************************************************************

def buildWikiQuery():
    queryURL = "https://en.wikipedia.org/wiki/Category:Lists_of_cities_in_the_United_States_by_state"
    getAllStateLists(queryURL)

def getAllStateLists(queryURL):
    browser = setOptionsForBrowser()
    browser.get(queryURL)
    start_time = time.time()
 
    try:
        navbox = WebDriverWait(browser,10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.nowraplinks.hlist.mw-collapsible.expanded.navbox-inner.mw-made-collapsible'))
        )

        state_navbox = navbox.find_element(By.CSS_SELECTOR, '.navbox-list-with-group.navbox-list.navbox-odd')
        unordered_list = state_navbox.find_element(By.TAG_NAME, 'ul')
        list_elements = unordered_list.find_elements(By.TAG_NAME, 'li')
        hrefs = []

        # to get state, href, and empty city dict in the database
        for list in list_elements:
            a_tag = list.find_element(By.TAG_NAME, 'a')
            state = a_tag.text
            href = a_tag.get_attribute('href')
            hrefs.append(href)

            if not locationsCollection.find_one({"state" : state}):
                stateDocument = {}
                stateDocument |= {'state' : state}
                stateDocument |= {'href' : href}
                stateDocument |= {'cities' : ""}
                locationsCollection.insert_one(stateDocument)
        
    except Exception as e:
        print(f"Error waiting for navbox: {e}")  
    
    finally:
        browser.quit()

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(getAllCityLists, href) for href in hrefs]
        for future in as_completed(futures):
            future.result()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"scraping took: {elapsed_time: .2f} seconds")

    # first attempt no selenium grid 689.69 seconds
    # second attempt no selenium grid 750.25 seconds
    # third attempt 241.81 seconds java jar file max workers
    # fourth attempt docker-compose with 4gb shm size 239 seconds but web app doesn't open
    # fifth attemp docker-compose with 6gb shm size 232 seconds web app still doesn't open

def getAllCityLists(href):
    browser = setOptionsForBrowser()
    browser.get(href)
    
    try:
        table = WebDriverWait(browser,10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.wikitable.sortable.jquery-tablesorter'))
        )

        # accounts for structural differences in wikipedia pages account for different element names 
        if table.find_element(By.TAG_NAME, 'a').get_attribute('title') == 'County seat':  
            table = browser.find_element(By.CSS_SELECTOR, '.wikitable.sortable.plainrowheaders.jquery-tablesorter')

        table_body = table.find_element(By.TAG_NAME, 'tbody')
        tr_tags = table_body.find_elements(By.TAG_NAME, 'tr')
        cityDocuments = []

        for tr_tag in tr_tags:
        
            class_attribute = tr_tag.get_attribute('class')
            if class_attribute == 'sortbottom':     #checks for the end of the table
                break

            a_tag = tr_tag.find_element(By.TAG_NAME, 'a')
            city = a_tag.text
            cityHref = a_tag.get_attribute('href')

            print(f"city: {city}, href: {cityHref}")

            if city and cityHref:
                cityDocument = {}
                cityDocument |= {'city' : city}
                cityDocument |= {'href' : cityHref}
                cityDocuments.append(cityDocument)

    except Exception as e:
        print(f"Error waiting for table: {e}")

    finally:
        browser.quit()

    locationsCollection.update_one(
        {"href" : href}, 
        {"$set" : {"cities" : cityDocuments}}
    )


# **********************************************************************************************************
# Notes for starting Selenium Grid
#   - running through java jar file
#       - java -jar selenium-server-<version>.jar standalone
#           (java -jar selenium-server-4.23.0.jar standalone --selenium-manager true)
# Once this is started Grid is ran on local machine
# **********************************************************************************************************