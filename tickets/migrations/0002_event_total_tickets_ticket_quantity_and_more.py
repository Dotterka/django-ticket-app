# Generated by Django 4.1.13 on 2025-03-04 11:54

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='total_tickets',
            field=models.PositiveIntegerField(default=500),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='ticket',
            name='quantity',
            field=models.PositiveIntegerField(default=3, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='event',
            name='available_tickets',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
