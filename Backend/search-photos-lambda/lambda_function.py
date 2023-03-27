import json
import random 
import decimal 
import time
from config import *
import boto3
import datetime
import re
import uuid
from zoneinfo import ZoneInfo
import inflect
from opensearchpy import OpenSearch, RequestsHttpConnection


def get_slots(intent_request):
    return intent_request['sessionState']['intent']['slots']
    
def get_slot(intent_request, slotName):
    slots = get_slots(intent_request)
    if slots is not None and slotName in slots and slots[slotName] is not None:
        return slots[slotName]['value'].get('interpretedValue') or slots[slotName]['value'].get('originalValue')
    else:
        return None

        
def get_session_attributes(intent_request):
    sessionState = intent_request['sessionState']
    print("Session attributes, ", sessionState)
    if 'sessionAttributes' in sessionState:
        if 'current_session_id' not in sessionState['sessionAttributes']:
            sessionState['sessionAttributes']['current_session_id'] = str(uuid.uuid4())
        return sessionState['sessionAttributes']

    return {}

def close(intent_request, session_attributes, fulfillment_state, message, dialogState):
    intent_request['sessionState']['intent']['state'] = fulfillment_state
    return {
        'sessionState': {
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': dialogState
            },
            'intent': intent_request['sessionState']['intent']
        },
        'messages': [message],
        'sessionId': intent_request['sessionId'],
        'requestAttributes': intent_request['requestAttributes'] if 'requestAttributes' in intent_request else None
    }

def create_client():
    host = 'https://search-photos-i2pm6nlhd5qlkcigtklk7qchk4.us-east-1.es.amazonaws.com'
    port = 443
    auth = ('admin', 'Admin1230!')

    client = OpenSearch(
        hosts = [host],
        http_auth = auth,
        use_ssl = True,
        verify_certs = True,
        ssl_assert_hostname = False,
        ssl_show_warn = False,
        connection_class = RequestsHttpConnection
    )
    return client
    
def query_elastic_search():
    client = create_client()
    result = []
    index_name = "photos"
    resp = client.search(
            index=index_name,
            body = {
                "query": {
                    "match_all" : {}
                }
            }
        )
    print(resp) 
    for each_data in resp['hits']['hits']:
        print(each_data)
        result.extend(each_data['_source']['labels']) 
    
    result = list(set(result))
    return result
    
def check_if_categories_are_valid(category1, category2):
    """
    Checks if the categories exist in opensearch
    """
    valid_categories = query_elastic_search() 
    valid_categories.append(None)
    
    print(category1, category2, valid_categories)
    
    if category1 not in valid_categories or category2 not in valid_categories:
        return False
    else:
        return True
    

def validate_request(intent_request):
    session_attributes = get_session_attributes(intent_request)
    print(session_attributes)
    slots = get_slots(intent_request)
    category1 = get_slot(intent_request, 'category1')
    category2 = get_slot(intent_request, 'category2')
    
    p = inflect.engine()
    
    print("CloudOne context:: ", category1, category2)
    if category1 != None and p.singular_noun(category1):
        category1 = p.singular_noun(category1)
    if category2 != None and p.singular_noun(category2):
        category2 = p.singular_noun(category2)
    
    is_valid = check_if_categories_are_valid(category1, category2)
    if is_valid:
        if category1 and category2:
            message = category1 + "," + category2
        elif category1:
            message = category1
        else:
            message = "Invalid"
    else:
        message = "Invalid"
    
    dialogAction = 'ElicitIntent'
    
    data =  {
            'contentType': 'PlainText',
            'content': message
        }
    print("before close::", data)
    fulfillment_state = "Fulfilled"   
    
    return close(intent_request, session_attributes, fulfillment_state, data, dialogAction)   

def dispatch(intent_request):
    intent_name = intent_request['sessionState']['intent']['name']
    response = None
    print(intent_name)
    if intent_name != "GreetingIntent":
        print('Intent with name ' + intent_name + ' not supported')
        return None
    else:
        return validate_request(intent_request)
        
        
def lambda_handler(event, context):
    # TODO implement
    print(event)
    # event = {'sessionId': '023011713484875', 'bot': {'aliasId': 'TSTALIASID', 'aliasName': 'TestBotAlias', 'name': 'Photo-search-bot', 'version': 'DRAFT', 'localeId': 'en_US', 'id': 'KC165FERXS'}, 'inputTranscript': 'papers and pins', 'interpretations': [{'intent': {'confirmationState': 'None', 'name': 'GreetingIntent', 'state': 'InProgress', 'slots': {'category2': {'shape': 'Scalar', 'value': {'originalValue': 'pins', 'resolvedValues': ['pins'], 'interpretedValue': 'pins'}}, 'category1': {'shape': 'Scalar', 'value': {'originalValue': 'papers', 'resolvedValues': ['papers'], 'interpretedValue': 'papers'}}}}, 'nluConfidence': 1.0}, {'intent': {'confirmationState': 'None', 'name': 'FallbackIntent', 'state': 'InProgress', 'slots': {}}}], 'responseContentType': 'text/plain; charset=utf-8', 'messageVersion': '1.0', 'invocationSource': 'DialogCodeHook', 'transcriptions': [{'resolvedContext': {'intent': 'GreetingIntent'}, 'transcription': 'papers and pins', 'resolvedSlots': {'category2': {'shape': 'Scalar', 'value': {'originalValue': 'pins', 'resolvedValues': ['pins']}}, 'category1': {'shape': 'Scalar', 'value': {'originalValue': 'papers', 'resolvedValues': ['papers']}}}, 'transcriptionConfidence': 1.0}], 'sessionState': {'sessionAttributes': {}, 'intent': {'confirmationState': 'None', 'name': 'GreetingIntent', 'state': 'InProgress', 'slots': {'category2': {'shape': 'Scalar', 'value': {'originalValue': 'pins', 'resolvedValues': ['pins'], 'interpretedValue': 'pins'}}, 'category1': {'shape': 'Scalar', 'value': {'originalValue': 'papers', 'resolvedValues': ['papers'], 'interpretedValue': 'papers'}}}}, 'originatingRequestId': '49ef7900-44c5-402f-ac0e-4ecf727f8c69'}, 'inputMode': 'Text'}
    print(context)
    response = {} 
    response = dispatch(event)
    print(response)
    return response