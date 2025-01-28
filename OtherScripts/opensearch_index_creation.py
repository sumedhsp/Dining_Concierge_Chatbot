import boto3
import requests
from requests_aws4auth import AWS4Auth
import json
from opensearchpy import OpenSearch, RequestsHttpConnection

# Set up AWS clients and credentials
access_key = 'AWS_ACCESS_KEY'
secret_key = 'AWS_SECRET_KEY'
dynamodb = boto3.resource('dynamodb', 
                          aws_access_key_id=access_key,
                          aws_secret_access_key=secret_key,
                          region_name='us-east-1')
table = dynamodb.Table('yelp-restaurants')  # DynamoDB table name

# OpenSearch details
region = 'us-east-1'  # e.g., 'us-east-1'
service = 'es'
opensearch_host = 'search-restaurants-sotlhoitstaaxvua7geerld6hq.us-east-1.es.amazonaws.com'  # OpenSearch domain endpoint
index_name = 'restaurants'  # OpenSearch index name

# Get AWS credentials
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(access_key, secret_key, region, service)

# OpenSearch endpoint
opensearch_url = f"https://{opensearch_host}/{index_name}/_doc"

username = "OpenSearch_username"
password = "OpenSearch_Password"

client = OpenSearch(
    hosts=[{'host': opensearch_host, 'port': 443}],
    http_auth=(username, password),
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
    )

# Function to send data to OpenSearch
def index_data_to_opensearch(item):
    # Extract only the fields you want to index (cuisines and business_id)
    cuisines = {
        'cuisines': item.get('Cuisine', [])
    }
    
    restaurant_id = item.get('BusinessID')

    response = client.index(
        index=index_name,
        body=cuisines,
        id=restaurant_id,  # Optional document ID. If not provided, OpenSearch will auto-generate an ID.
        refresh=True  # Ensures the document is immediately searchable
    )

    #print (response)


# Function to scan DynamoDB and populate OpenSearch
def populate_opensearch_from_dynamodb():
    # Scan DynamoDB table
    response = table.scan()
    data = response.get('Items', [])
    
    # Iterate over each item in the table and send to OpenSearch
    for item in data:
        # Print item for debugging
        print(f"Indexing item: {item}")
        
        # Index only relevant fields to OpenSearch
        index_data_to_opensearch(item)

    print ("Finished sending data to Elastic search..")        
    # Handle pagination if there are more records
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data = response.get('Items', [])
        for item in data:
            print(f"Indexing item: {item}")
            index_data_to_opensearch(item)

if __name__ == "__main__":
    populate_opensearch_from_dynamodb()
