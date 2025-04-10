# ISS Tracker

TODO introduction and architecture.

Here it is running on the Badger 2040w device...

![Project running on a Badger 2040w device](running_on_badger.jpg)

I did a live stream about this project: [Watch it here](https://www.youtube.com/watch?v=zSsMsijupz0) and don't forget to subscribe and get notified whenever I'm live.  Thanks!

There's also a CircuitPython project by Aaron Pendley that's inspired by this and does some things better than my version.  It runs on the Adafruit MagTag, see pictures of it and check out the source code [here](https://github.com/apendley/magtag-iss-tracker).

## Back End Cloud Function

TODO

### Deploying to Google Cloud

TODO commentary on how this works...

```
cd cloud-functions/iss-locator
gcloud functions deploy isslocator --gen2 --runtime=nodejs18 --source=. --entry-point=isslocator --trigger-http --region=europe-west2 --set-env-vars GEONAMES_USER=your_geonames_account,GEOCODER_API_KEY=your_google_api_key,CLIENT_PASSPHRASES="valid_passphrase_1|valid_passphrase_2|valid_passphrase_n"
```

## Front End for Pimoroni Badger 2040w

TODO

### Copying Files to the Device

First, delete all existing files from your Badger 2040w.  Then copy all of the following to the root of the Badger 2040w's filesystem:

* `phew` (folder plus all files contained in it)
* `templates` (folder plus all files contained in it)
* `config.py`
* `iss.jpg`
* `main.py`
* `worldmap.jpg`

### Configuration

Edit the copy of `config.py` that is on your device.  Change the following lines:

```
ISS_SERVICE_URL="YOUR CLOUD FUNCTION URL HERE"
```

Replace the placeholder text with the full URL to your Google Cloud function, for example `https://europe-west2-someorg.cloudfunctions.net/isslocator/`.

```
ISS_SERVICE_PASSPHRASE="YOUR CLOUD FUNCTION ACCESS TOKEN HERE"
```

Replace the placeholder text with one of the client passphrase values you configured when deploying your Google Cloud function.

Give your device a unique ID so that it can be identified more easily in Google Cloud when it calls the Cloud Function to get the ISS position.  Replace this with your choice of device ID (e.g. `mydevice` or `1234`).

```
DEVICE_ID="YOUR DEVICE ID HERE"
```

### Setup Process

Reset the Badger 2040w to start the setup process.  It should start up and expose a WiFi access point whose SSID is "ISSTracker".

Connect to this with your phone and follow the setup process in the web portal that pops up.  You'll need to provide your WiFi SSID and password as well as your location's latitude and longitude values.

Save the changes in the form using the "Save Settings" button.  The device should reboot and attempt to connect to your network.  If successful, it should start to track the International Space Station.

If the device can't connect to your WiFi network or you provided incorrect details, it will display an error message.  Press both the A and C buttons together to reset it and try again.

### Reset Process

If you need to change the WiFi details (because you've take the device somewhere else for example) or you want to change your location, press both the A and C buttons while on the map screen to reset the device.

### Limitations

This project only works on WiFi networks with SSID and password.  It is unlikely to work on public WiFi networks that use captive portals for signup or accepting terms and conditions.
