# Generated by Django 2.2.16 on 2022-11-26 07:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_comment'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={},
        ),
        migrations.AlterField(
            model_name='comment',
            name='text',
            field=models.TextField(),
        ),
    ]
