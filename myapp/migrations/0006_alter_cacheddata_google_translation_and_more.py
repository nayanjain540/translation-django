# Generated by Django 5.0.7 on 2024-08-02 06:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0005_cacheddata_want_to_run_sushi_result'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cacheddata',
            name='google_translation',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='cacheddata',
            name='sushi_test_result',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='cacheddata',
            name='translation',
            field=models.TextField(blank=True, default=''),
        ),
    ]
