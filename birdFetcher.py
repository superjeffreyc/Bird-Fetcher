"""
This skill pulls data from eBird.org and reports the 10 most recent sightings
for a city.
"""

from __future__ import print_function
import json
import urllib2

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "Bird Fetcher",
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': {},
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the Bird Fetcher skill! " \
                    "Please tell me your location of interest by saying, " \
                    "birds near Binghamton New York."
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please tell me your location of interest by saying, " \
                    "birds near Binghamton New York."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for trying Bird Fetcher. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

# Takes an eBird JSON response and returns a string of all the common names
def buildBirdListAsString(eBirdData, dataSize):
    birdSightings = ""
    
    for sighting in eBirdData:
        birdSightings += "%s, " % sighting['comName']

        # Insert the word 'and' before the last sighting for proper grammar
        dataSize -= 1
        if dataSize == 1:
            birdSightings += "and "
    
    # Replace dangling comma at end with a period
    birdSightings = birdSightings[:-2] + "."
    
    return birdSightings 

# Builds Alexa's Response
def buildRecentSightingsResponse(eBirdData, city, state, birdSightings):
    if len(eBirdData) == 0:
        return "There are no recent sightings for %s %s" % (city, state)
    else:
        lastDate = eBirdData[-1]['obsDt'].split()[0]    # Only grab the date, ignore the time
        
        if len(eBirdData) == 1:
            return "The only recent bird seen since %s in %s %s, is a %s" % (lastDate, city, state, birdSightings)
        else:
            return "The %s most recent birds seen since %s in %s %s, are %s" % (len(eBirdData), lastDate, city, state, birdSightings)

# Gets the index in the Google Maps JSON response that contains the state name
def getStateNameIndex(location):
    for i in range(len(location['address_components'])):
        if 'administrative_area_level_1' in location['address_components'][i]['types']:
            return i

# Handler for intent "GetBirdsWithPlace"
def get_bird_data(intent, session):

    card_title = intent['name']
    session_attributes = {}
    should_end_session = True
    speech_output = "I'm not sure what your city is. Please try again by " \
                    "saying, birds near Binghamton New York"
    
    if 'City' in intent['slots'] and 'value' in intent['slots']['City'] and 'State' in intent['slots'] and 'value' in intent['slots']['State']:

        # Get the city from the intent
        city = intent['slots']['City']['value'].title()

        try:
            # Build Google Maps API call and replace all spaces with %20 for HTTP GET parameter
            mapsURL = "https://maps.googleapis.com/maps/api/geocode/json?address=%s" % city.replace(" ", "%20")
            
            # Call the Google Maps API to get the latitude and longitude of the city
            locationData = json.load(urllib2.urlopen(mapsURL))
    
            # If there are multiple cities with the same name, find the one with the state that the user provided
            for location in locationData['results']:
                stateIndex = getStateNameIndex(location)
                
                # Grab the latitude and longitude from the Google Maps API to pass to the eBird API
                if location['address_components'][stateIndex]['long_name'] == intent['slots']['State']['value'].title():
                    state = location['address_components'][stateIndex]['long_name']
                    latitude = location['geometry']['location']['lat']
                    longitude = location['geometry']['location']['lng']
                    break
    
            # Build eBird API call. Set max results returned to 10.
            eBirdURL = "https://ebird.org/ws1.1/data/obs/geo/recent?lng=%f&lat=%f&maxResults=10&fmt=json" % (longitude, latitude)
            eBirdData = json.load(urllib2.urlopen(eBirdURL))
            
            # Convert the eBird JSON response to a string of bird names
            birdSightings = buildBirdListAsString(eBirdData, len(eBirdData))
    
            # Format Alexa's response based on the number of recent sightings
            speech_output = buildRecentSightingsResponse(eBirdData, city, state, birdSightings)
            
        except:
            should_end_session = False
            
    else:
        should_end_session = False
        
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, None, should_end_session))
        



# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "GetBirdsWithPlace":
        return get_bird_data(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    This statement prevents someone else from configuring a skill that sends 
    requests to this function.
    """
    if (event['session']['application']['applicationId'] !=
            "amzn1.ask.skill.a8960bfa-8f7b-4050-9630-b33f1ecf0e2c"):
        raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
