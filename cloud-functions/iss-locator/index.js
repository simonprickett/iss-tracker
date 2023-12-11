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
  'Republic of the Congo': 'Congo',
  'Türkiye': 'Turkiye'
};

require('dotenv').config();

const CLIENT_PASSPHRASES = process.env.CLIENT_PASSPHRASES.split('|')

function findAddressComponent(addressComponents, componentToFind, useShortForm) {
  const matches = addressComponents.filter(comp => comp.types.includes(componentToFind));

  if (matches.length > 0) {
    return useShortForm ? matches[0].short_name : matches[0].long_name;
  }

  return null;
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
  if (!req.header(SECURITY_HEADER_NAME) || ! CLIENT_PASSPHRASES.includes(req.header(SECURITY_HEADER_NAME))) {
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
      // Unknown, service was down?
    }
  } else {
    // Retrieve fields of interest from geocoder response, if present.
    const locality = findAddressComponent(geocodeInfo.results[0].address_components, 'locality');
    const country = findAddressComponent(geocodeInfo.results[0].address_components, 'country');

    // If we have a locality and the country is the USA then let's send the short
    // name for the region which will be the state name.
    // TODO: Potentially also Canadian provinces?
    if (country) { response.country = formatCountryName(country); }

    const region = findAddressComponent(geocodeInfo.results[0].address_components, 'administrative_area_level_1', ('USA' === response.country && locality));

    if (locality) { response.locality = locality; }
    if (region) { response.region = region; }

  }

  rightNow = new Date();
  // Mon 11 Dec 8:12am UTC
  response.updatedAt = `${dateformat(rightNow, 'ddd dd mmm h:MMtt')} UTC`;
  response.timestamp = rightNow.getTime();

  return res.json(response);
});