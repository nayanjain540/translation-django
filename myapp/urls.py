# myapp/urls.py
from django.urls import path
from .views import upload_image, display_data, translate_api,TranslateParticularQuestion, TranslateBatch, sushi_test,sushi_test_api

urlpatterns = [
    path('upload/', upload_image, name='upload_image'),
    path('display/<int:image_id>/', display_data, name='display_data'),
    path('translate/<int:data_id>/', translate_api, name='translate'),
    path('translate-particular-sentence/', TranslateParticularQuestion, name='translate_particular_sentence'),
    path('translate-batch-api/', TranslateBatch, name='translate-batch-api'),
    path('adaptive_scoring_test/', sushi_test, name="sushi-test" ),
    path('sushi_testing_api/<int:data_id>/', sushi_test_api, name="sushi_testing_api")
]