import badger2040
import config
import gc
import jpegdec
import json
import machine
import network
import os
import sys
import time
import urequests
import _thread

from phew import access_point, connect_to_wifi, is_connected_to_wifi, dns, server
from phew.template import render_template

MAP_IMAGE_HEIGHT = 128
MAP_IMAGE_WIDTH = 192
ISS_IMAGE_WIDTH = 203
MAX_TEXT_WIDTH = 330
MAP_LEFT_OFFSET = badger2040.WIDTH - MAP_IMAGE_WIDTH
MAP_TOP_OFFSET = 0
EQUATOR_Y = MAP_IMAGE_HEIGHT // 2
MERIDIAN_X = MAP_IMAGE_WIDTH // 2
TEXT_LEFT_OFFSET = 2
WIFI_FILE = "wifi.json"
TEMPLATE_PATH = "templates"


# Initialize display.
display = badger2040.Badger2040()
display.set_update_speed(badger2040.UPDATE_NORMAL)
display.led(0)
display.set_font("bitmap8")

# Initialize location history
location_history = []


# Reboot the system.
def machine_reset():
    time.sleep(1)
    print("Resetting...")
    machine.reset()

# Utility function, displays text horizontally centered.
def display_centered(text_to_display, y_pos, scale):
    width = display.measure_text(text_to_display, scale)
    x_pos = (badger2040.WIDTH - width) // 2
    display.text(text_to_display, x_pos, y_pos, badger2040.WIDTH, scale)
    return x_pos

# Expose an access point allowing the user to configure wifi and other details.
def setup_mode():
    print("Setup mode")
    display.set_pen(15)
    display.clear()
    display.set_pen(0)
    display_centered("SETUP MODE", 10, 2)
    display_centered("Connect to WiFi network", 35, 2)
    display_centered(config.AP_NAME, 70, 3)
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    networks = wlan.scan()
    
    found_wifi_networks = {}
    
    for n in networks:
        ssid = n[0].decode().strip('\x00')
        # TODO remove this when satisfied.
        print(f"network '{ssid}'")
        if len(ssid) > 0:
            rssi = n[3]
            if ssid in found_wifi_networks:
                if found_wifi_networks[ssid] < rssi:
                    found_wifi_networks[ssid] = rssi
            else:
                found_wifi_networks[ssid] = rssi

    wifi_networks_by_strength = sorted(found_wifi_networks.items(), key = lambda x:x[1], reverse = True)

    def ap_index(request):
        if request.headers.get("host").lower() != config.AP_DOMAIN.lower():
            return render_template(f"{TEMPLATE_PATH}/redirect.html", domain = config.AP_DOMAIN.lower())
                
        return render_template(f"{TEMPLATE_PATH}/index.html", lat = str(config.DEFAULT_LATITUDE), lng = str(config.DEFAULT_LONGITUDE), loc = config.DEFAULT_PLACE, wifis = wifi_networks_by_strength)

    def ap_configure(request):
        print("Saving wifi credentials...")

        with open(WIFI_FILE, "w") as f:
            json.dump(request.form, f)
            f.close()

        # Reboot from new thread after we have responded to the user.
        _thread.start_new_thread(machine_reset, ())
        return render_template(f"{TEMPLATE_PATH}/configured.html", ssid = request.form["ssid"])
        
    def ap_catch_all(request):
        if request.headers.get("host") != config.AP_DOMAIN:
            return render_template(f"{TEMPLATE_PATH}/redirect.html", domain = config.AP_DOMAIN)

        return "Not found.", 404

    server.add_route("/", handler = ap_index, methods = ["GET"])
    server.add_route("/configure", handler = ap_configure, methods = ["POST"])
    server.set_callback(ap_catch_all)

    ap = access_point(config.AP_NAME)
    ip = ap.ifconfig()[0]
    dns.run_catchall(ip)
    
    display.update()
    server.run()

# Load up the jpg file and text for the startup splash screen.
def prepare_splash_screen():
    display.clear()
    
    # Load the image of the ISS.
    jpg = jpegdec.JPEG(display.display)
    jpg.open_file("iss.jpg")
    jpg.decode(0, 0, jpegdec.JPEG_SCALE_FULL)
    
    # Draw a blank area to the right of the ISS to make the screen
    # the same colour.
    display.set_pen(15)
    display.rectangle(ISS_IMAGE_WIDTH, 0, badger2040.WIDTH - ISS_IMAGE_WIDTH, badger2040.HEIGHT)
    
    # Add some text...
    display.set_pen(0)
    display.text("simonprickett.dev", 130, 5, scale=2)
    
# Get a new ISS position and associated information from the backend and
# display it.
def update_iss_position(iss_data):
    global location_history
    
    # If we got an error, just display the error message over whatever is there already.
    if "error" in iss_data:
        # Erase any previous timetamp area and display an error message.
        display.set_pen(15)
        display.rectangle(0, 119, badger2040.WIDTH, badger2040.HEIGHT)
        display.set_pen(0)
        display.text("Network Error.", TEXT_LEFT_OFFSET, 120, scale=1)
        display.update()
        return

    # No error, get on with displaying the info.
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
    # Pad with leading 0 to always make it 5 digits.
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
    
    if len(location_history) == config.MAX_LOCATION_HISTORY:
        location_history.pop()
    
    # Draw the previous positions as smaller circles.
    for previous_loc in location_history:
        display.circle(previous_loc[0], previous_loc[1], 2)
    
    # Add the current location to the history.
    location_history.insert(0, [ iss_x, iss_y ])

    # Display when this update was performed.
    display.text(iss_data["updatedAt"], TEXT_LEFT_OFFSET, 120, scale=1)
    
    # Turn the LED on if the ISS is close enough to us, otherwise off.
    if iss_data['dist'] <= config.CLOSE_BY_DISTANCE:
        display.led(128)
    else:
        display.led(0)
            
    # Update the screen with the new information.
    display.update()


# Main program starts here... let's display a splash screen.
prepare_splash_screen()
display.update()
time.sleep(3)

# First, see if there's a configured WiFi network.
try:
    os.stat(WIFI_FILE)
    
    # File was found, read the configuration and try to connect.
    f = open(WIFI_FILE, "r")
    wifi_credentials = json.load(f)
    f.close()
    
    display.text("Connecting...", 160, 100, scale=2)
    display.update()
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(wifi_credentials["ssid"], wifi_credentials["password"])

    while not wlan.isconnected() and wlan.status() >= 0:
        print("Connecting...")
        time.sleep(0.2)

    wifi_status_text = ""

    if wlan.status() == network.STAT_GOT_IP:
        print("Connected")
        wifi_status_text = "Connected!"
    elif wlan.status() == network.STAT_WRONG_PASSWORD:
        wifi_status_text = "Wrong WiFi password."
        print("Wrong password")
    elif wlan.status() == network.STAT_NO_AP_FOUND:
        wifi_status_text = "Wrong WiFi SSID."
        print("Wrong SSID")
    else:
        print("Wifi connection error.")
        wifi_status_text = "Unknown WiFi error."


    display.set_pen(15)
    display.clear()
    display.set_pen(0)
    display_centered(wifi_status_text, 56, 2)
    
    if wlan.status() != network.STAT_GOT_IP:
        display_centered("Press A and C buttons to reset.", 85, 2)
        
    display.update()
    
    # Bad WiFi configuration, so wait for them to press A&C then reboot.
    if (wlan.status() != network.STAT_GOT_IP):
        print("Deleted wifi.json, waiting to reboot.")
        os.remove(WIFI_FILE)
        
        while True:
            if display.pressed(badger2040.BUTTON_A) and display.pressed(badger2040.BUTTON_C):
                machine_reset()
                
            time.sleep(0.2)            

    # Let the WiFi status message show for a moment.  Will actually show a little
    # longer than this as it will stay on the screen while the first ISS position is
    # retrieved from the server.
    time.sleep(2)

    # Main loop - basically get the ISS position and other information periodically
    # from the backend and display it.
    last_updated = 0
    
    while True:
        # Check for the reset key press.
        if display.pressed(badger2040.BUTTON_A) and display.pressed(badger2040.BUTTON_C):
            print("Deleted wifi.json, will reboot.")
            os.remove(WIFI_FILE)
            machine_reset()
        
        # Is it time to run the update?
        if last_updated == 0 or time.ticks_diff(time.ticks_ms(), last_updated) >= (config.REFRESH_INTERVAL * 1000):
            # A little bit of manual memory management just in case.
            gc.collect()

            try:
                iss_data = urequests.get(
                    f"{config.ISS_SERVICE_URL}?deviceid={config.DEVICE_ID}&lat={wifi_credentials['lat']}&lng={wifi_credentials['lng']}",
                    headers = {
                        "X-ISS-Locator-Token": config.ISS_SERVICE_PASSPHRASE
                    }
                ).json()
        
            except:
                iss_data = { "error": True }
            
            update_iss_position(iss_data)
            last_updated = time.ticks_ms()
        
        time.sleep(0.2)
                            
except Exception:
    # Either no wifi configuration file found, or something went wrong, 
    # so go into setup mode.
    setup_mode()