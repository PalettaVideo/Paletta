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

# Get environment variables from Lambda configuration
UPLOAD_BUCKET = os.environ.get('UPLOAD_BUCKET')
URL_EXPIRATION_SECONDS = 300  # 5 minutes

def lambda_handler(event, context):
    """
    This function generates a presigned S3 URL for file uploads.
    It is triggered by an API Gateway request.
    CORS is configured and handled by API Gateway, not in this function.
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract fileName and contentType from the query string
        query_params = event.get('queryStringParameters')
        if not query_params:
            return {
                'statusCode': 400, 
                'body': json.dumps({'error': 'Missing query string parameters: fileName and contentType are required.'})
            }
        
        file_name = query_params.get('fileName')
        content_type = query_params.get('contentType')

        if not file_name or not content_type:
            return {
                'statusCode': 400, 
                'body': json.dumps({'error': 'Query string must include fileName and contentType.'})
            }
        
        # Create a unique S3 key to prevent file overwrites
        unique_id = uuid.uuid4()
        file_extension = os.path.splitext(file_name)[1]
        s3_key = f"videos/{unique_id}{file_extension}"

        # Generate the presigned URL for a PUT request
        presigned_url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': UPLOAD_BUCKET,
                'Key': s3_key,
                'ContentType': content_type,
            },
            ExpiresIn=URL_EXPIRATION_SECONDS
        )

        logger.info(f"Successfully generated presigned URL for key: {s3_key}")
        
        # Return the presigned URL and the key to the client
        response_body = {
            'uploadURL': presigned_url,
            'key': s3_key
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_body)
        }

    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error. Could not generate presigned URL.'})
        } 