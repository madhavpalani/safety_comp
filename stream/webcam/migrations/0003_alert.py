# Generated by Django 4.2.5 on 2023-10-06 05:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webcam', '0002_employee1_supervisor_delete_employee'),
    ]

    operations = [
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
