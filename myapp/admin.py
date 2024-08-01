from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(UploadedImage)
admin.site.register(ExtractedData)
admin.site.register(CachedData)
