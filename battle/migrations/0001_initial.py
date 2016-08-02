# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Battle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('battle_name', models.CharField(max_length=100)),
                ('hashtag1', models.CharField(max_length=500)),
                ('hashtag1_typos', models.CharField(null=True, max_length=100, blank=True)),
                ('hashtag2', models.CharField(max_length=500)),
                ('hashtag2_typos', models.CharField(null=True, max_length=100, blank=True)),
                ('started_at', models.CharField(max_length=100)),
                ('ended_at', models.CharField(max_length=100)),
                ('winner', models.CharField(null=True, max_length=500, blank=True)),
                ('status', models.CharField(max_length=100)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['user', 'battle_name'],
            },
        )
    ]