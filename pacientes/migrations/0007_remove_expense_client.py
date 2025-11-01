from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pacientes', '0006_specialist_comp_type_specialist_comp_value_expense'),
    ]

    operations = [
        # Migración vacía - el campo client fue removido pero se restauró en 0009
        # Se deja vacía para mantener la secuencia de migraciones
    ]