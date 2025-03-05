# Generated by Django 4.1.13 on 2025-03-05 08:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0003_order_expires_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='currency',
            field=models.CharField(default='HUF', max_length=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='event',
            name='ticket_price',
            field=models.DecimalField(decimal_places=2, default=6000, max_digits=15),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='currency',
            field=models.CharField(default='HUF', max_length=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='total_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True),
        ),
    ]
