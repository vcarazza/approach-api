import json
import boto3
import logging

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from botocore.exceptions import ClientError

REGION_NAME = "us-east-1"
SECRETS_NAME = "approach_arenawinners"

def get_AWS_secrets():
    # Create a Secrets Manager client
    session = boto3.Session()
    client = session.client(

        service_name='secretsmanager',
        region_name=REGION_NAME
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=SECRETS_NAME
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    return json.loads(get_secret_value_response['SecretString'])


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def make_response(status_code, body):
    response = {
        'statusCode': status_code,
        'body': json.dumps(body),
        'headers': {
            'Access-Control-Allow-Headers':
            'Content-Type,X-Amz-Date,X-Amz-Security-Token,Authorization,X-Api-Key,X-Requested-With,Accept,Access-Control-Allow-Methods,Access-Control-Allow-Origin,Access-Control-Allow-Headers',
            'Access-Control-Allow-Methods': 'OPTIONS,GET',
            'Access-Control-Allow-Credentials': True,
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        }
    }
    return response


def list_subscriptions(event, context):
    try:
        
        # Retrieve secrets
        SECRETS = get_AWS_secrets()
        google_secrets = json.loads(SECRETS.get('google'))
        
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']

        credentials = ServiceAccountCredentials.from_json_keyfile_dict(google_secrets, scope)
        gc = gspread.authorize(credentials)
        gsheet = gc.open_by_url('https://docs.google.com/spreadsheets/d/1gkyvW7UXqNRsc-_VW9DUz88FEzXNMmJTkeEGHKRKSqY/edit?resourcekey=&gid=222744022')
        spreadsheets = [spreadsheet.get_all_values() for spreadsheet in gsheet.worksheets()]

        headers = [data.pop(0) for data in spreadsheets]
        data = [dict(zip(headers[i], row)) for i in range(len(spreadsheets)) for row in spreadsheets[i]]

        # Convert to JSON
        data_json = json.dumps(data)

        return make_response(200, {'data': data_json})
    except Exception as ex:
        logging.error(f"Exception error! Error description: {str(ex)}")
        return make_response(404, {"error":"Internal error"})

if __name__ == '__main__':
    list_subscriptions(event=None,context=None)

