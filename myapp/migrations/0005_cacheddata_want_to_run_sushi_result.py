# Generated by Django 5.0.7 on 2024-08-02 00:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0004_cacheddata_google_translation_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cacheddata',
            name='want_to_run_sushi_result',
            field=models.BooleanField(default=False),
        ),
    ]
