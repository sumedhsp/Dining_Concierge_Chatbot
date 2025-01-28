import json
import boto3
import datetime
import uuid

lex_client = boto3.client('lexv2-runtime')

def lambda_handler(event, context):
    # TODO implement
    
    # Define the Lex V2 bot details
    bot_id = '3QLFE02KTP'  # The unique ID of your Lex V2 bot
    bot_alias_id = 'TSTALIASID'  # The bot alias ID (version) you want to use
    locale_id = 'en_US'  # The language locale, e.g., en_US for English (US)
    
    print (event)
    print (context)
    sessionToken =  event.get('sessionToken', 'null')
    if (sessionToken == 'null'):
        sessionToken = "12345678" #str(uuid.uuid4())
    
    messages = event['messages']
    
    for message in messages:
        if (message['type'] == 'unstructured'):
            input_text = message['unstructured']['text']
            
            # Call the Lex V2 bot using post_text method
            response = lex_client.recognize_text(
                botId=bot_id,
                botAliasId=bot_alias_id,
                localeId=locale_id,
                sessionId=sessionToken,
                text=input_text
            )
    
            # Log the Lex V2 response for debugging purposes
            #print(f"Lex V2 Response: {json.dumps(response, indent=4)}")
            
            # Process the response from Lex V2
            lex_message = response.get('messages', [{}])[0].get('content', 'No message from Lex')
            
            total_response_content = response.get('messages', [{}])
            
            buffer_message = []
            
            for i, conv in enumerate(total_response_content):
                local_msg = {
                        "type":"unstructured",
                        "unstructured": {
                            "id":str(i),
                            "text": conv.get('content',''),
                            "timestamp": str(datetime.datetime.now().timestamp())
                        }
                    }
                buffer_message.append(local_msg)
            
            # Return a response (this could be an HTTP response, a chatbot response, etc.)
            return {
                'statusCode': 200,
                'messages': buffer_message,
                'sessionID': sessionToken
            }
    
    