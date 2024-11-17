# Generated by Django 5.1.2 on 2024-11-12 11:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pacientes', '0005_remove_session_is_reserved_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='session',
            name='status',
            field=models.CharField(choices=[('Activo', 'Activo'), ('Alta', 'Alta'), ('Suspendido', 'Suspendido')], default='Pending', help_text="Estado de la sesión: 'Pending', 'Completed' o 'Cancelled'.", max_length=10),
        ),
    ]