# myapp/models.py
from django.db import models

class UploadedImage(models.Model):
    image = models.ImageField(upload_to='uploads/')
    created_at = models.DateTimeField(auto_now_add=True)

class ExtractedData(models.Model):
    uploaded_image = models.ForeignKey(UploadedImage, on_delete=models.CASCADE)
    extracted_data = models.TextField(default = [])
    hindi = models.TextField(null=True, blank=True)
    gujarati = models.TextField(null=True, blank=True)
    marathi = models.TextField(null=True, blank=True)
    malayalam = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "ExtractedData"
        verbose_name_plural = "ExtractedData"

    def __str__(self):
        return self.extracted_data

class CachedData(models.Model):
    english_sentence = models.TextField(default = "", null=True, blank=True)
    language_code = models.TextField(default = "", null=True, blank=True)
    translation = models.TextField(default = "", null=True, blank=True)

    google_translation = models.TextField(default= "", null=True, blank=True)
    sushi_test_result = models.TextField(default= "", null=True, blank=True)

    want_to_run_sushi_result = models.BooleanField(default = False)

    class Meta:
        verbose_name = "CachedData"
        verbose_name_plural = "CachedData"

    def __str__(self):
        return "Sentence-" + self.english_sentence + " language_code-" + self.language_code
