import json
import boto3

sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb',
                              aws_access_key_id='AWS_KEY',
                              aws_secret_access_key='AWS_SECRET_KEY',
                              region_name='us-east-1')
intermediary_state = dynamodb.Table('intermediary_state')

def lambda_handler(event, context):
    
    # Event can be null
    if (event is None):
        return None

    URL = 'https://sqs.us-east-1.amazonaws.com/565393062640/SuggestionsQueue'
    
    cuisine_support = ['korean', 'japanese', 'american']
    location_support = ['manhattan', 'new york']
    
    sessionId = event['sessionId']
    intent = event['sessionState']['intent']['name']
    
    
    # Hit the DB to check if the session already exists.
    resp = intermediary_state.get_item(Key={'sessionID': sessionId})
    
    print ("Response from DynamoDB", resp.get('Item'))
    
    if (intent == 'GreetingIntent'):
        sessionState = event['sessionState']
        interpretations = event['interpretations']
        
        response = {
            'sessionId' : sessionId,
            'sessionState': {
                'dialogAction': {
                    'type':"Close"
                },
                'intent':{
                    'name': "GreetingIntent",
                    'state': "Fulfilled",
                    'slots' : {}
                }
                    
            }
        }
        
        print (json.dumps(response))
        
        return response
    elif (intent == 'ThankYouIntent'):
        sessionState = event['sessionState']
        interpretations = event['interpretations']
        
        response = {
            'sessionId': sessionId,
            'sessionState' : {
                'dialogAction':{
                    'type':"Close"
                },
                'intent':{
                    'name': intent,
                    'state': "Fulfilled",
                    'slots' : {}
                }
            }
        }
        
        return response
    
    
    else:
        # Need to validate the slot values.
        
        sessionState = event['sessionState']
        interpretations = event['interpretations']
        
        slots = sessionState['intent']['slots']
        
        receivedAllSlots = False
        
        for slot in slots.keys():
            if (slots[slot] is None):
                response = {
                    'sessionId': sessionId,
                    'sessionState' : {
                        'dialogAction':{
                            'type':"ElicitSlot",
                            'slotToElicit':slot
                        },
                        'intent':{
                            'name': intent,
                            'state': "InProgress",
                            'slots' : slots
                        }
                    }
                }
                
                return response
            
            # Validate other slots
            # 1) Location
            if (slots['location'] is not None):
                loc = slots['location']['value']['interpretedValue']
                if (loc.lower() not in location_support):
                    slots['location'] = None
                    
                    response = {
                        'sessionId': sessionId,
                        'sessionState' : {
                            'dialogAction':{
                                'type':"ElicitSlot",
                                'slotToElicit': 'location'
                            },
                            'intent':{
                                'name': intent,
                                'state': "InProgress",
                                'slots' : slots
                            }
                        }
                    }
                    
                    return response
            
            print ("Slots" +str( slots))
            # 2) cuisine
            if (slots['Cuisine'] is not None):
                cus = slots['Cuisine']['value']['originalValue']
                if (cus.lower() not in cuisine_support):
                    slots['Cuisine'] = None
                    response = {
                        'sessionId': sessionId,
                        'sessionState' : {
                            'dialogAction':{
                                'type':"ElicitSlot",
                                'slotToElicit': 'Cuisine'
                            },
                            'intent':{
                                'name': intent,
                                'state': "InProgress",
                                'slots' : slots
                            }
                        }
                    }
                
                    return response
                
        
        message_body = {
            'Location': slots['location']['value']['interpretedValue'],
            'Cuisine': slots['Cuisine']['value']['interpretedValue'],
            'DiningTime': slots['DiningTime']['value']['interpretedValue'],
            'NumberOfPeople': slots['NumberOfPeople']['value']['interpretedValue'],
            'Email': slots['email']['value']['interpretedValue']
        }
        
        # Send the message to SQS
        response = sqs.send_message(
            QueueUrl=URL,
            MessageBody=json.dumps(message_body)  # Convert the payload to JSON string
        )
        
        
        intermediary_state.put_item(
            Item={
                'sessionID' : sessionId,
                'preference': message_body
            })
        
        
        # Log the response from SQS
        print(f"Message sent to SQS. Message ID: {response['MessageId']}")
        
        # To include a confirmIntent type
        # We have received all the slot values
        
        response = {
            'sessionId': sessionId,
            'sessionState' : {
                'dialogAction':{
                    'type':"Delegate"
                },
                'intent':{
                    'name': intent,
                    'state': "Fulfilled",
                    'slots' : slots
                }
            }
        }
        
        return response
        
        
