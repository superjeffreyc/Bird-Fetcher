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
            'title': "Bird Fetcher - " + title,
            'content': "Bird Fetcher - " + output
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
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the Bird Fetcher skill," \
                    "Please tell me your location of interest by saying, " \
                    "Birds near Binghamton, "
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please tell me your location of interest by saying, " \
                    "Birds near Binghamton, "
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


def get_bird_data(intent, session):

    card_title = intent['name']
    session_attributes = {}
    should_end_session = True
    speech_output = "I'm not sure what your city is. Please try again by " \
                    "saying, birds near Binghamton"
    
    if 'Location' in intent['slots']:
        
        # Try to call Google Maps API and eBird API based on location in intent
        try:
            # Get the city from the intent and call the Google Maps API
            city = intent['slots']['Location']['value']
            mapsURL = "https://maps.googleapis.com/maps/api/geocode/json?address=%s" % city
            locationData = json.load(urllib2.urlopen(mapsURL))
            
            # Grab the latitude and longitude and call the eBird API
            latitude = locationData['results'][0]['geometry']['location']['lat']
            longitude = locationData['results'][0]['geometry']['location']['lng']
            eBirdURL = "https://ebird.org/ws1.1/data/obs/geo/recent?lng=%f&lat=%f&maxResults=10&fmt=json" % (longitude, latitude)
            eBirdData = json.load(urllib2.urlopen(eBirdURL))
            
            birdSightings = ""          # List of 10 recent birds seen
            lastDate = ""               # Oldest date among the 10 recent bird sightings
            dataSize = len(eBirdData)   # Grab the number of entries (could possibly be less than 10)
            
            for sighting in eBirdData:
                birdSightings += "%s, " % sighting['comName']
                dataSize -= 1
                lastDate = sighting['obsDt'].split()[0]     # Only grab the date, ignore the time
                
                # Insert the word 'and' before the last sighting to make it sound better
                if dataSize == 1:
                    birdSightings += " and "
    
            if len(eBirdData) == 0:
                speech_output = "There are no recent sightings in %s." % city
            elif len(eBirdData) == 1:
                speech_output = "The only recent bird seen since %s in %s is a %s" % (lastDate, city, birdSightings)
            else:
                speech_output = "The %s most recent birds seen since %s in %s are %s" % (str(len(eBirdData)), lastDate, city, birdSightings)
                
        # Problem with the city name provided        
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

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])