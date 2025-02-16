placeOptions = [
        "restaurants",
        "dessert",
        "things to do"
    ]

def buildMapsQuery(city, state, place):
    query = f"{place} near {city} {state}"  
    queryURL = f"https://www.google.com/maps/search/{place}+near+{city}+{state}"
    
    return