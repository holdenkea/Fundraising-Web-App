import asyncio
from playwright.async_api import Playwright, async_playwright
from .db import placesCollection


placeOptions = [
        "restaurants",
        "dessert",
        "things to do"
    ]

async def fetch_attributes_for_place(place, page):
    try:
        await page.goto(place)

        # wait for name to load
            # add name to variable or to database     
  
        # wait for attribute table to load
            # get all attributes that aren't none

        # save attributes somewhere

        # return list of attributes for a given place
        
    finally:
        await page.close()

async def scrape_multiple_places(place_previews, context):
    tasks = []
    pages = []
    for place in place_previews:
        page = await context.new_page()
        pages.append(page)
        task = fetch_attributes_for_place(place, page)
        tasks.append(task)

        # FOR EACH PLACE, RETURN A LIST OF ATTRIBUTES ALONG WITH THE WEBSITE
        # ADD WEBSITE TO A LIST OF WEBSITES
                     
    results = await asyncio.gather(*tasks)

    # WITH THE LIST OF WEBSITES CALL FUNCTION TO SEARCH EACH ONE FOR FUNDRAISING OR NOT
    # for website in websites:
        #page = await context.new_page()
        #pages.append(page)
        #task = check_website_for_fundraising(website, page)
        #tasks.append(task)


async def begin_scraping_sidebar(page, city, state, place):
    query = f"{place} near {city} {state}"  

    queryURL = f"https://www.google.com/maps/search/{place}+near+{city}+{state}"

    await page.goto(f"{queryURL}")
    

    # Get viewport size directly from Playwright instead of using evaluate
    viewport_size = page.viewport_size
    
    # Set the viewport to the maximum screen size of the machine
    await page.set_viewport_size(viewport_size)

    # Zoom out the page to 25% using CSS
    await page.evaluate("document.body.style.zoom='50%'")

    # Simulate a human-like refresh by clicking the refresh button (not reloading)
    await page.keyboard.press('F5')  # Press 'F5' to refresh the page

    # wait for sidebar to load
    await page.wait_for_selector(f"div[aria-label='Results for {query}']")

    place_previews = []

    # need this set since query_selector_all will return whatever is on the page
    seen_place_hrefs = set()

    scrollable = True

    while scrollable:

        # gets the class that contains the label (Name of place), and href, place preview link
        restaurant_links = await page.query_selector_all('//div//a[@class="hfpxzc"]')

        for link in restaurant_links:
            name = await link.get_attribute("aria-label")
            href = await link.get_attribute("href")

            if href and href not in seen_place_hrefs:
                place_previews.append({"name" : name, "href" : href})
                seen_place_hrefs.add(href)

        # now, need to scroll the same height as the scroll right now OR until you can't anymore AND reach this message
        # if you can't scroll but don't have this message wait for the page to load to avoid premature exits
        # Scroll by the sidebar's height
        scrolled = await page.evaluate('''
            () => {
                let sidebar = document.querySelector('div[role="feed"]');
                if (!sidebar) return false;

                let prevScrollTop = sidebar.scrollTop;
                let scrollAmount = sidebar.clientHeight; // Get the current sidebar height
                sidebar.scrollTop += scrollAmount; // Scroll down by the visible height
                
                return sidebar.scrollTop !== prevScrollTop; // Returns true if we scrolled
            }
        ''')

        if not scrolled:
            end_of_list_message = await page.query_selector('text="You\'ve reached the end of the list."')
            if end_of_list_message:
                scrollable = False
            else:
                await page.wait_for_timeout(2000)
        
    return place_previews



async def run(playwright: Playwright, placesCollection, city, state, place) -> None:
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()

    # returns list of hrefs of place previews
    place_previews = await begin_scraping_sidebar(page, city, state, place)
    await page.close()

    print(f"Found {len(place_previews)} places")


    
    # maybe first split the place_previews into chunks?

    # for each website in list of place previews
        # pass href with context to new function
        # click into place preview href
        
        # if place preview has a website
            # save name, address, website, phone number, etc. into variables

            # click into that website
            # if the website has fundraising
                # go out and save into has fundraising

            # if not clear, save still and return contact info

    await context.close()
    await browser.close()


async def google_main(city, state, place) -> None:
    import time
    async with async_playwright() as playwright:

        start_time = time.time()
        await run(playwright, placesCollection, city, state, place)
        end_time = time.time()

        total_time = end_time - start_time
        print(f"The end time for google maps crawling is: {total_time}")
    

# just begin_scraping_sidebar


# Alameda, CA

    # 50% window size
    #Found 113 places
    #The end time for google maps crawling is: 31.787801504135132

    # 75% window size
    # Found 113 places
    # The end time for google maps crawling is: 41.174848794937134

    # 40% window size bricked :(

    # 45% also bricked 

    # 60%
    # Found 113 places
    # The end time for google maps crawling is: 39.718761682510376

    # 55% bricked

    # no change
    # Found 113 places
    # The end time for google maps crawling is: 44.284316062927246

    # 50% again
    # Found 113 places
    # The end time for google maps crawling is: 31.776206493377686