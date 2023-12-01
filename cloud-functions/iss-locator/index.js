const dateformat = require('dateformat');
const functions = require('@google-cloud/functions-framework');
const haversine = require('haversine');

const SECURITY_HEADER_NAME = 'X-ISS-Locator-Token';

const COUNTRY_NAME_MAP = {
  'United States': 'USA',
  'United Arab Emirates': 'UAE',
  'United Kingdom': 'UK',
  'Central African Republic': 'C African Rep',
  'Saint Vincent and the Grenadines': 'St Vincent & Grenadines',
  'São Tomé and Príncipe': 'Sao Tome & Principe',
  'Trinidad and Tobago': 'Trinidad & Tobago',
  'Marshall Islands': 'Marshall Isles',
  'Saint Kitts and Nevis': 'St Kitts & Nevis',
  'Saint Lucia': 'St Lucia',
  'Solomon Islands': 'Solomon Isles',
  'Bosnia and Herzegovina': 'Bosnia Herzegovina',
  'Antigua and Barbuda': 'Antigua & Barbuda',
  'Democratic Republic of the Congo': 'DR Congo',
  'Republic of the Congo': 'Congo'
};

require('dotenv').config();

function findAddressComponent(addressComponents, componentToFind) {
  const matches = addressComponents.filter(comp => comp.types.includes(componentToFind));

  return matches.length > 0 ? matches[0].long_name : null;
}

function formatCountryName(countryName) {
  return COUNTRY_NAME_MAP[countryName] ? COUNTRY_NAME_MAP[countryName] : countryName;
}

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
  apiResponse = await fetch(`https://maps.googleapis.com/maps/api/geocode/json?result_type=country|locality|administrative_area_level_1|natural_feature&language=en_GB&latlng=${response.lat},${response.lon}&key=${process.env.GEOCODER_API_KEY}`);
  const geocodeInfo = await apiResponse.json();

  if (geocodeInfo.status === 'ZERO_RESULTS') {
    // Try for an ocean name if possible.
    try {
      apiResponse = await fetch(`https://secure.geonames.org/oceanJSON?lat=${response.lat}&lng=${response.lon}&username=${process.env.GEONAMES_USER}`);
      const oceanInfo = await apiResponse.json();

      if (oceanInfo.ocean) { response.ocean = oceanInfo.ocean.name; }
    } catch (e) {
      // Unknown, service was down?.
    }
  } else {
    // Retrieve fields of interest from geocoder response, if present.
    const locality = findAddressComponent(geocodeInfo.results[0].address_components, 'locality');
    const region = findAddressComponent(geocodeInfo.results[0].address_components, 'administrative_area_level_1');
    const country = findAddressComponent(geocodeInfo.results[0].address_components, 'country');

    if (locality) { response.locality = locality; }
    if (region) { response.region = region; }
    if (country) { response.country = formatCountryName(country); }

    // Consider... when country is USA, shorten state names to codes using short_name field.
    // Potentially also Canadian provinces?
  }

  rightNow = new Date();
  response.updatedAt = `${dateformat(rightNow, 'mmm dd HH:MM')} UTC`;
  response.timestamp = rightNow.getTime();

  return res.json(response);
});