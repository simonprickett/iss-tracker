# How many previous ISS locations to display.
MAX_LOCATION_HISTORY=15
# How close in miles does the ISS need to be to turn the light on?
CLOSE_BY_DISTANCE=1000
# How often in seconds to retrieve a new ISS position from the internet.
REFRESH_INTERVAL=300
# Latitude and longitude for where you are.
USER_LATITUDE=52.9676828
USER_LONGITUDE=-1.1616151
# Where to get the ISS information from.
ISS_SERVICE_URL="YOUR CLOUD FUNCTION URL HERE"
# Passphrase for the ISS information service.
ISS_SERVICE_PASSPHRASE="YOUR CLOUD FUNCTION ACCESS TOKEN HERE"
# Initial access point name and domain
AP_NAME = "ISSTracker"
AP_DOMAIN = "isstracker.net"