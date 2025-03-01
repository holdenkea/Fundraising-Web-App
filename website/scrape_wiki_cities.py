import asyncio
from playwright.async_api import Playwright, async_playwright
from .db import locationsCollection, placesCollection


states = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware', 'Florida', 
             'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts',
             'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico',
             'New York', 'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina',
             'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming'] 


async def process_row(row):

    class_attribute = await row.get_attribute('class')
    if class_attribute == 'sortbottom':
        return None  # End of table

    city_element = await row.query_selector('a')
    if not city_element:
        print(f"returning NONE from process row")

        return None

    city = await city_element.text_content()
    if city:
        city_document = {}
        city_document |= {'city' : city}
        # print(f"RETURNING CITY: {city} from process row")
        return city

    return None


async def fetch_cities_for_state(state_href, page):
    try:   
        await page.goto(state_href)
        
        # wait for table to appear before attempting to select it
        await page.wait_for_selector('.wikitable.sortable.jquery-tablesorter')
        table = await page.query_selector('.wikitable.sortable.jquery-tablesorter')

        # Edge case for structural differences in Wikipedia pages
        # Check if the first 'a' tag has the 'title' attribute equal to 'County seat'
        first_a_tag = await table.query_selector('a')
        title_attribute = await first_a_tag.get_attribute('title')

        if title_attribute == 'County seat':
            # If the condition is met, find the other table with a different class
            table = await page.query_selector('.wikitable.sortable.plainrowheaders.jquery-tablesorter')

        # table's body
        table_body = await table.query_selector('tbody')

        # selecting all tr tags in table
        rows = await table_body.query_selector_all('tr')

        cities_documents = []
        
        # processing 10 rows per chunk
        chunk_size = 23
        chunks = []
        chunks = [rows[i:i + chunk_size] for i in range(0, len(rows), chunk_size)]

        for chunk in chunks:
            tasks = []
            #cities_documents = []

            for row in chunk:
                tasks.append(process_row(row))
                # print("Processing Row")

            results = await asyncio.gather(*tasks)

            # Ensure each result is properly structured before appending
            for res in results:
                cities_documents.append(res)

        print(f"UPDATING STATE IN locations collection WITH HREF: {state_href}")
        locationsCollection.update_one(
            {"href" : state_href},
            { "$addToSet": {"cities" : {"$each" : cities_documents}} },
            upsert=True
        )  

        print(f"UPDATING STATE IN place collection WITH HREF: {state_href}")
        placesCollection.update_one(
            {"href" : state_href},
            { "$addToSet": {"cities" : {"$each" : cities_documents}} },
            upsert=True
        )  

        #print(f"RETURNING FROM STATE WITH HREF: {state_href}")
        #return state_href, cities_documents
        #return cities

    finally:
        await page.close()

async def scrape_multiple_states(state_and_hrefs, context):
    tasks = []
    pages = []
    for state_href in state_and_hrefs.values():
        page = await context.new_page()
        pages.append(page)
        task = fetch_cities_for_state(state_href, page)
        tasks.append(task)

    results = await asyncio.gather(*tasks)
        
async def extract_state_hrefs(page, locationsCollection, placesCollection):
    BASE_URL = "https://en.wikipedia.org"

    await page.goto(f"{BASE_URL}/wiki/Category:Lists_of_cities_in_the_United_States_by_state")
    await page.wait_for_selector('div.navbox')
    navbox = await page.query_selector('div.navbox')
    
    await navbox.wait_for_selector('td.navbox-list-with-group.navbox-list.navbox-odd')
    sub_navbox = await navbox.query_selector('td.navbox-list-with-group.navbox-list.navbox-odd')

    unordered_list = await sub_navbox.query_selector('ul')
    list_items = await unordered_list.query_selector_all('li')

    state_and_hrefs = {}
   
    for li in list_items:
        element = await li.query_selector('a')

        if element:
            href = await element.get_attribute('href')
            state_name = await element.text_content()

            href = BASE_URL + href
            # If href is found, store the state and href
            if href:
                state_and_hrefs[state_name] = href
                # print(f"State: {state_name}, Href: {href}")

                if not locationsCollection.find_one({"state" : state_name}):
                    stateDocument = {}
                    stateDocument |= {'state' : state_name}
                    stateDocument |= {'href' : href}
                    stateDocument |= {'cities' : []}
                    locationsCollection.insert_one(stateDocument)  
                    
                if not placesCollection.find_one({"state" : state_name}):
                    stateDocument = {}
                    stateDocument |= {'state' : state_name}
                    stateDocument |= {'href' : href}
                    stateDocument |= {'cities' : []}
                    placesCollection.insert_one(stateDocument)

    return state_and_hrefs    
   
async def run(playwright: Playwright, locationsCollection, placesCollection) -> None:
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()

    states_and_hrefs = await extract_state_hrefs(page, locationsCollection, placesCollection) 
    await page.close()

    await scrape_multiple_states(states_and_hrefs, context)
    await context.close()
    await browser.close()

async def wiki_main() -> None:
    import time
    async with async_playwright() as playwright:

        start_time = time.time()
        await run(playwright, locationsCollection, placesCollection)
        end_time = time.time()

        total_time = end_time - start_time
        print(f"The end time for wikipedia crawling is: {total_time}")

# asyncio.run(main())

# HEADLESS OFF

    #time to add to database no chunking for table
    #The end time for crawling is: 202.46524262428284

    #chunk size 10: 171
    #chunk size 50: 155
    #chunk size 30: 148.22796392440796
    #chunk size 23: 146.3689410686493
    #chunk size 18: 147.41725087165833

        # chunk size 23 with print statements and both place and location db updates:
        # The end time for wikipedia crawling is: 161.66940665245056

        # chunk size 23 without print statements for each city:
        # The end time for wikipedia crawling is: 144.71464681625366

        # chunk size 23 without all print statements:
        # The end time for wikipedia crawling is: 170.78959703445435 ???? lol
        # The end time for wikipedia crawling is: 169.70345783233643