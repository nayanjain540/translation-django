from openai import OpenAI
import base64
import os
from dotenv import load_dotenv

load_dotenv()  

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key=OPENAI_API_KEY)

# myapp/views.py
from .models import *
import requests
import json
import re
from os import environ

from google.cloud import translate
import datetime
from .translate_using_glossary import *
from .transliterate import *
from .prompt import *

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def return_openai_response_gpt_4o(messages_list):
    try:

        response_openai = client.chat.completions.create(
                        model="gpt-4o",
                        response_format={"type": "json_object"},
                        messages=messages_list,
                        max_tokens=4096,
                        )

        extracted_text_content = json.loads(response_openai.choices[0].message.content)
        
        return extracted_text_content
    except Exception as e:
        return "Error"

def return_openai_response_gpt_4_turbo(messages_list):
    try:

        response_openai = client.chat.completions.create(
                        model="gpt-4-turbo",
                        response_format={"type": "json_object"},
                        messages=messages_list,
                        max_tokens=4096,
                        )

        extracted_text_content = json.loads(response_openai.choices[0].message.content)
        print("HEREEE in return_openai_response_gpt_4_turbo")
        return extracted_text_content
    except Exception as e:
        return "Error"

def final_translation_function(input_sentence, target_language):
    try:
        do_not_translate_words = []

        for items in transliterated_terms:
            if items["term"].lower() in input_sentence.lower():
                do_not_translate_words.append(items[target_language])

        target_language_dict = {
                        "hin_Deva": "hi",
                        "guj_Gujr": "gu",
                        "mar_Deva": "mr",
                        "mal_Mlym": "ml"
                    }

        language_dictionary = {
                        "hin_Deva": "hindi",
                        "guj_Gujr": "gujarati",
                        "mar_Deva": "marathi",
                        "mal_Mlym": "malayalam"
                    }

        translations_google = translate_text_with_glossary(input_sentence,'en', target_language_dict[target_language])

        sending_for_refined_sentences = {}
        sending_for_refined_sentences["original_english_sentence"] = input_sentence
        sending_for_refined_sentences["translations"] = translations_google

        base_system_message = f"I need you to be a {language_dictionary[target_language]} BANK translator for common people, I will give you a sentence, you need to give me a sentence which is much more readable and understandable to the common man. DONT CHANGE THE CONTEXT, MEANING, TONE."

        input_sentence_updated_arr = input_sentence.split(" ")

        if len(input_sentence_updated_arr) <= 3:
            base_system_message = f"I need you to be a {language_dictionary[target_language]} BANK translator.  "
            base_system_message += "You are translating a banking app into regional languages. Your job is make sure that the UI of the app is not affected because of the translations. For instance 'accounts' when translated in hindi would mean 'हिसाब किताब' but since you are a banking app translator, you will keep it 'खाते'. Since app has limited space in terms of UI, we will keep it simple. You can even transliterate them for the common people. For example 'statement' can become 'स्टेटमेंट'. This will ensure that the translations are not very complex"
            sending_for_refined_sentences["translations"] = " "

        if len(do_not_translate_words) != 0:
            base_system_message += f"\n Do not try to change or update the words in the given array: {do_not_translate_words}"              
        
        base_system_message = BASE_TRANSLATE_INSTRUCTIONS

        message_list = [
                    {
                      "role": "user",
                      "content": [
                        {"type": "text", "text": base_system_message},
                        {"type": "text", "text": f"{sending_for_refined_sentences}"}
                      ],
                    },
                  ]

        extracted_text_content = return_openai_response_gpt_4_turbo(message_list)

        try:
            final_translation = extracted_text_content["translations"]
        except Exception as e:
           final_translation = extracted_text_content["corrected_translation"]

        if final_translation == "":
            final_translation = translations_google

        print("Final translation of the function final_translation %s", final_translation)

        return final_translation
    except Exception as e:
        print("Error is %s" , str(e))

        
