import asyncio
from playwright.async_api import Playwright, async_playwright
from .db import placesCollection

import random

from bs4 import BeautifulSoup

placeOptions = [
        "restaurants",
        "dessert",
        "things to do",
        "fun"
    ]

async def check_website_for_fundraising(website, page):
    KEYWORDS = {"foundation", "foundations", "fundraising", "fundraiser",
                "fundraisers", "rewards", "community", "communities",
                "care", "cares", "outreach", "funds", "dine and donate",
                "donate"}

    try:
        await page.goto(website, timeout=7500)
        html = await page.content()

        # parse html with Beautiful soup
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=" ").lower()

        # search for keywords
        found_keywords = [keyword for keyword in KEYWORDS if keyword in text]

        return found_keywords
    
    except Exception as e:
        print(f"Error accessing {website}: {e}")
        return []

async def get_place_attributes(place, context):
    # place has 'name' key value pair and 'href' key value pair

    # delay to try to avoid detection
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
            # waiting for the page to load for timeout seconds, if not skip
            await page.goto(place['href'], timeout=30000)
        except (TimeoutError):
            return None

        # viewport size from Playwright 
        viewport_size = page.viewport_size
        
        # set viewport to max screen size 
        await page.set_viewport_size(viewport_size)

        # zoom out the page to 50% using CSS for faster crawling
        await page.evaluate("document.body.style.zoom='50%'")

        # human like refresh 
        await page.keyboard.press('F5')  

        #uses CSS selector
        sidebar = await page.query_selector(".XltNde.tTVLSc")

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
                    #print("FOUND BUTTON")
                    aria_label = await button.get_attribute("aria-label")

                    if aria_label and "Address: " in aria_label:
                        #print("FOUND ADDRESS")
                        address = aria_label.replace("Address: ", "")
                    if aria_label and "Phone: " in aria_label:
                        #print("FOUND PHONE")
                        phone_number = aria_label.replace("Phone: ", "")
                    if aria_label and "Plus code: " in aria_label:
                        #print("FOUND PLUS CODE")
                        plus_code = aria_label.replace("Plus code: ", "")
                    if aria_label and "Website: " in aria_label:
                        website = aria_label.replace("Website: ", "https://")
                        print(f"FOUND WEBSITE {website}")

            if website:
                print(f"IN WEBSITE {website}")
                fundraising_types = await check_website_for_fundraising(website, page)

                if fundraising_types != []:
                    print(f"WEBSITE {website} HAS FUNDRAISING TYPES {fundraising_types}")

                    place_document = {}
                    place_document |= {'name' : name}
                    place_document |= {'website' : website}
                    place_document |= {'types' : fundraising_types}
                    place_document |= {'address' : address}
                    place_document |= {'phone' : phone_number}
                    place_document |= {'plus' : plus_code}
                    return place_document
    finally:
        await page.close()

async def scrape_multiple_places(place_previews, context):
# GOOGLE WILL BLOCK REQUESTS IF TOO MANY ARE SENT FROM THE SAME
# CONTEXT AT ONCE

# NEED TO CHUNK THE PLACE PREVIEW URLs BEFORE I SEND IT TO THE
# CHECK PLACE FOR FUNDRAISING FUNCTION
    chunk_size = 15
    chunks = [place_previews[i:i + chunk_size] for i in range(0, len(place_previews), chunk_size)]

    all_results = []

    for chunk in chunks:
        tasks = [get_place_attributes(place, context) for place in chunk]
        results = await asyncio.gather(*tasks)

        # filter out None results 
        valid_results = [r for r in results if r is not None]
        all_results.extend(valid_results)

    return all_results

async def begin_scraping_sidebar(page, city, state, place, numPlaces):
    query = f"{place} near {city} {state}"  

    queryURL = f"https://www.google.com/maps/search/{place}+near+{city}+{state}"

    await page.goto(f"{queryURL}")

    viewport_size = page.viewport_size
    await page.set_viewport_size(viewport_size)
    await page.evaluate("document.body.style.zoom='50%'")
    await page.keyboard.press('F5')  # Press 'F5' to refresh the page

    # wait for sidebar to load
    await page.wait_for_selector(f"div[aria-label='Results for {query}']")

    place_previews = []
    place_count = 0

    # need this set since query_selector_all will return whatever is on the page
    seen_place_hrefs = set()

    scrollable = True

    while scrollable and (place_count <= numPlaces):

        # gets the class that contains the label (Name of place), and href, place preview link
        restaurant_links = await page.query_selector_all('//div//a[@class="hfpxzc"]')

        for link in restaurant_links:
            name = await link.get_attribute("aria-label")
            href = await link.get_attribute("href")

            if href and href not in seen_place_hrefs:
                place_previews.append({"name" : name, "href" : href})
                seen_place_hrefs.add(href)
                place_count = place_count + 1

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



async def run(playwright: Playwright, placesCollection, city, state, place, numPlaces) -> None:
    browser = await playwright.chromium.launch()
    context = await browser.new_context()
    page = await context.new_page()

    # returns list of hrefs of place previews
    print(">> BEGIN scraping", flush=True)
    place_previews = await begin_scraping_sidebar(page, city, state, place, numPlaces)
    print(">> END scraping sidebar", flush=True)    
    await page.close()

    print(f"Found {len(place_previews)} places")

    # need to make sure this returns a list of places and their attibutes
    # for places that were deemed to have fundraising opportunities
    print(">> BEGIN fundraising scrape", flush=True)
    fundraising_place_attributes = await scrape_multiple_places(place_previews, context)
    print(">> END fundraising scrape", flush=True)
    
    print(f"Fundraising places collected: {len(fundraising_place_attributes)}", flush=True)

    print("PRINTING FUNDRAISING PLACE ATTRIBUTES", flush=True)
    print(fundraising_place_attributes, flush=True)

    await context.close()
    await browser.close()

    return fundraising_place_attributes


async def google_main(city, state, place, numPlaces) -> None:
    import time
    if numPlaces == 'all':
        numPlaces = 200
    else:
        numPlaces = int(numPlaces)

    async with async_playwright() as playwright:

        start_time = time.time()
        result = await run(playwright, placesCollection, city, state, place, numPlaces)
        end_time = time.time()

        total_time = end_time - start_time
        print(f"The end time for google maps crawling is: {total_time}")
    
        return result

