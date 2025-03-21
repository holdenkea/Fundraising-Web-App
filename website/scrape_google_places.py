import asyncio
from playwright.async_api import Playwright, async_playwright
from .db import placesCollection

import random

placeOptions = [
        "restaurants",
        "dessert",
        "things to do"
    ]

async def check_place_for_fundraising():
    return

async def get_place_attributes(place, context):
    # place has 'name' key value pair and 'href' key value pair

    # delay to try to avoid robot detection
    delay = random.uniform(1,3)

    await asyncio.sleep(delay)

    page = await context.new_page()

    name = place['name']
    address = None
    website = None
    phone_number = None
    plus_code = None

    try:
        #print(place)
        try: 
            # waiting for the page to load fo 10 seconds, if not skip
            await page.goto(place['href'], timeout=30000)
        except (TimeoutError):
            return None

        # Get viewport size directly from Playwright instead of using evaluate
        viewport_size = page.viewport_size
        
        # Set the viewport to the maximum screen size of the machine
        await page.set_viewport_size(viewport_size)

        # Zoom out the page to 50% using CSS
        await page.evaluate("document.body.style.zoom='50%'")

        # Simulate a human-like refresh by clicking the refresh button (not reloading)
        await page.keyboard.press('F5')  # Press 'F5' to refresh the page

        # wait for sidebar to load
        #sidebar = await page.query_selector("class=m6QErb WNBkOb XiKgde")

        #uses CSS selector
        sidebar = await page.query_selector(".XltNde.tTVLSc")

        #if sidebar:
        #    print("FOUND THE SIDEBAR")

        # wait for attribute table to load
        # attribute_table = await sidebar.query_selector(".m6QErb.XiKgde")

        # uses the XPATH where the class is the class's name and 
        # it also has the aria label of Information for (place name)
        # from the name variable
        attribute_table = await sidebar.query_selector(f"xpath=//div[contains(@class, 'm6QErb XiKgde') and @aria-label=\"Information for {name}\"]")


        # look for all of the button classes "CsEnBe" for the attribute table
        if attribute_table:
            print("FOUND THE ATTRIBUTE TABLE")

            info_bars = await attribute_table.query_selector_all(".RcCsl.fVHpi.w4vB1d.NOE9ve.M0S7ae.AG25L")
            
            for bar in info_bars:

                button = await bar.query_selector(".CsEnBe") 

                if button:
                    print("FOUND BUTTON")
                    aria_label = await button.get_attribute("aria-label")

                    if aria_label and "Address: " in aria_label:
                        print("FOUND ADDRESS")
                        address = aria_label.replace("Address: ", "")
                    if aria_label and "Phone: " in aria_label:
                        print("FOUND PHONE")
                        phone_number = aria_label.replace("Phone: ", "")
                    if aria_label and "Plus code: " in aria_label:
                        print("FOUND PLUS CODE")
                        plus_code = aria_label.replace("Plus code: ", "")
                    if aria_label and "Website: " in aria_label:
                        print("FOUND WEBSITE")
                        website = aria_label.replace("Website: ", "https://")

                        # CALL FUNCTION TO SCRAPE WEBSITE HERE


                    #print(aria_label)


        # ONCE WEBSITE FOUND MUST GO INTO WEBSITE
        # AND LOOK FOR THE FUNDRAISING KEYWORDS
        
    finally:
        await page.close()

async def scrape_multiple_places(place_previews, context):

# GOOGLE WILL BLOCK REQUESTS IF TOO MANY ARE SENT FROM THE SAME
# CONTEXT AT ONCE

# I NEED TO CHUNK THE PLACE PREVIEW URLs BEFORE I SEND IT TO THE
# CHECK PLACE FOR FUNDRAISING FUNCTION

    #pages = []

    chunk_size = 15
    chunks = [place_previews[i:i + chunk_size] for i in range(0, len(place_previews), chunk_size)]

    for chunk in chunks:
        tasks = []

        for place in chunk:
        #page = await context.new_page()
        #pages.append(page)

            task = get_place_attributes(place, context)
            tasks.append(task)

        results = await asyncio.gather(*tasks)

    return results

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

    await scrape_multiple_places(place_previews, context)


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
    


# SIDEBAR CRAWLING TIMES AND GETTING WEBSITE ATTRIBUTE TIMES
# Alameda, CA

# Chunk size 10 - 119 seconds - no timeout
# Chunk size 30 - timeout
# Chunk size 15 - timeout again


# SIDEBAR CRAWLING TIMES
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

