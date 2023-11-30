import badger2040
import jpegdec
import json
import time

MAP_IMAGE_HEIGHT = 128
MAP_IMAGE_WIDTH = 192
MAX_TEXT_WIDTH = 330
MAP_LEFT_OFFSET = badger2040.WIDTH - MAP_IMAGE_WIDTH
MAP_TOP_OFFSET = 0
EQUATOR_Y = MAP_IMAGE_HEIGHT // 2
MERIDIAN_X = MAP_IMAGE_WIDTH // 2
TEXT_LEFT_OFFSET = 2
MAX_LOCATION_HISTORY = 10 # TODO move to config file
CLOSE_BY_DISTANCE = 500 # TODO move to config file
REFRESH_INTERVAL = 300 # TODO move to config file

# Initialize display.
display = badger2040.Badger2040()
display.set_update_speed(badger2040.UPDATE_NORMAL)
display.led(0)
display.set_font("bitmap8")

# Initialize location history
location_history = []

    
def update_iss_position(iss_data):
    global location_history
    
    display.clear()

    # Load the map.
    jpg = jpegdec.JPEG(display.display)
    jpg.open_file("worldmap.jpg")
    jpg.decode(MAP_LEFT_OFFSET, 0, jpegdec.JPEG_SCALE_FULL, dither=False)

    # Draw a blank area to the left of the map for text to go in.
    display.set_pen(15)
    display.rectangle(0, 0, MAP_LEFT_OFFSET, badger2040.HEIGHT)
    display.set_pen(0)

    # Display how far away the ISS is.
    # TODO pad with leading 0 to always make it 5 digits.
    display.text(f"{iss_data['dist']:05}", TEXT_LEFT_OFFSET, 2, scale=4)
    display.text("miles away", TEXT_LEFT_OFFSET, 32, scale=1)
    
    # Display the name of the place, region, country or ocean that it's over.
    location_text = ""
    
    if "ocean" in iss_data:
        # ISS over the ocean, there will be no further location fields.
        location_text = iss_data["ocean"]
    else:
        if "locality" in iss_data:
            location_text = f"{iss_data['locality'].replace('-', ' ').replace('/', ' ')}"
        if "region" in iss_data:
            location_text = f"{location_text}{', ' if len(location_text) > 0 else ''}{iss_data['region'].replace('-', ' ').replace('/', ' ')}"
        if "country" in iss_data:
            location_text = f"{location_text}{', ' if len(location_text) > 0 else ''}{iss_data['country'].replace('-', ' ').replace('/', ' ')}" 
        
    if len(location_text) == 0:
        location_text = "Unknown Location"
    else:
        location_text = location_text.strip(" ,")

    # See if the location text needs adjusting to better fit the space.
    if display.measure_text(location_text, 2) > MAX_TEXT_WIDTH:
        # The location text is too long, let's first try and remove the region if present.
        location_parts = location_text.split(', ')
        if len(location_parts) == 3:
            # We have locality, region, country - drop the region.
            location_text = f"{location_parts[0]}, {location_parts[2]}"
              
        text_width = display.measure_text(location_text, 2)
        if text_width > MAX_TEXT_WIDTH:
            # Taking 1 character to be 6 pixels wide, guesstimate how many
            # characters we are over length and add in a few to make room
            # for an ellipsis.
            slice_off = 0 - (((text_width + 12) - MAX_TEXT_WIDTH) // 6)
            location_text = f"{location_text[:slice_off].strip(' ')}..."
    
    display.text(location_text, TEXT_LEFT_OFFSET, 46, wordwrap=badger2040.WIDTH - MAP_IMAGE_WIDTH - TEXT_LEFT_OFFSET, scale=2)

    # Figure out the lat/lon position for the ISS as x/y co-ordinates on the map, taking
    # into account the position of the map on the display.
    iss_lat = iss_data["lat"]
    iss_lon = iss_data["lon"]

    meridian_offset_px = abs(iss_lon) * (MAP_IMAGE_WIDTH / 360)
    iss_x = (round(MERIDIAN_X - meridian_offset_px if iss_lon < 0 else MERIDIAN_X + meridian_offset_px)) + MAP_LEFT_OFFSET

    equator_offset_px = abs(iss_lat) * (MAP_IMAGE_HEIGHT / 180)
    iss_y = (round(EQUATOR_Y - equator_offset_px if iss_lat >= 0 else EQUATOR_Y + equator_offset_px)) + MAP_TOP_OFFSET

    display.circle(iss_x, iss_y, 4)
    
    # Update the previous positions with this one and cap the list size if needed.
    
    if len(location_history) == MAX_LOCATION_HISTORY:
        location_history.pop()
    
    # Draw the previous positions as smaller circles.
    for previous_loc in location_history:
        display.circle(previous_loc[0], previous_loc[1], 2)
    
    # Add the current location to the history.
    location_history.insert(0, [ iss_x, iss_y ])

    # Display when this update was performed.
    display.text(iss_data["updatedAt"], TEXT_LEFT_OFFSET, 120, scale=1)

    # Update the screen with the new information.
    display.update()
    
    # Turn the LED on if the ISS is close enough to us, otherwise off.
    if iss_data['dist'] <= CLOSE_BY_DISTANCE:
        display.led(128)
    else:
        display.led(0)
    
# Main program starts here... for now just feed some data in to test display.

# TODO wifi stuff...

# TODO call the service in a loop...

#iss_data = json.loads('{"lat": 1.756,"lon": -109.3535,"dist": 6871,"ocean": "North Pacific Ocean","updatedAt": "Nov 30 17:40 UTC"}')
#update_iss_position(iss_data)
#time.sleep(5)
#iss_data = json.loads('{"lat": 16.6401,"lon": -98.3091,"dist": 5597,"region": "Guerrero","country": "Mexico","updatedAt": "Nov 30 17:45 UTC"}')
#update_iss_position(iss_data)
#time.sleep(5)
#iss_data = json.loads('{"lat": 31.3806,"lon": -84.438,"dist": 4256,"locality": "Atlanta","country": "United States","updatedAt": "Nov 30 17:50 UTC"}')
#update_iss_position(iss_data)
#time.sleep(5)
iss_data = json.loads('{"lat": 31.3806,"lon": -84.438,"dist": 409,"locality": "Raleigh-Durham","region": "Georgia", "country": "United States of America","updatedAt": "Nov 30 17:50 UTC"}')
update_iss_position(iss_data)
time.sleep(5)
#iss_data = json.loads('{"lat": 31.3806,"lon": -84.438,"dist": 4256,"country": "United States","updatedAt": "Nov 30 17:50 UTC"}')
#update_iss_position(iss_data)
#time.sleep(5)

#iss_data = json.loads('{"lat": 42.9715,"lon": -67.008,"dist": 3012,"ocean": "North Atlantic Ocean","updatedAt": "Nov 30 17:55 UTC"}')
#update_iss_position(iss_data)
#time.sleep(5)
#iss_data = json.loads('{"lat": 50.4487,"lon": -42.2722,"dist": 1745,"ocean": "North Atlantic Ocean","updatedAt": "Nov 30 18:00 UTC"}')
#update_iss_position(iss_data)
