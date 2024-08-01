from django.shortcuts import render
from openai import OpenAI
import base64

# Create your views here.
client = OpenAI(
  api_key="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",
)

# myapp/views.py
from django.shortcuts import render, redirect
from .forms import ImageUploadForm
from .models import UploadedImage, ExtractedData
import requests
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from .transliterate import *

import re

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

def translate(request, data_id):
    extracted_data = ExtractedData.objects.get(id=data_id)
    # Call your translation API
    response = requests.post('http://127.0.0.1:5000/predict', data=json.dumps({
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

                input_sentence = input_sentence.lower()

                for items in transliterated_terms:
                    input_sentence = input_sentence.lower().replace(items["term"].lower(), items[target_language])

                response_ai_4bharat = requests.post('http://127.0.0.1:5000/translate-to-particular-language', data=json.dumps({
                    "input": input_sentence,
                    "target_language": target_language
                }))

                print(response_ai_4bharat)
                translations = response_ai_4bharat.json()["translation"]
                print(translations)
                sending_for_refined_sentences = {}
                sending_for_refined_sentences["original_english_sentence"] = input_sentence
                sending_for_refined_sentences["translations"] = translations

                base_system_message = "Can you please check the translations provided and improve them wherever needed. Try to convert difficult words to easier words so that all type of readers of that language can understand it. STRICTLY follow the same JSON format in which the input is given."
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
                final_translation = extracted_text_content["translations"]

                # final_translation_json = {}

                # final_base_message = "BE VERY SMART ABOUT IT AND CONSIDER YOURSELF AN EXPERT TRANSLATOR.STEPS:" 
                # final_base_message += "\n 1. FOLLOW THIS INSTRUCTION PROPERLY : Do not translate bank names or shortforms or abbreviations like 'ID, RBL, CIF, PAN etc'"
                # final_base_message += "\n 2. FOLLOW THIS INSTRUCTION PROPERLY : Keep numbers in english only, do not translate them. "
                # final_base_message += "\n 3. TRANSLITERATE general banking terms and not translate them." 
                # final_base_message += "\n 4. It should be easy to understand for all type of malayalam speakers."
                # final_base_message += "\n 5. If the system is easy to understand then you don't update it,  however if there are tough words which you feel are better transliterated rather than translated please do it."
                # final_base_message += "\n 6. Simple non-financial terms should be translated to malayalam. "
                # final_base_message += "\n 7. Check the grammar once before giving the output and also check everything is in malayalam and NOT IN ENGLISH."


                # final_translation_json["original_english"] = input_sentence
                
                # if target_language == "hin_Deva":
                #     final_translation_json["pure_hindi"] = extracted_text_content["translations"]
                #     final_translation_json["easier_hindi_with_banking_terms"] = " "
                #     final_base_message = final_base_message.replace("malayalam", "hindi")

                # if target_language == "guj_Gujr":
                #     final_translation_json["pure_gujarati"] = extracted_text_content["translations"]
                #     final_translation_json["easier_gujarati_with_banking_terms"] = " "
                #     final_base_message = final_base_message.replace("malayalam", "gujarati")

                # if target_language == "mar_Deva":
                #     final_translation_json["pure_marathi"] = extracted_text_content["translations"]
                #     final_translation_json["easier_marathi_with_banking_terms"] = " "
                #     final_base_message = final_base_message.replace("malayalam", "marathi")

                # if target_language == "mal_Mlym":
                #     final_translation_json["pure_malayalam"] = extracted_text_content["translations"]
                #     final_translation_json["easier_malayalam_with_banking_terms"] = " "

                # print(final_translation_json)
                
                # response_ai_final = client.chat.completions.create(
                #                 model="gpt-4o",
                #                 response_format={"type": "json_object"},
                #                 messages=[
                #                         {
                #                           "role": "user",
                #                           "content": [
                #                             {"type": "text", "text": final_base_message},
                #                             {"type": "text", "text": f" : {final_translation_json}"},
                #                             {"type": "text", "text":"Please return in the following JSON format: {'original_english':'','final_translations':''}"}
                #                           ],
                #                         },
                #                       ],
                #                 max_tokens=4096,
                #                 )

                # extracted_text_content = json.loads(response_ai_final.choices[0].message.content)
                # print(extracted_text_content)

                #response["final_translation"] = extracted_text_content["final_translations"]
                # final_translation = extracted_text_content["final_translations"]

            else:

                hinglish_translation_json = {}
                hinglish_translation_json["original_english_sentence"] = input_sentence
                hinglish_translation_json[target_language] = ""
            
                if target_language == "hindi_english":
                    base_system_message = "Please translate this to the combination of the language given as key. For example hindi_english is a combination of hindi and english(but script in hindi) where the entire script is in hindi. I will give you an example: Mode of Registration in hindi-English is :रजिस्ट्रेशन का तरीका."

                elif target_language == "gujarati_english":
                    base_system_message = "Please translate this to the combination of the language given as key. For example gujarati_english is a combination of gujarati and english(but script in gujarati) where the entire script is in gujarati. I will give you an example: Mode of Registration in gujarati-English is :રજીસ્ટ્રેશનનો રીત."

                elif target_language == "marathi_english":
                    base_system_message = "Please translate this to the combination of the language given as key. For example marathi_english is a combination of marathi and english where the entire script(but script in marathi) is in marathi. I will give you an example: Mode of Registration in marathi-English is :रजिस्ट्रेशनचा मार्ग."

                elif target_language == "malayalam_english":
                    base_system_message = "Please translate this to the combination of the language given as key. For example malayalam_english is a combination of malayalam and english(but script in malayalam) where the entire script is in malayalam. I will give you an example: Mode of Registration in malayalam-English is :രജിസ്ട്രേഷന്റെ രീതി."

                response_ai = client.chat.completions.create(
                                model="gpt-4-turbo",
                                response_format={"type": "json_object"},
                                messages=[
                                        {
                                          "role": "user",
                                          "content": [
                                            {"type": "text", "text": base_system_message},
                                            {"type": "text", "text": "FOLLOW THIS INSTRUCTION PROPERLY : Do not translate shortforms and abbreviations like 'ID, RBL, CIF, PAN etc' "},
                                            {"type": "text", "text": "FOLLOW THIS INSTRUCTION PROPERLY : Keep numbers in english only, do not translate them. "},
                                            {"type": "text", "text": "Please follow the same JSON format in which the input is given."},
                                            {"type": "text", "text": f"{hinglish_translation_json}"}
                                          ],
                                        },
                                      ],
                                max_tokens=4096,
                                )

                extracted_text_content_hinglish = json.loads(response_ai.choices[0].message.content)
                final_translation = extracted_text_content_hinglish[target_language]
                
                if contains_english_characters(final_translation) == True:
                    response_ai = client.chat.completions.create(
                                model="gpt-4o",
                                response_format={"type": "json_object"},
                                messages=[
                                        {
                                          "role": "user",
                                          "content": [
                                            {"type": "text", "text": "The following translations has some english words, please TRANSLATE PROPERLY in the language..IT IS VERY IMPORTANT TO NOT HAVE ANY ENGLISH WORDS."},
                                            {"type": "text", "text": "FOLLOW THIS INSTRUCTION PROPERLY : Do not translate the following 'ID, RBL, CIF, PAN, NRI, ATM, IFSC, KYC, NEFT, RTGS, NPA, FD, OD, GST, FY, HUF,PAN, TAN, IMPS etc', translate the rest everything. "},
                                            {"type": "text", "text": "FOLLOW THIS INSTRUCTION PROPERLY : Keep numbers in english only, do not translate them. Translate everything else. "},
                                            {"type": "text", "text": "Please follow the same JSON format in which the input is given."},
                                            {"type": "text", "text": f"{extracted_text_content_hinglish}"}
                                          ],
                                        },
                                      ],
                                max_tokens=4096,
                                )
                    extracted_text_content_hinglish = json.loads(response_ai.choices[0].message.content)
                    final_translation = extracted_text_content_hinglish[target_language]
                    print("In second GPT call")
                    print(final_translation)

            response["final_translation"] = final_translation
            response["id_of_translation_word"] = id_of_translation_word
            response["status"] = 200
            response["status_message"] = "success"

        except Exception as e:
            print(str(e))

        return Response(data=response)

TranslateParticularQuestion = TranslateParticularQuestionAPI.as_view()
