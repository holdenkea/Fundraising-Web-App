import asyncio
from playwright.async_api import Playwright, async_playwright
from .db import placesCollection


placeOptions = [
        "restaurants",
        "dessert",
        "things to do"
    ]

async def get_fundraising_information(link, page):
    try:
        link.click()

    finally: 
        await page.close()



async def extract_place_attributes(links, context, placesCollection):
    tasks = []
    pages = []
    #for link in links:
    ##    page = await context.new_page()
     #   pages.append(page)
     #   task = get_fundraising_information(link, page)
     #   tasks.append(task)
                     
    results = await asyncio.gather(*tasks)

async def begin_scraping_sidebar(page, city, state, place):
    query = f"{place} near {city} {state}"  

    queryURL = f"https://www.google.com/maps/search/{place}+near+{city}+{state}"

    await page.goto(f"{queryURL}")

    # sidebar
    results_side_bar = await page.wait_for_selector(f"div[aria-label='Results for {query}']")
    place_previews = set()
    prev_height = -1

    while True:
        # Extract restaurant links
        restaurant_links = await page.query_selector_all('//div//a[@class="hfpxzc"]')
        for link in restaurant_links:
            href = await link.get_attribute("href")
            if href:
                place_previews.add(href)

        if restaurant_links:
            await restaurant_links[-1].scroll_into_view_if_needed()
            
        # Wait for content to load
        await page.wait_for_timeout(1000)

        # Check if we've reached the bottom
        current_height = await page.evaluate("(el) => el.scrollHeight", results_side_bar)
        if current_height == prev_height:
            break  # Stop scrolling if height does not change
        prev_height = current_height

    print(f"Found {len(place_previews)} places")

    place_previews = list(place_previews)

    """
    update_db = placesCollection.update_one(
    {"states.name": state},  # Find the state
    {
        "$set": {
            f"states.$.cities.{city}.place_previews": place_previews  # Update city place_previews if the city exists
        },
        "$setOnInsert": {
            f"states.$.cities": {city: {"place_previews": place_previews}}  # Insert city if it doesn't exist
        }
    },
    upsert=True  # Ensure the state is inserted if it doesn't exist
    )

    """

    """
    PLACE COLLECTION AND LOCATION NOW HAVE THE SAME STRUCTURE,
    NEED TO UPDATE HOW WE CAN ADD THE PLACE PREVIEWS TO THE DB

    WHY AM I ADDING PLACE PREVIEWS TO THE DB ANYWAYS?
    SHOULDN"T I JUST HOLD IT AS A LIST AND PASS THE CONTEXT TO
    OPEN A NEW PAGE AND CLICK INTO IT EVERY TIME I WANT TO SCRAPE IT?

    """
    
    if update_db.upserted_id:
        print(f"Succesfully inserted new collection for place previews in {city},{state}")
    else:
        print("Successfully updated existing city and state's collection in database")

async def run(playwright: Playwright, placesCollection, city, state, place) -> None:
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()


    place_previews = await begin_scraping_sidebar(page, city, state, place)
    await page.close()

    #for preview in place_previews:
    #    print(preview + '\n')


    #await extract_place_attributes(place_previews, context, placesCollection)

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
    