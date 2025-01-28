import json
import boto3

# For Open Search
import urllib3
import os
from base64 import b64encode


sqs = boto3.client('sqs')

# SQS Queue URL
QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/565393062640/SuggestionsQueue'

def lambda_handler(event, context):
    
    # Pull a message from SQS Queue
    try:
        # Receive message from SQS queue
        response = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=1,  # Set to the number of messages you want to process at once
            WaitTimeSeconds=5  # Enable long polling for efficiency
        )
        
        # Check if there are any messages in the response
        messages = response.get('Messages', [])
        if not messages:
            print("No messages available in the queue.")
            return {
                'statusCode': 200,
                'body': json.dumps('No messages in the queue.')
            }
        
        count = 0
        for message in messages:
            # Process the message (you can customize this based on your requirements)
            print(f"Received message: {message['Body']}")
            
            # Extract message ID and receipt handle (needed for deleting the message later)
            receipt_handle = message['ReceiptHandle']
            message_body = message['Body']
            
            # Example: Process the message body (you can customize this)
            isProcessed = process_message(message_body)
            
            if (isProcessed):
                    
                # Delete the message after processing it
                sqs.delete_message(
                    QueueUrl=QUEUE_URL,
                    ReceiptHandle=receipt_handle
                )
                
                print(f"Deleted message with receipt handle: {receipt_handle}")
                count += 1
            else:
                print ("Error occurred while processing the message. Receipt Handle: " + str(receipt_handle))
                continue
        
        
        return {
            'statusCode': 200,
            'body': json.dumps(f"Processed {count} message(s)")
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {str(e)}")
        }
    
    
def process_message(message_body):
    # You can parse the message if it's in JSON format or handle it based on its content
    messageJson = json.loads(message_body)
    email = messageJson['Email']
    cuisine = messageJson['Cuisine']
    
    # Connect to Elastic Search and Retrieve details
    business_ids = getOpenSearchResults(cuisine)
    
    if (len(business_ids) == 0):
        print ("Failed to process message for " + str(email))
        return False
    
    # Connect to DynamoDB and get the details
    dynamodb = boto3.resource('dynamodb',
                              aws_access_key_id='AWS_ACCESS_KEY',
                              aws_secret_access_key='AWS_SECRET_KEY',
                              region_name='us-east-1')
    
    # DynamoDB table name
    table_name = 'yelp-restaurants'
    
    batch_keys = {
        table_name : {
            'Keys' : [{'BusinessID' : business_id, 'Cuisine' : cuisine} for business_id in business_ids]
        }
    }
    response = dynamodb.batch_get_item(RequestItems=batch_keys)
    
    items = response.get('Responses', {}).get(table_name, [])
    
    # Format the details
    records = []
    
    for item in items:
        address = item['address']
        name = item['name']
        rating = item['rating']
        reviewCount = item['review_count']
        
        # New Formatted details
        record = {
            "Name": item['name'],
            "Address": item['address'],
            "Rating": item.get('rating','N/A'),
            "ReviewCount" : item.get('review_count','N/A')
        }
        
        records.append(record)
    
    records = sorted(records, key=lambda x: x['Rating'], reverse=True)
    
    # Create email body using html
    html_content = format_details_as_html(records, cuisine)
    
    # Send the email using SES
    res = send_email_ses(html_content, "From Dining Concierge", email)
    
    print ("Email response : " + str(res))
    if (res):
        return True
    else:
        return False
            
def send_email_ses(html_content, subject, recipient_email):
    ses_client = boto3.client('ses', region_name='us-east-1')  # Replace with your AWS region

    # Send the email using SES
    response = ses_client.send_email(
        Source="sumedhsparvatikar@gmail.com",  # Verified SES email address
        Destination={
            "ToAddresses": [
                recipient_email,
            ]
        },
        Message={
            "Subject": {
                "Data": subject,
                "Charset": "UTF-8"
            },
            "Body": {
                "Html": {
                    "Data": html_content,
                    "Charset": "UTF-8"
                }
            }
        }
    )
    return response

def format_details_as_html(records, cuisine):
    # Create a basic HTML structure
    html_content = """
    <html>
    <head>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            table, th, td {
                border: 1px solid black;
            }
            th, td {
                padding: 10px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
        </style>
    </head>"""
    
    html_content += f"""<body>
        <h2> {cuisine.capitalize()} Restaurant Suggestions </h2>
        <p>Here are our favorite picks based on your profile :</p>
        <table>
            <tr>
                <th>Name</th>
                <th>Location</th>
                <th>Rating</th>
                <th>Reviews</th>
            </tr>
    """

    # Add each record as a new row in the table
    for record in records:
        html_content += f"""
            <tr>
                <td>{record.get('Name', 'N/A')}</td>
                <td>{record.get('Address', 'N/A')}</td>
                <td>{record.get('Rating','N/A')}</td>
                <td>{record.get('ReviewCount')}</td>
            </tr>
        """

    # Close the HTML tags
    html_content += """
        </table>
    <p>Hope you enjoy our choices and a satiating meal!</p>
    </body>
    </html>
    """

    return html_content



# Initialize the urllib3 HTTP connection pool
http = urllib3.PoolManager()

# Function to query OpenSearch
def getOpenSearchResults(cuisine):
    
    OPENSEARCH_HOST = 'https://search-restaurants-sotlhoitstaaxvua7geerld6hq.us-east-1.es.amazonaws.com'  # e.g., https://your-domain-name.us-east-1.es.amazonaws.com
    
    USERNAME = 'OpenSearch_Username'
    PASSWORD = 'OpenSearch_Password'
    
    index_name = 'restaurants'
    
    # Replace with your OpenSearch index name
    search_url = f"{OPENSEARCH_HOST}/{index_name}/_search"
    
    # Define the OpenSearch query
    query = {
        "size": 5,
        "query": {
            "match": {
                "cuisines": cuisine  # Modify based on your query requirements
            }
        }
    }

    # Encode username and password for Basic Authentication
    basic_auth = f"{USERNAME}:{PASSWORD}"
    encoded_auth = b64encode(basic_auth.encode()).decode('utf-8')

    # Prepare headers with Basic Auth and content type
    headers = {
        'Authorization': f"Basic {encoded_auth}",
        'Content-Type': 'application/json'
    }
    
    try:
        # Send the HTTP POST request to OpenSearch
        response = http.request(
            'POST',
            search_url,
            body=json.dumps(query),
            headers=headers
        )

        # Parse the response
        if response.status == 200:
            
            search_results = json.loads(response.data.decode('utf-8'))['hits']['hits']
            
            print (search_results)
            
            business_ids = []
            for result in search_results:
                business_ids.append(result['_id'])
            
            return business_ids

        else:
            return []

    except Exception as e:
        print ("Exception occured at OpenSearch section. Details:" + str(e))
        return []
