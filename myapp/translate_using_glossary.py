import os
from google.cloud import translate_v3beta1 as translate

# this is where you decided to download your service account credentials
SERVICE_ACCOUNT_CREDENTIALS = os.getcwd() +  '/google_credentials.json'

# You must set this environment variable before you initialize the TranslationServiceClient
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = SERVICE_ACCOUNT_CREDENTIALS

# Initialize the TranslationServiceClient
translation_client = translate.TranslationServiceClient()

# insert your own PROJECT ID here
PROJECT_ID = 'bamboo-host-424020-c9'

# Location
LOCATION = 'us-central1'

# Glossary ID
GLOSSARY_ID = 'my-glossary'

# GLOSSARY_LANGS are the languages your glossary supports. These are the
# languages in the column headers of your glossary
GLOSSARY_LANGS = ['en', 'gu', 'hi', 'mr', 'ml']

def translate_text_with_glossary(string_of_text, source_language_code, target_language_code):
    glossary_config = {
        'glossary': f"projects/{PROJECT_ID}/locations/{LOCATION}/glossaries/{GLOSSARY_ID}",
        'ignore_case':True
    }

    request = {
        'parent': f"projects/{PROJECT_ID}/locations/{LOCATION}",
        'contents': [string_of_text],
        'mime_type': 'text/plain',  # mime types: text/plain, text/html
        'source_language_code': source_language_code,
        'target_language_code': target_language_code,
    }

    # only use the glossary if it includes the languages we are translating to and from
    if source_language_code in GLOSSARY_LANGS and target_language_code in GLOSSARY_LANGS:
        request['glossary_config'] = glossary_config

    response = translation_client.translate_text(request=request)

    translations = []

    # if we used the glossary, the translations will end up in response.glossary_translations
    # otherwise, it will end up in response.translations
    if response.glossary_translations:
        print("here")
        translations = response.glossary_translations[0].translated_text
    else:
        translations = response.translations[0].translated_text

    print("Google translation result %s", translations)
    return translations 

    #for translation in translations:
    #    print(f"Translation: {translation.translated_text}")


# Example usage
# translate_text_with_glossary("I want the monthly average balance", "en", "gu")