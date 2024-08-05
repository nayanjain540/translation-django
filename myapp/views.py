from django.shortcuts import render
from openai import OpenAI
import base64
import os
# Create your views here.
#api_key = os.getenv('OPENAI_API_KEY')
from dotenv import load_dotenv
load_dotenv()  # Load variables from .env file

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key=OPENAI_API_KEY)

# myapp/views.py
from django.shortcuts import render, redirect
from .forms import ImageUploadForm
from .models import UploadedImage, ExtractedData,CachedData
import requests
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from .transliterate import *
import re
from os import environ

from google.cloud import translate
import datetime
import time
from .utils import *
from .prompt import *

def upload_image(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_image = form.save()
            # Call your internal API to extract data
            script_dir = os.getcwd()
            
            image_path = script_dir + "/" + str(uploaded_image.image) 

            encoded_image = encode_image(image_path)
            
            base_system_message = UPLOAD_IMAGE_PROMPT
            
            messages_open_ai = [
                        {
                          "role": "user",
                          "content": [
                            {"type": "text", "text": base_system_message},
                            {
                              "type": "image_url",
                              "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded_image}",
                              },
                            },
                            
                          ],
                        }
                        
                      ]

            
            extracted_text_content = return_openai_response_gpt_4o(messages_open_ai)
            print("Extracted content from the image %s", extracted_text_content)
            extracted_text_content = extracted_text_content["extracted_text"]

            for items in extracted_text_content:
                ExtractedData.objects.create(
                    uploaded_image=UploadedImage.objects.get(pk=uploaded_image.id),
                    extracted_data = items
                )
            return redirect('display_data', uploaded_image.id)
    else:
        form = ImageUploadForm()
    return render(request, 'myapp/upload_image.html', {'form': form})


def translate_api(request, data_id):
    extracted_data = ExtractedData.objects.get(id=data_id)
    
    languages_list = ["hin_Deva", "guj_Gujr", "mar_Deva", "mal_Mlym"]
    for items in languages_list:

        final_translation = final_translation_function(extracted_data.extracted_data, items)
        print("Final translation inside translate api %s", final_translation)
        if items == "hin_Deva":
            extracted_data.hindi = final_translation
        if items == "guj_Gujr":
            extracted_data.gujarati = final_translation
        if items == "mar_Deva":
            extracted_data.marathi = final_translation
        if items == "mal_Mlym":
            extracted_data.malayalam = final_translation
        extracted_data.save()

    return redirect('display_data', extracted_data.uploaded_image.pk)

def sushi_test_api(request, data_id):
    try:
        print("cached_data %s", data_id)
        cached_data = CachedData.objects.get(id=data_id)

        target_language = cached_data.language_code
        if target_language == "hin_Deva":
            source_language_code = "hi"

        if target_language == "mar_Deva":
            source_language_code = "mr"

        if target_language == "guj_Gujr":
            source_language_code = "gu"

        if target_language == "mal_Mlym":
            source_language_code = "ml"

        google_translation = translate_text_with_glossary(cached_data.translation,
                                                    source_language_code, 'en')

        print("Google translation to english in sushi test %s", google_translation)
        cached_data.google_translation = google_translation
        cached_data.save()

        json_for_translation = {'original_text':cached_data.english_sentence, 'translated_english_text':google_translation}
        base_system_message = str(json_for_translation)
        base_system_message += SUSHI_TEST_PROMPT
        messages = [
                    {
                      "role": "user",
                      "content": [
                        {"type": "text", "text": base_system_message},
                      ],
                    },
                  ]

        extracted_text_content = return_openai_response_gpt_4_turbo(messages)

        print("Sushi test results %s", extracted_text_content)

        total_marks = int(extracted_text_content["key_details"])*0.45 + int(extracted_text_content['phrase_structure'])*0.35 + int(extracted_text_content['article_usage'])*0.10 + int(extracted_text_content['tonality'])*0.10
        cached_data.sushi_test_result = total_marks
        cached_data.save()
    except Exception as e:
        print(str(e))
        return Response(data={"error":str(e)})

    return redirect('sushi-test')

class TranslateParticularQuestionAPI(APIView):

    def post(self, request, *args, **kwargs):

        response = {"status": "500", "status_message": "Internal server Error"}

        try:

            start_time = datetime.datetime.now()

            request_data = request.data

            input_sentence = request_data["input"]

            target_language = request_data["target_language"]

            if CachedData.objects.filter(english_sentence=input_sentence.lower(),language_code=target_language):

               response["final_translation"] = CachedData.objects.filter(english_sentence=input_sentence.lower(),language_code=target_language)[0].translation
               response["id_of_translation_word"] = id_of_translation_word
               response["status"] = 200
               response["status_message"] = "success"
               return Response(data=response)

            final_translation = final_translation_function(input_sentence,target_language)

            response["final_translation"] = final_translation

            CachedData.objects.create(english_sentence=input_sentence.lower(),
                language_code=target_language,
                translation=final_translation)

            response["status"] = 200
            response["status_message"] = "success"

            print("Final response in translate api - particular %s", str(response))

        except Exception as e:
            print(str(e))
            response["error"] = str(e)

        return Response(data=response)



class TranslateBatchAPI(APIView):

    def post(self, request, *args, **kwargs):

        response = {"status": "500", "status_message": "Internal server Error"}


        try:

            request_data = request.data
            print(request_data)

            sentence_list = request_data["sentence_list"]

            final_translation_array = []

            for input_sentence_obj in sentence_list:
                print(input_sentence_obj)
                input_sentence = input_sentence_obj["input"]
                id_of_translation_word = input_sentence_obj["id_of_translation_word"]

                target_language = request_data["target_language"]

                if CachedData.objects.filter(english_sentence=input_sentence.lower(),language_code=target_language):

                   final_translation_array.append({"final_translation":CachedData.objects.filter(english_sentence=input_sentence.lower(),language_code=target_language)[0].translation,
                                                    "id_of_translation_word":id_of_translation_word})
                   continue

                final_translation = final_translation_function(input_sentence,target_language)

                final_translation_array.append({"final_translation":final_translation,
                                                    "id_of_translation_word":id_of_translation_word})

                CachedData.objects.create(english_sentence=input_sentence.lower(),
                        language_code=target_language,
                        translation=final_translation)

            response["sentence_list"] = final_translation_array
            response["status"] = 200
            response["status_message"] = "success"
            print("Final response in translate api - particular %s", str(response))

        except Exception as e:
            print(str(e))
            response["error"] = str(e)

        return Response(data=response)

TranslateParticularQuestion = TranslateParticularQuestionAPI.as_view()
TranslateBatch = TranslateBatchAPI.as_view()



def display_data(request, image_id):
    extracted_data = ExtractedData.objects.filter(uploaded_image_id=image_id)
    return render(request, 'myapp/display_data.html', {'extracted_data': extracted_data})



def sushi_test(request):
    extracted_data = CachedData.objects.filter(want_to_run_sushi_result=True)
    return render(request, 'myapp/sushi_test.html', {'extracted_data': extracted_data})
