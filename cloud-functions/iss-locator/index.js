const functions = require('@google-cloud/functions-framework');
const haversine = require('haversine');

const SECURITY_HEADER_NAME = 'X-ISS-Locator-Token';

require('dotenv').config();

functions.http('isslocator', async (req, res) => {
  res.set('Access-Control-Allow-Origin', '*');

  if (req.method === 'OPTIONS') {
    res.set('Access-Control-Allow-Methods', 'GET');
    res.set('Access-Control-Allow-Headers', 'Content-Type', SECURITY_HEADER_NAME);
    res.set('Access-Control-Max-Age', '3600');
    return res.status(204).sendStatus('');
  }

  if (req.method !== 'GET') {
    return res.status(405).appendHeader('Allow', 'GET,OPTIONS').send('Method not allowed.');
  }

  // Check X-ISS-Locator-Token header value and 403 if missing or wrong.
  // TODO move secret value into environment variable.
  if (!req.header(SECURITY_HEADER_NAME) || req.header(SECURITY_HEADER_NAME) !== process.env.CLIENT_PASSPHRASE) {
    return res.status(401).send('Not authorized.');
  }

  // Check for required lat/lng parameters.
  if (!req.query.lat || !req.query.lng) {
    return res.status(400).send('Bad request.');
  }

  // Get ISS Position.
  let apiResponse = await fetch('http://api.open-notify.org/iss-now.json');
  const issInfo = await apiResponse.json();
  const response = {
    lat: parseFloat(issInfo.iss_position.latitude),
    lon: parseFloat(issInfo.iss_position.longitude),
    dist: Math.round(haversine(
      {
        latitude: req.query.lat,
        longitude: req.query.lng
      }, {
      latitude: issInfo.iss_position.latitude,
      longitude: issInfo.iss_position.longitude
    },
      {
        unit: 'mile'
      }
    )),
    units: 'mi'
  };

  // Reverse geocode the ISS location to get city, country info if possible.
  // TODO move key to env var.
  apiResponse = await fetch(`https://maps.googleapis.com/maps/api/geocode/json?result_type=country|locality|administrative_area_level_1|natural_feature&language=en_GB&latlng=${response.lat},${response.lon}&key=${process.env.GEOCODER_API_KEY}`);
  const geocodeInfo = await apiResponse.json();

  // TODO parse down the reverse geocoder response.
  response.geo = geocodeInfo;

  if (geocodeInfo.status === 'ZERO_RESULTS') {
    // Try for an ocean name if possible.
    apiResponse = await fetch(`https://secure.geonames.org/oceanJSON?lat=${response.lat}&lng=${response.lon}&username=${process.env.GEONAMES_USER}`);
    const oceanInfo = await apiResponse.json();

    if (oceanInfo.ocean) {
      response.ocean = oceanInfo.ocean.name;
    }
  }

  return res.json(response);
});