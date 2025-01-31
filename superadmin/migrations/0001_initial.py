# Generated by Django 5.1 on 2024-10-31 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='APISettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('openai_api_key', models.CharField(blank=True, max_length=255, null=True)),
                ('pinecone_api_key', models.CharField(blank=True, max_length=255, null=True)),
                ('claude_api_key', models.CharField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
