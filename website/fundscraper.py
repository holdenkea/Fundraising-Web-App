# convert selenium to playwright
# i cant believe i didn't use element.click on selenium

# switch to playwright because it is faster




from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException

import urllib3
import time
from time import sleep

from .models import Place
from .__init__ import usersCollection, locationsCollection, placesCollection

from pymongo.mongo_client import MongoClient

# gives the run function to a context manager for multithread execution
from concurrent.futures import ThreadPoolExecutor, as_completed 

# Used to set the browser options, in this case for the Chrome Webdriver
def setOptionsForBrowser():
    options = webdriver.ChromeOptions()
   # options.add_argument("--headless")
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



#different place types to research from
placeOptions = [
        "restaurants",
        "dessert",
        "things to do"
    ]

# restaurants, things to do, dessert/cafe/boba/bakery are all places that can be requested
def buildMapsPlaceQuery(city, state, place):
    query = f"{place} near {city} {state}"  
    queryURL = f"https://www.google.com/maps/search/{place}+near+{city}+{state}"
    
    getAllPlaceLists(queryURL, query)

def getAllPlaceLists(queryURL, query):
    browser = setOptionsForBrowser()
    browser.get(queryURL)
    start_time = time.time()

    try:
        resultsSideBar = WebDriverWait(browser,10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, f"div[aria-label='Results for {query}']"))
        )

        #filter sidebar to ultimately get the name of place and href of the place
        foundEnd = False
        placePreviews = []  #Restaurant google maps preview list

        while(foundEnd == False):
            restaurant = browser.find_elements(By.XPATH, '//div//a[@class="hfpxzc"]') #this path means searching if the element hfpxzc could be inside //div//a

            for i in range(len(restaurant)):
                if restaurant[i].get_attribute("href") not in placePreviews:
                    placePreviews.append(restaurant[i].get_attribute("href")) 

            resultsSideBar.send_keys(Keys.PAGE_DOWN)
            resultsSideBar.send_keys(Keys.PAGE_DOWN)

            html = browser.find_element(By.TAG_NAME, "html").get_attribute('outerHTML')
           
            if(html.find("You've reached the end of the list.")!=-1):
                foundEnd = True

    except Exception as e:
        print(f"Error waiting for navbox: {e}")
    
    finally:
        browser.quit()

    #once all hrefs are gotten get all places and their attributes
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(getPlaceAttributes, previewURL) for previewURL in placePreviews]
        for future in as_completed(futures):
            future.result()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"scraping took: {elapsed_time: .2f} seconds")

def getPlaceAttributes(previewURL):
    print("Getting attributes for " + previewURL + '\n')

    browser = setOptionsForBrowser()
    curPlace = Place('','','','')

    #WAIT FOR THE URL TO POP UP FOR A SECOND

    try:
        browser.get(previewURL)
    except StaleElementReferenceException:
        pass

    xpaths = [
        '//h1[@class="DUwDvf lfPIob"]',
        '//div[@class="qBF1Pd fontHeadlineSmall ',
        '//div[@class="qBF1Pd fontHeadlineSmall kiIech Hi2drd"]'
    ]

    for xpath in xpaths:
        try:
    
            #FIX THIS STILL
            placeElement = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            curPlace.name = placeElement.text
            break
        except:
            print(f"Could not find element with xpath {xpath}" + '\n')
            continue

    infoBar = browser.find_elements(By.XPATH,'//*[@class="CsEnBe"]') #list of specific rows from info bar
    for k in range(len(infoBar)): 
        try:
            attribute = infoBar[k].get_attribute("aria-label")
        except StaleElementReferenceException:
            attribute = None

        if attribute:
            if('Website: ' in attribute):
                print(curPlace.name + " has a website")
                website = attribute.replace('Website: ', 'https://')
                curPlace.website = website
            elif('Phone: ' in attribute):
                print(curPlace.name + " has a phone")
                curPlace.phone = attribute
            elif('Address: ' in attribute):
                print(curPlace.name + " has an address")
                curPlace.address = attribute
    
    document = {}
    document |= {'name' : curPlace.name}
    document |= {'website' : curPlace.website}
    document |= {'phone' : curPlace.phone}
    document |= {'address' : curPlace.address}

    placesCollection.insert_one(document)

    browser.quit()

    #now logic needed to go into the place's website and check if it has fundraising or not

#def checkForFundraising():


# Below functions used to scrape Wikipedia for all municipalities by state
# data is later used for the autofill dropdown menu on the frontend which filters by state and city
# Not called every time app is ran
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

        # edge case for structural differences in wikipedia pages account for different element names 
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

