from django.shortcuts import render
from openai import OpenAI
import base64
import os
# Create your views here.
#api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key="")

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
    # Call your translation API
    response = requests.post('http://3.222.84.147:5000/predict', data=json.dumps({
        "input": extracted_data.extracted_data
    }))
    translations = response.json()
    print(translations)
    
    sending_for_refined_sentences = {}
    sending_for_refined_sentences["original_english_sentence"] = extracted_data.extracted_data
    sending_for_refined_sentences["translations"] = translations

    print(sending_for_refined_sentences)
    base_system_message = "Can you please check the translations provided and improve them wherever needed. STRICTLY follow the same JSON format in which the input is given."


    response = client.chat.completions.create(
                    model="gpt-4o",
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

    extracted_text_content = json.loads(response.choices[0].message.content)

    hinglish_translation_json = {}
    hinglish_translation_json["original_english_sentence"] = extracted_data.extracted_data
    hinglish_translation_json["translations"] = {"hindi_english":"","gujarati_english":"","marathi_english": "","malayalam_english":""}
    
    
    base_system_message = "Please translate this to the combination of the language given as key. For example hindi_english is a combination of hindi and english.I will give you an example: Mode of Registration in hindi-English is :रजिस्ट्रेशन का तरीका. Similarly gujarati_english is gujarati and english. Mode of Registration in gujarati-English is :રજીસ્ટ્રેશનનો રીત.  Please follow the same JSON format in which the input is given."

    response = client.chat.completions.create(
                    model="gpt-4o",
                    response_format={"type": "json_object"},
                    messages=[
                            {
                              "role": "user",
                              "content": [
                                {"type": "text", "text": base_system_message},
                                {"type": "text", "text": "FOLLOW THIS INSTRUCTION PROPERLY : Do not translate shortforms and abbreviations like 'ID, RBL, CIF, PAN etc' "},
                                {"type": "text", "text": f"{hinglish_translation_json}"}
                              ],
                            },
                          ],
                    max_tokens=4096,
                    )

    extracted_text_content_hinglish = json.loads(response.choices[0].message.content)

    print(extracted_text_content)
    print(extracted_text_content_hinglish)

    try:
        extracted_data.hindi = extracted_text_content["hin_Deva"]
        extracted_data.gujarati = extracted_text_content["guj_Gujr"]
        extracted_data.marathi = extracted_text_content["mar_Deva"]
        extracted_data.malayalam = extracted_text_content["mal_Mlym"]
        extracted_data.hinglish = extracted_text_content_hinglish["hindi_english"]
        extracted_data.gujarati_english = extracted_text_content_hinglish["gujarati_english"]
        extracted_data.marathi_english = extracted_text_content_hinglish["marathi_english"]
        extracted_data.malayalam_english = extracted_text_content_hinglish["malayalam_english"]
        extracted_data.save()
    
    except Exception as e:
        extracted_data.hindi = extracted_text_content["translations"]["hin_Deva"]
        extracted_data.gujarati = extracted_text_content["translations"]["guj_Gujr"]
        extracted_data.marathi = extracted_text_content["translations"]["mar_Deva"]
        extracted_data.malayalam = extracted_text_content["translations"]["mal_Mlym"]
        extracted_data.hinglish = extracted_text_content_hinglish["translations"]["hindi_english"]
        extracted_data.gujarati_english = extracted_text_content_hinglish["translations"]["gujarati_english"]
        extracted_data.marathi_english = extracted_text_content_hinglish["translations"]["marathi_english"]
        extracted_data.malayalam_english = extracted_text_content_hinglish["translations"]["malayalam_english"]
        extracted_data.save()

    

    # extracted_data = ExtractedData.objects.filter(uploaded_image_id=extracted_data.uploaded_image.pk)
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

class TranslateParticularQuestionAPI(APIView):

    def post(self, request, *args, **kwargs):

        response = {"status": "500", "status_message": "Internal server Error"}

        #["hin_Deva", "guj_Gujr", "mar_Deva", "mal_Mlym"]
        #["hindi_english", "gujarati_english", "marathi_english", "malayalam_english"]

        try:

            request_data = request.data

            id_of_translation_word = request_data.get("id_of_translation_word","")

            input_sentence = request_data["input"]

            target_language = request_data["target_language"]

            if target_language in ["hin_Deva", "guj_Gujr", "mar_Deva", "mal_Mlym"]:

                original_sentence = input_sentence.lower()

                input_sentence = input_sentence.lower()

                if CachedData.objects.filter(english_sentence=original_sentence,language_code=target_language):
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
                
                translations_google = translate_text(input_sentence_updated, target_language_dict[target_language]).translated_text
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

            response["final_translation"] = final_translation

            CachedData.objects.create(english_sentence=original_sentence,
                language_code=target_language,
                translation=final_translation)

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
                    
                    translations_google = translate_text(input_sentence_updated, target_language_dict[target_language]).translated_text

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
