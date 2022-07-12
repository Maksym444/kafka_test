# Generated by Django 4.0.6 on 2022-07-09 07:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_update', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.TextField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_update', models.DateTimeField(auto_now=True, null=True)),
                ('enabled', models.BooleanField()),
                ('title', models.TextField(blank=True, null=True)),
                ('url', models.TextField()),
                ('channel_id', models.TextField(db_index=True)),
                ('last_parsed', models.DateTimeField(null=True)),
                ('last_message_id', models.IntegerField(default=0)),
                ('source', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='producer.source')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
