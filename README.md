# Dining Concierge Chatbot - Serverless Web Application

This project is a serverless, microservice-driven web application that leverages AWS services to provide restaurant recommendations based on user preferences. It is powered by Natural Language Processing (NLP) using Amazon Lex for chatbot interactions and several AWS services like DynamoDB, SQS, Lambda, and ElasticSearch for backend operations.

## Features

1. **Serverless Architecture**: The entire application is built using AWS Lambda functions, API Gateway, and other AWS services, ensuring high scalability and low operational cost.
2. **Chatbot Integration**: A chatbot powered by Amazon Lex allows users to interact and provide their preferences (location, cuisine, dining time, number of people).
3. **Restaurant Recommendations**: Restaurant data is fetched from Yelp API and stored in DynamoDB. ElasticSearch is used for fast retrieval of restaurant suggestions.
4. **Queue Management**: Requests are queued using SQS and processed by a Lambda function that provides restaurant suggestions via email using SES.
5. **Stateless and State-based Recommendations**: Provides both real-time restaurant suggestions and maintains state for returning users with saved preferences.

## Architecture Overview

The project utilizes the following AWS services:
- **Amazon S3**: Hosts the frontend of the application.
- **API Gateway**: Manages the API endpoints that interact with the chatbot and other services.
- **AWS Lambda**: Contains multiple functions for chatbot processing, handling API requests, and sending recommendations via email.
- **Amazon Lex**: Handles the NLP chatbot interaction.
- **DynamoDB**: Stores restaurant data and session state information.
- **ElasticSearch**: Indexes restaurant data for quick search and retrieval.
- **SQS (Simple Queue Service)**: Handles queuing of user requests for processing.
- **SES (Simple Email Service)**: Sends restaurant suggestions via email.

