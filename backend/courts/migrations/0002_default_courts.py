from datetime import time

from django.db import migrations


def defaults(apps, schema_editor):
    Area, Slot = apps.get_model('courts', 'Area'), apps.get_model('courts', 'Slot')
    for code, name, count, price in [('zijing', '紫荆网球场', 14, 15), ('beiguan', '北馆网球场', 4, 120)]:
        Area.objects.get_or_create(code=code, defaults={'name': name, 'court_count': count, 'reference_price': price})
    for hour in range(8, 22):
        Slot.objects.get_or_create(start=time(hour), defaults={'end': time(hour + 1)})


class Migration(migrations.Migration):
    dependencies = [('courts', '0001_initial')]
    operations = [migrations.RunPython(defaults, migrations.RunPython.noop)]
