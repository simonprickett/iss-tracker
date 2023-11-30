import badger2040
import jpegdec
import json

MAP_IMAGE_HEIGHT = 128
MAP_IMAGE_WIDTH = 192
MAP_LEFT_OFFSET = badger2040.WIDTH - MAP_IMAGE_WIDTH
MAP_TOP_OFFSET = 0
EQUATOR_Y = MAP_IMAGE_HEIGHT // 2
MERIDIAN_X = MAP_IMAGE_WIDTH // 2
TEXT_LEFT_OFFSET = 2

# Initialize display.
display = badger2040.Badger2040()
display.set_update_speed(badger2040.UPDATE_NORMAL)
display.led(0)
display.set_font("bitmap8")

    
def update_iss_position(iss_data):    
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
    display.text("miles away", TEXT_LEFT_OFFSET, 32, scale=2)
    
    # Display the name of the place, region, country or ocean that it's over.
    location_text = ""
    
    if "ocean" in iss_data:
        # ISS over the ocean, there will be no further location fields.
        location_text = iss_data["ocean"]
    else:
        if "locality" in iss_data:
            location_text = f"{iss_data['locality']}, "
        if "region" in iss_data:
            location_text = f"{location_text}, {iss_data['region']}, "
        if "country" in iss_data:
            location_text = f"{location_text}, {iss_data['country']}" 
        
    if len(location_text) == 0:
        location_text = "Unknown Location"
    else:
        location_text = location_text.strip(" ,")
    
    display.text(location_text, TEXT_LEFT_OFFSET, 54, wordwrap=badger2040.WIDTH - MAP_IMAGE_WIDTH - TEXT_LEFT_OFFSET, scale=2)

    # Figure out the lat/lon position for the ISS as x/y co-ordinates on the map, taking
    # into account the position of the map on the display.
    iss_lat = iss_data["lat"]
    iss_lon = iss_data["lon"]

    meridian_offset_px = abs(iss_lon) * (MAP_IMAGE_WIDTH / 360)
    iss_x = (round(MERIDIAN_X - meridian_offset_px if iss_lon < 0 else MERIDIAN_X + meridian_offset_px)) + MAP_LEFT_OFFSET

    equator_offset_px = abs(iss_lat) * (MAP_IMAGE_HEIGHT / 180)
    iss_y = (round(EQUATOR_Y - equator_offset_px if iss_lat >= 0 else EQUATOR_Y + equator_offset_px)) + MAP_TOP_OFFSET

    display.circle(iss_x, iss_y, 4)

    # Display when this update was performed.
    display.text(iss_data["updatedAt"], TEXT_LEFT_OFFSET, 118, scale=1)

    # Update the screen with the new information.
    display.update()
    
iss_data = json.loads('{ "lat": -48.6912, "lon": 140.7159, "dist": 771, "ocean": "Indian Ocean", "units": "mi", "updatedAt": "Nov 30 16:56 UTC", "timestamp": 1701363382170 }')
update_iss_position(iss_data)