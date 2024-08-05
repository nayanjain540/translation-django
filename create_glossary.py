import os
from google.cloud import translate_v3beta1 as translate

# this is where you decided to download your service account credentials
SERVICE_ACCOUNT_CREDENTIALS = '/home/ubuntu/translation-django/google_credentials.json'

# You must set this environment variable before you initialize the TranslationServiceClient
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = SERVICE_ACCOUNT_CREDENTIALS

# Initialize the TranslationServiceClient
translation_client = translate.TranslationServiceClient()

# insert your own PROJECT ID here
PROJECT_ID = 'bamboo-host-424020-c9'

# insert your own BUCKET NAME and FILENAME here
BUCKET_NAME = 'glossary-bucket-translation'
FILENAME = 'glossary.csv'
GLOSSARY_URI = f'gs://{BUCKET_NAME}/{FILENAME}'

# you can decide your own GLOSSARY_ID. this is used if you need to update/delete
# the glossary resource
GLOSSARY_ID = 'my-glossary'

# GLOSSARY_LANGS are the languages your glossary supports. These are the
# languages in the column headers of your glossary
GLOSSARY_LANGS = ["en", "hi", "gu", "mr", "ml"]
LOCATION = 'us-central1'

def create_glossary_resource():
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}"
    glossary = {
        'language_codes_set': {
            'language_codes': GLOSSARY_LANGS
        },
        'name': f"projects/{PROJECT_ID}/locations/{LOCATION}/glossaries/{GLOSSARY_ID}",
        'input_config': {
            'gcs_source': {
                'input_uri': GLOSSARY_URI
            }
        }
    }
    
    request = {'parent': parent, 'glossary': glossary}

    print('Creating glossary resource...')
    # Create glossary using a long-running operation
    operation = translation_client.create_glossary(request=request)

    # Wait for the operation to complete
    response = operation.result()

    print('Created glossary:')
    print(f"InputUri {glossary['input_config']['gcs_source']['input_uri']}")

create_glossary_resource()