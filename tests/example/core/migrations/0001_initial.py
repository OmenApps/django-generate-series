# Generated by Django 3.2.13 on 2022-04-26 18:32

import django.contrib.postgres.fields.ranges
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DateRangeTest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("term", django.contrib.postgres.fields.ranges.DateRangeField()),
            ],
            options={
                "abstract": False,
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="DateTest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("term", models.DateField()),
            ],
            options={
                "abstract": False,
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="DateTimeRangeTest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("term", django.contrib.postgres.fields.ranges.DateTimeRangeField()),
            ],
            options={
                "abstract": False,
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="DateTimeTest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("term", models.DateTimeField()),
            ],
            options={
                "abstract": False,
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="DecimalRangeTest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("term", django.contrib.postgres.fields.ranges.DecimalRangeField()),
            ],
            options={
                "abstract": False,
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="DecimalTest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("term", models.DecimalField(decimal_places=2, max_digits=9)),
            ],
            options={
                "abstract": False,
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="IntegerRangeTest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("term", django.contrib.postgres.fields.ranges.IntegerRangeField()),
            ],
            options={
                "abstract": False,
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="IntegerTest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("term", models.IntegerField()),
            ],
            options={
                "abstract": False,
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="ConcreteDateRangeTest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("some_field", django.contrib.postgres.fields.ranges.DateRangeField()),
            ],
        ),
        migrations.CreateModel(
            name="ConcreteDateTest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("some_field", models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name="ConcreteDateTimeRangeTest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("some_field", django.contrib.postgres.fields.ranges.DateTimeRangeField()),
            ],
        ),
        migrations.CreateModel(
            name="ConcreteDateTimeTest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("some_field", models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name="ConcreteDecimalRangeTest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("some_field", django.contrib.postgres.fields.ranges.DecimalRangeField()),
            ],
        ),
        migrations.CreateModel(
            name="ConcreteDecimalTest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("some_field", models.DecimalField(decimal_places=2, max_digits=9)),
            ],
        ),
        migrations.CreateModel(
            name="ConcreteIntegerRangeTest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("some_field", django.contrib.postgres.fields.ranges.IntegerRangeField()),
            ],
        ),
        migrations.CreateModel(
            name="ConcreteIntegerTest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("some_field", models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name="Event",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_datetime", models.DateTimeField()),
                ("ticket_qty", models.IntegerField()),
                ("false_field", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="SimpleOrder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order_date", models.DateField()),
                ("cost", models.IntegerField()),
            ],
        ),
    ]
