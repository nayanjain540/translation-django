# Generated by Django 5.0.7 on 2024-08-05 21:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0006_alter_cacheddata_google_translation_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='extracteddata',
            name='gujarati_english',
        ),
        migrations.RemoveField(
            model_name='extracteddata',
            name='hinglish',
        ),
        migrations.RemoveField(
            model_name='extracteddata',
            name='malayalam_english',
        ),
        migrations.RemoveField(
            model_name='extracteddata',
            name='marathi_english',
        ),
    ]
