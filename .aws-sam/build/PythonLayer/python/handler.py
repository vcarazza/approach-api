import json
import boto3
import re
import logging
from datetime import datetime

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from botocore.exceptions import ClientError

REGION_NAME = "us-east-1"
SECRETS_NAME = "approach_arenawinners"

def get_AWS_secrets():
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
            'Access-Control-Allow-Methods': 'OPTIONS,GET,POST',
            'Access-Control-Allow-Credentials': True,
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        }
    }
    return response


def clean_headers(headers):
    cleaned_headers = [
        re.sub(r'^\s*REQUISITOS SOBRE O\s*', '', re.sub(r'\s*\(.*?\)\s*', '', header)).strip()
        for header in headers
    ]
    return cleaned_headers

# Function to calculate age from birth date
def calculate_age(birth_date, current_date):
    birth_date = datetime.strptime(birth_date, '%d/%m/%Y')
    age = current_date.year - birth_date.year - ((current_date.month, current_date.day) < (birth_date.month, birth_date.day))
    return age

# Function to clean and format phone number
def clean_phone_number(phone_number):
    return re.sub(r'\D', '', phone_number)


def list_subscriptions(event, context):
    try:
        # Retrieve secrets
        SECRETS = get_AWS_secrets()
        stored_password = SECRETS.get('password')
        
        # Retrieve password from the event
        body = json.loads(event['body'])
        provided_password = body.get('password')
        
        if provided_password != stored_password:
            return make_response(401, {"error": "Senha incorreta!"})
        
        google_secrets = json.loads(SECRETS.get('google'))
        
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']

        credentials = ServiceAccountCredentials.from_json_keyfile_dict(google_secrets, scope)
        gc = gspread.authorize(credentials)
        gsheet = gc.open_by_url('https://docs.google.com/spreadsheets/d/1gkyvW7UXqNRsc-_VW9DUz88FEzXNMmJTkeEGHKRKSqY/edit?resourcekey=&gid=222744022')
        spreadsheets = [spreadsheet.get_all_values() for spreadsheet in gsheet.worksheets()]

        headers = [clean_headers(data.pop(0)) for data in spreadsheets]
        data = [dict(zip(headers[i], row)) for i in range(len(spreadsheets)) for row in spreadsheets[i]]
        
        # Current date (today's date)
        current_date = datetime.today()

        # Add 'age' to each record
        for record in data:
            birth_date = record['DATA DE NASCIMENTO']
            age = calculate_age(birth_date, current_date)
            record['Idade'] = age
            cleaned_phone = clean_phone_number(record['TELEFONE'])
            record['whatsapp'] = f"https://api.whatsapp.com/send?phone=55{cleaned_phone}"
            del record['DATA DE NASCIMENTO']

        # Convert to JSON
        # Sort data by 'NOME'
        data.sort(key=lambda x: x['NOME'])

        data_json = json.dumps(data)

        return make_response(200, {'data': data_json})
    except Exception as ex:
        logging.error(f"Exception error! Error description: {str(ex)}")
        return make_response(404, {"error":"Internal error"})

if __name__ == '__main__':
    list_subscriptions(event=None,context=None)
