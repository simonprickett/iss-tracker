# ISS Tracker

TODO

## Front End for Pimoroni Badger 2040w

TODO

## Back End Cloud Function

TODO

Deployment command:

```
cd cloud-functions/iss-locator
gcloud functions deploy isslocator --gen2 --runtime=nodejs18 --source=. --entry-point=isslocator --trigger-http --region=europe-west2 --set-env-vars GEONAMES_USER=your_geonames_account,GEOCODER_API_KEY=your_google_api_key,CLIENT_PASSPHRASES="valid_passphrase_1|valid_passphrase_2|valid_passphrase_n"
```