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
    hinglish = models.TextField(null=True, blank=True)
    gujarati_english = models.TextField(null=True, blank=True)
    marathi_english = models.TextField(null=True, blank=True)
    malayalam_english = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "ExtractedData"
        verbose_name_plural = "ExtractedData"

    def __str__(self):
        return self.extracted_data