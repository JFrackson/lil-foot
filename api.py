#!flask/bin/python
"""
Yelp API v2.0 code sample.

This program demonstrates the capability of the Yelp API version 2.0
by using the Search API to query for businesses by a search term and location,
and the Business API to query additional information about the top result
from the search query.

Please refer to http://www.yelp.com/developers/documentation for the API documentation.

This program requires the Python oauth2 library, which you can install via:
`pip install -r requirements.txt`.

Sample usage of the program:
`python sample.py --term="bars" --location="San Francisco, CA"`
"""

from flask import Flask, jsonify, request, render_template, redirect
from flask.ext.googlemaps import GoogleMaps
from flask.ext.googlemaps import Map

import argparse
import json
import pprint
import sys
import os
import requests
import urllib
import urllib2
import simplejson

import oauth2

app = Flask(__name__)
GoogleMaps(app)
PORT=int(os.environ.get('PORT', 5000))

API_HOST = 'api.yelp.com'
DEFAULT_TERM = 'dinner'
DEFAULT_LOCATION = 'San Francisco, CA'
SEARCH_LIMIT = 20
SEARCH_PATH = '/v2/search/'
BUSINESS_PATH = '/v2/business/'

# OAuth credential placeholders that must be filled in by users.
CONSUMER_KEY = 'm-L326N-ElbOD8dC9BvhOQ'
CONSUMER_SECRET = 'Gxag6-dor9I2IdHybS9DSqGPebM'
TOKEN = 'bg04FohLicwvcED9NVB-vXE66DXZxTMp'
TOKEN_SECRET = 'mbg7wwxRkYOJ-5MJYONkZeeQA_M'

'''
    Main page. Nothing here.
'''

@app.route('/', methods = ['GET'])
def hello():
    return render_template('puppies.html')

''' 
    Initial puppies page
'''

@app.route('/puppies', methods=['GET', 'POST'])
def getData():
    return render_template('map.html')
    
'''
    Manage POST
'''
@app.route('/output', methods=['POST'])
def returnData():
    location =  request.form['location']
    return redirect('/puppies/' + location)

''' 
    Returns dictionary: {Park name: address}, where address
    is a dictionary with fields "address", "city", "coordinate",
    "country_code", "display_address", "geo_accuracy", "postal_code",
    "state_code".
    "coordinate" is itself a dictionary with fields "latitude", 
    "longitude".
'''
def puppies(location):
    data = search(location)
    filtered_data = {}

    for business in data['businesses']:
        name = business['name'] # Name
        location = business['location']
        rating = business['rating_img_url']

        filtered_data[name] = [location,rating]

    return filtered_data


googleGeocodeUrl = 'http://maps.googleapis.com/maps/api/geocode/json?'

def get_coordinates(query, from_sensor=False):
    query = query.encode('utf-8')
    params = {
        'address': query,
        'sensor': "true" if from_sensor else "false"
    }
    url = googleGeocodeUrl + urllib.urlencode(params)
    json_response = urllib.urlopen(url)
    response = simplejson.loads(json_response.read())
    if response['results']:
        location = response['results'][0]['geometry']['location']
        latitude, longitude = location['lat'], location['lng']
        print query, latitude, longitude
    else:
        latitude, longitude = None, None
        print query, "<no results>"
    return latitude, longitude


'''
    Display map after puppies request
'''
@app.route('/puppies/<start>', methods=['GET'])
def yelp(start):

    data = puppies(start)
    #print data

    lat, lng = get_coordinates(start)
    location = (lat,lng)

    names = data.keys()
    coordinates = []
    longitudes = []
    latitudes = []

    ratings = []
    parks = []

    for park in names:

        address = (data[park])[0]
        coordinate = address['coordinate']

        rating = (data[park])[1]
        if 'stars_5.png' in rating:
            rating = '5'
        elif 'stars_4_half.png':
            rating = '4.5'
        else:
            rating = rating
        ratings.append(rating)
        coordinates.append(coordinate)

    for coordinate in coordinates:
        latitude = coordinate['latitude']
        longitude = coordinate['longitude']
        parks.append((latitude,longitude))

    sndmap = Map(
        identifier = "sndmap",
        lat=lat,
        lng = lng,
        markers={'http://maps.google.com/mapfiles/ms/icons/blue-dot.png':location, 
        'http://maps.google.com/mapfiles/ms/icons/green-dot.png':parks}

        )

    display_values = zip(names, ratings)
    print display_values


    return render_template('map_result.html', location=location, parks=parks, names=names, ratings=ratings, display_values=display_values)






def requestz(host, path, url_params=None):
    """Prepares OAuth authentication and sends the request to the API.

    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        url_params (dict): An optional set of query parameters in the request.

    Returns:
        dict: The JSON response from the request.

    Raises:
        urllib2.HTTPError: An error occurs from the HTTP request.
    """
    url_params = url_params or {}
    url = 'http://{0}{1}?'.format(host, urllib.quote(path.encode('utf8')))

    consumer = oauth2.Consumer(CONSUMER_KEY, CONSUMER_SECRET)
    oauth_request = oauth2.Request(method="GET", url=url, parameters=url_params)

    oauth_request.update(
        {
            'oauth_nonce': oauth2.generate_nonce(),
            'oauth_timestamp': oauth2.generate_timestamp(),
            'oauth_token': TOKEN,
            'oauth_consumer_key': CONSUMER_KEY
        }
    )
    token = oauth2.Token(TOKEN, TOKEN_SECRET)
    oauth_request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), consumer, token)
    signed_url = oauth_request.to_url()

    print signed_url
    
    print u'Querying {0} ...'.format(url)

    conn = urllib2.urlopen(signed_url, None)
    try:
        response = json.loads(conn.read())
    finally:
        conn.close()

    return response

#def search(term, location):
def search(location):
    """Query the Search API by a search term and location.

    Args:
        term (str): The search term passed to the API.
        location (str): The search location passed to the API.

    Returns:
        dict: The JSON response from the request.
    """
    
    url_params = {
        #'term': term.replace(' ', '+'),
        'location': location.replace(' ', '+'),
        'limit': SEARCH_LIMIT,
        'sort':1,
    
        'category_filter': 'dog_parks'
    }
    return requestz(API_HOST, SEARCH_PATH, url_params=url_params)

def get_business(business_id):
    """Query the Business API by a business ID.

    Args:
        business_id (str): The ID of the business to query.

    Returns:
        dict: The JSON response from the request.
    """
    business_path = BUSINESS_PATH + business_id

    return requestz(API_HOST, business_path)

def query_api(term, location):
    """Queries the API by the input values from the user.

    Args:
        term (str): The search term to query.
        location (str): The location of the business to query.
    """
    response = search(term, location)

    businesses = response.get('businesses')

    if not businesses:
        print u'No businesses for {0} in {1} found.'.format(term, location)
        return

    business_id = businesses[0]['id']

    print u'{0} businesses found, querying business info for the top result "{1}" ...'.format(
        len(businesses),
        business_id
    )

    response = get_business(business_id)

    print u'Result for business "{0}" found:'.format(business_id)
    pprint.pprint(response, indent=2)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-q', '--term', dest='term', default=DEFAULT_TERM, type=str, help='Search term (default: %(default)s)')
    parser.add_argument('-l', '--location', dest='location', default=DEFAULT_LOCATION, type=str, help='Search location (default: %(default)s)')

    input_values = parser.parse_args()

    try:
        query_api(input_values.term, input_values.location)
    except urllib2.HTTPError as error:
        sys.exit('Encountered HTTP error {0}. Abort program.'.format(error.code))


if __name__ == '__main__':
    #main()

    app.debug=True
    app.run(host='0.0.0.0', port=PORT)


