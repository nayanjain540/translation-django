from django.shortcuts import render
from openai import OpenAI
import base64
import os
# Create your views here.
#api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key="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")

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


def contains_english_characters(text):
    # Regular expression pattern to match English alphabets (both uppercase and lowercase)
    pattern = re.compile(r'[a-zA-Z]')
    return bool(pattern.search(text))

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def upload_image(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_image = form.save()
            # Call your internal API to extract data
            print(uploaded_image.image)
            image_path = "/Users/nayanjain/translation/" + str(uploaded_image.image) 

            encoded_image = encode_image(image_path)
            base_system_message = "Please give me the content in the screen which you think should be translated to other languages. Don't give all content, content where sentiment will be changed if translated to english, don't give me that content.  For example 'apno ka bank' should not be extracted. Extract only such data. Return in JSON format where all extracted text is value of the main key as array.Main key is 'extracted_text'"


            response = client.chat.completions.create(
                        model="gpt-4o",
                        response_format={"type": "json_object"},
                        messages=[
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
                        
                      ],
                        max_tokens=4096,
                        )
            extracted_text_content = json.loads(response.choices[0].message.content)["extracted_text"]

            for items in extracted_text_content:
                ExtractedData.objects.create(
                    uploaded_image=UploadedImage.objects.get(pk=uploaded_image.id),
                    extracted_data = items
                )
            return redirect('display_data', uploaded_image.id)
    else:
        form = ImageUploadForm()
    return render(request, 'myapp/upload_image.html', {'form': form})

def display_data(request, image_id):
    extracted_data = ExtractedData.objects.filter(uploaded_image_id=image_id)
    return render(request, 'myapp/display_data.html', {'extracted_data': extracted_data})




def translate_api(request, data_id):
    extracted_data = ExtractedData.objects.get(id=data_id)
    
    languages_list = ["hin_Deva", "guj_Gujr", "mar_Deva", "mal_Mlym"]
    for items in languages_list:

        url = "http://127.0.0.1:8000/myapp/translate-particular-sentence/"

        payload = json.dumps({
          "input": extracted_data.extracted_data,
          "target_language": items
        })
        headers = {
          'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        final_translation = json.loads(response.text)["final_translation"]

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

def translate_text(text: str, target_language_code: str):
    PROJECT_ID = environ.get("PROJECT_ID", "")
    PARENT = f"projects/{PROJECT_ID}"
    print(PARENT)
    client = translate.TranslationServiceClient()

    response = client.translate_text(
        parent="projects/astrico-translation",
        contents=[text],
        source_language_code= "en",
        target_language_code=target_language_code,
    )
    print(response.translations[0])
    return response.translations[0]

def translate_google_api(text: str, target_language_code: str):
    import requests
    import json

    url = "http://3.108.207.239:8000/myapp/google-translate-api/"

    payload = json.dumps({
      "input": text,
      "target_language": target_language_code
    })
    headers = {
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    translations_google = json.loads(response.text)["translations_google"]

    return translations_google

def translate_to_english(text: str, source_language_code: str):
    import requests
    import json

    url = "http://3.108.207.239:8000/myapp/google-translate-api/"

    payload = json.dumps({
      "input": text,
      "target_language": "en",
      "source_language_code":source_language_code
    })
    headers = {
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    translations_google = json.loads(response.text)["translations_google"]

    return translations_google


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

        google_translation = translate_to_english(text = cached_data.translation,
                                                    source_language_code=source_language_code)

        cached_data.google_translation = google_translation
        print("google translation", google_translation)
        cached_data.save()

        json_for_translation = {'original_text':cached_data.english_sentence, 'translated_english_text':google_translation}
        base_system_message = str(json_for_translation)
        base_system_message += '''
        The Sushi Test is used to compare translated texts with the original text. The goal is to determine how accurately the key details, phrase structure, article usage, and tonality are preserved in the translation. The test is divided into four main parameters, each with a specified weightage:
        Key Details: This parameter assesses whether the essential information from the original text is retained in the translation. All significant facts and figures should be correctly translated.
        Phrase Structure: This evaluates whether the grammatical structure of phrases in the translation matches that of the original text. It specifically focuses on the proper use of conjunctions, verbs, and adverbs. If there are minor issues with conjunctions or verb usage, this can affect the readability but should not drastically alter the meaning. Capitalization should not have a big impact.
        Article Usage: This checks if articles (e.g., "a," "the") are used correctly in the translation. The correct use of articles is crucial for the clarity of the text. If the original text does not use articles or if article usage is not applicable (due to differences in languages), this parameter may receive a full score of 100%.
        Tonality: This evaluates whether the tone of the translation matches that of the original text. The tone should be consistent, whether formal, informal, or neutral.
        Scoring Method:
        For each parameter, scores are assigned based on how well the translation matches the original text.
        Each parameter will get a score out of 100
        If a parameter is not applicable due to differences between languages or contexts (e.g., article usage in a language where articles are not used), it will receive a full score of 100%.
        
        Return the following JSON: {‘key_details’: ‘’, ‘phrase_structure’:’’,’article_usage’:’’, ‘tonality’:’’}'''


        response_ai = client.chat.completions.create(
                                    model="gpt-4-turbo",
                                    response_format={"type": "json_object"},
                                    messages=[
                                            {
                                              "role": "user",
                                              "content": [
                                                {"type": "text", "text": base_system_message},
                                              ],
                                            },
                                          ],
                                    max_tokens=4096,
                                    )

        extracted_text_content = json.loads(response_ai.choices[0].message.content)

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

        #["hin_Deva", "guj_Gujr", "mar_Deva", "mal_Mlym"]
        #["hindi_english", "gujarati_english", "marathi_english", "malayalam_english"]

        try:

            start_time = datetime.datetime.now()

            request_data = request.data

            id_of_translation_word = request_data.get("id_of_translation_word","")

            input_sentence = request_data["input"]

            target_language = request_data["target_language"]

            if target_language in ["hin_Deva", "guj_Gujr", "mar_Deva", "mal_Mlym"]:

                original_sentence = input_sentence.lower()

                input_sentence = input_sentence.lower()

                if CachedData.objects.filter(english_sentence=original_sentence,language_code=target_language):

                   time.sleep(1)

                   response["final_translation"] = CachedData.objects.filter(english_sentence=original_sentence,language_code=target_language)[0].translation
                   response["id_of_translation_word"] = id_of_translation_word
                   response["status"] = 200
                   response["status_message"] = "success"
                   return Response(data=response)

                do_not_translate_words = []

                for items in transliterated_terms:
                    if items["term"].lower() in input_sentence.lower():
                        input_sentence = input_sentence.lower().replace(items["term"].lower(), items[target_language])
                        do_not_translate_words.append(items[target_language])

                input_sentence_updated = input_sentence

                input_sentence = original_sentence
                
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
                
                translations_google = translate_google_api(input_sentence_updated, target_language_dict[target_language])
                sending_for_refined_sentences = {}

                sending_for_refined_sentences["original_english_sentence"] = input_sentence_updated
                sending_for_refined_sentences["translations"] = translations_google

                print(sending_for_refined_sentences)

                base_system_message = f"I need you to be a {language_dictionary[target_language]} BANK translator for common people, I will give you a sentence, you need to give me a sentence which is much more readable and understandable to the common man. DONT CHANGE THE CONTEXT, MEANING, TONE."
                
                input_sentence_updated_arr = input_sentence_updated.split(" ")
                if len(input_sentence_updated_arr) <= 3:
                    base_system_message = f"I need you to be a {language_dictionary[target_language]} BANK translator. you are a translator. "
                    base_system_message += "you are translating a banking app into regional languages. You job is make sure that the UI of the app is not affected because of the translations. For instance 'accounts' when translated in hindi would mean 'हिसाब किताब' but since you are a banking app translator, you will keep it 'खाते'. Since app has limited space in terms of UI, we will keep it simple. You can even transliterate them for the common people. For example 'statement' can become 'स्टेटमेंट'. This will ensure that the translations are not very complex"
                    sending_for_refined_sentences["translations"] = " "
                
                if len(do_not_translate_words) != 0:
                    base_system_message += f"\n Do not try to change or update the words in the given array: {do_not_translate_words}"              
                

                base_system_message += "STRICTLY follow the same JSON format in which the input is given."
                base_system_message += "Return this JSON only: {'translations':''}"
                base_system_message += "\n IF THE ORIGINAL ENGLISH SENTENCE IS FEW WORDS, the translation should also be equally small."
                base_system_message += "\n 1. FOLLOW THIS INSTRUCTION PROPERLY : If there are abbreviations present in the original english sentence, and if they have been translated, bring them back in english language."
                base_system_message += "\n 2. FOLLOW THIS INSTRUCTION PROPERLY : Keep numbers in english only, do not translate them. "
                

                response_ai = client.chat.completions.create(
                                model="gpt-4-turbo",
                                response_format={"type": "json_object"},
                                messages=[
                                        {
                                          "role": "user",
                                          "content": [
                                            {"type": "text", "text": base_system_message},
                                            {"type": "text", "text": f"{sending_for_refined_sentences}"}
                                          ],
                                        },
                                      ],
                                max_tokens=4096,
                                )

                extracted_text_content = json.loads(response_ai.choices[0].message.content)
                print(extracted_text_content)

                try:
                   final_translation = extracted_text_content["translations"]
                except Exception as e:
                   final_translation = extracted_text_content["corrected_translation"]


            if final_translation == "":
                final_translation = translations_google
            response["final_translation"] = final_translation



            CachedData.objects.create(english_sentence=original_sentence,
                language_code=target_language,
                translation=final_translation)

            time.sleep(1)

            response["id_of_translation_word"] = id_of_translation_word
            response["status"] = 200
            response["status_message"] = "success"

        except Exception as e:
            print(str(e))
            response["error"] = str(e)

        return Response(data=response)

TranslateParticularQuestion = TranslateParticularQuestionAPI.as_view()


class TranslateBatchAPI(APIView):

    def post(self, request, *args, **kwargs):

        response = {"status": "500", "status_message": "Internal server Error"}

        #["hin_Deva", "guj_Gujr", "mar_Deva", "mal_Mlym"]
        #["hindi_english", "gujarati_english", "marathi_english", "malayalam_english"]

        try:

            request_data = request.data
            print(request_data)

            sentence_list = request_data["sentence_list"]

            final_translation_array = []

            for input_sentence_obj in sentence_list:

                input_sentence = input_sentence_obj["input"].lower()
                id_of_translation_word = input_sentence_obj["id_of_translation_word"]

                target_language = request_data["target_language"]

                if target_language in ["hin_Deva", "guj_Gujr", "mar_Deva", "mal_Mlym"]:

                    original_sentence = input_sentence.lower()

                    input_sentence = input_sentence.lower()

                    if CachedData.objects.filter(english_sentence=original_sentence,language_code=target_language):

                       final_translation_array.append({"final_translation":CachedData.objects.filter(english_sentence=original_sentence,language_code=target_language)[0].translation,
                                                        "id_of_translation_word":id_of_translation_word})
                       continue


                    do_not_translate_words = []

                    for items in transliterated_terms:
                        if items["term"].lower() in input_sentence.lower():
                            input_sentence = input_sentence.lower().replace(items["term"].lower(), items[target_language])
                            do_not_translate_words.append(items[target_language])

                    input_sentence_updated = input_sentence
                    

                    input_sentence = original_sentence

                    
                    sending_for_refined_sentences = {}
                    sending_for_refined_sentences["original_english_sentence"] = input_sentence_updated


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
                    
                    translations_google = translate_google_api(input_sentence_updated, target_language_dict[target_language])

                    sending_for_refined_sentences = {}
                    sending_for_refined_sentences["original_english_sentence"] = input_sentence_updated
                    sending_for_refined_sentences["translations"] = translations_google

                    base_system_message = f"I need you to be a {language_dictionary[target_language]} BANK translator for common people, I will give you a sentence, you need to give me a sentence which is much more readable and understandable to the common man. DONT CHANGE THE CONTEXT, MEANING, TONE."
                   
                    input_sentence_updated_arr = input_sentence_updated.split(" ")

                    if len(input_sentence_updated_arr) <= 3:
                        base_system_message = f"I need you to be a {language_dictionary[target_language]} BANK translator. you are a translator. "
                        base_system_message += "you are translating a banking app into regional languages. You job is make sure that the UI of the app is not affected because of the translations. For instance 'accounts' when translated in hindi would mean 'हिसाब किताब' but since you are a banking app translator, you will keep it 'खाते'. Since app has limited space in terms of UI, we will keep it simple. You can even transliterate them for the common people. For example 'statement' can become 'स्टेटमेंट'. This will ensure that the translations are not very complex"
                        sending_for_refined_sentences["translations"] = " "
                    
                    if len(do_not_translate_words) != 0:
                        base_system_message += f"\n Do not try to change or update the words in the given array: {do_not_translate_words}"              
                
                    base_system_message += "STRICTLY follow the same JSON format in which the input is given."
                    base_system_message += "Return this JSON only: {'translations':''}"
                    base_system_message += "\n IF THE ORIGINAL ENGLISH SENTENCE IS FEW WORDS, the translation should also be equally small."
                    base_system_message += "\n 1. FOLLOW THIS INSTRUCTION PROPERLY : If there are abbreviations present in the original english sentence, and if they have been translated, bring them back in english language."
                    base_system_message += "\n 2. FOLLOW THIS INSTRUCTION PROPERLY : Keep numbers in english only, do not translate them. "
                    print(base_system_message)
                    print(sending_for_refined_sentences)
                    response_ai = client.chat.completions.create(
                                    model="gpt-4-turbo",
                                    response_format={"type": "json_object"},
                                    messages=[
                                            {
                                              "role": "user",
                                              "content": [
                                                {"type": "text", "text": base_system_message},
                                                {"type": "text", "text": f"{sending_for_refined_sentences}"}
                                              ],
                                            },
                                          ],
                                    max_tokens=4096,
                                    )

                    extracted_text_content = json.loads(response_ai.choices[0].message.content)
                    print(extracted_text_content)

                    try:
                       final_translation = extracted_text_content["translations"]
                    except Exception as e:
                       final_translation = extracted_text_content["corrected_translation"]

                    if final_translation == "":
                        final_translation = translations_google
                    final_translation_array.append({"final_translation":final_translation,
                                                        "id_of_translation_word":id_of_translation_word})

                    CachedData.objects.create(english_sentence=original_sentence,
                            language_code=target_language,
                            translation=final_translation)

            response["sentence_list"] = final_translation_array
            response["status"] = 200
            response["status_message"] = "success"

        except Exception as e:
            print(str(e))
            response["error"] = str(e)

        return Response(data=response)

TranslateBatch = TranslateBatchAPI.as_view()



def sushi_test(request):
    extracted_data = CachedData.objects.filter(want_to_run_sushi_result=True)
    return render(request, 'myapp/sushi_test.html', {'extracted_data': extracted_data})
