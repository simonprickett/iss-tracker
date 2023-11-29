TODO

Deployment command:

```
cd cloud-functions/iss-locator
gcloud functions deploy isslocator --gen2 --runtime=nodejs18 --source=. --entry-point=isslocator --trigger-http --region=europe-west2 --set-env-vars GEONAMES_USER=your_geonames_account,GEOCODER_API_KEY=your_google_api_key,CLIENT_PASSPHRASE=secret_to_share_with_calling_code
```