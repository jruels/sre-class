import json
import boto3
import uuid
import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('UserRecords')

def lambda_handler(event, context):
    record_id = str(uuid.uuid4())
    timestamp = datetime.datetime.utcnow().isoformat()
    table.put_item(Item={"RecordId": record_id, "Timestamp": timestamp})
    return {
        'statusCode': 200,
        'body': f'Record saved with ID: {record_id}'
    }