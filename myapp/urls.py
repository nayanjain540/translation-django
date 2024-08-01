# myapp/urls.py
from django.urls import path
from .views import upload_image, display_data, translate,TranslateParticularQuestion

urlpatterns = [
    path('upload/', upload_image, name='upload_image'),
    path('display/<int:image_id>/', display_data, name='display_data'),
    path('translate/<int:data_id>/', translate, name='translate'),
    path('translate-particular-sentence/', TranslateParticularQuestion, name='translate_particular_sentence')
]
