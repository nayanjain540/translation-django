from google.cloud import translate_v3 as translate
from dotenv import load_dotenv
load_dotenv()


def translate_text(text, target_language):
    client = translate.TranslationServiceClient()
    parent = f"projects/bamboo-host-424020-c9/locations/global"

    response = client.translate_text(
        parent=parent,
        contents=[text],
        mime_type="text/plain",  # or "text/html"
        source_language_code="en",
        target_language_code=target_language,
        )
    
    return response.translations[0].translated_text

for i in range(0,10):
	translated_text = translate_text('Hello, world!', 'es')
	print(translated_text)

