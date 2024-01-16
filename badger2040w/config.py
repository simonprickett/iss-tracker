# How many previous ISS locations to display.
MAX_LOCATION_HISTORY=15
# How close in miles does the ISS need to be to turn the light on?
CLOSE_BY_DISTANCE=1000
# How often in seconds to retrieve a new ISS position from the internet.
REFRESH_INTERVAL=300
# Default lat/long values and place name.
DEFAULT_LATITUDE=52.953384
DEFAULT_LONGITUDE=-1.1505282
DEFAULT_PLACE="Nottingham England"
# Where to get the ISS information from.
ISS_SERVICE_URL="YOUR CLOUD FUNCTION URL HERE"
# Passphrase for the ISS information service.
ISS_SERVICE_PASSPHRASE="YOUR CLOUD FUNCTION ACCESS TOKEN HERE"
# String that you can use to identify calls made by this device to the cloud function.
DEVICE_ID="YOUR DEVICE ID HERE"
# Initial access point name and domain
AP_NAME = "ISSTracker"
AP_DOMAIN = "isstracker.net"
