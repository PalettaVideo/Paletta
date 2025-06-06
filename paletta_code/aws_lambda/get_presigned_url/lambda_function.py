import boto3
import json
import os
import uuid
import logging

# Configure logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Boto3 S3 client
s3 = boto3.client('s3')

# Get environment variables
UPLOAD_BUCKET = os.environ.get('UPLOAD_BUCKET')
ALLOWED_ORIGIN = os.environ.get('ALLOWED_ORIGIN', '*') # The domain of your frontend
URL_EXPIRATION_SECONDS = 300  # 5 minutes

def lambda_handler(event, context):
    """
    Handles API Gateway request to generate a presigned S3 URL for uploading a video.
    """
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # Get file metadata from the query string parameters
        # Example: ?fileName=my-video.mp4&contentType=video/mp4
        query_params = event.get('queryStringParameters')
        if not query_params:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing query string parameters fileName and contentType.'})
            }
        
        file_name = query_params.get('fileName')
        content_type = query_params.get('contentType')

        if not file_name or not content_type:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Both fileName and contentType are required.'})
            }
        
        # Generate a unique key for the S3 object to prevent overwrites
        unique_id = uuid.uuid4()
        file_extension = os.path.splitext(file_name)[1]
        s3_key = f"videos/{unique_id}{file_extension}"

        # Create the presigned URL
        presigned_url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': UPLOAD_BUCKET,
                'Key': s3_key,
                'ContentType': content_type,
            },
            ExpiresIn=URL_EXPIRATION_SECONDS
        )

        logger.info(f"Generated presigned URL for key: {s3_key}")
        
        # Prepare the successful response
        response_body = {
            'uploadURL': presigned_url,
            'key': s3_key
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': ALLOWED_ORIGIN,
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps(response_body)
        }

    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': ALLOWED_ORIGIN,
            },
            'body': json.dumps({'error': 'Failed to generate presigned URL.'})
        } 