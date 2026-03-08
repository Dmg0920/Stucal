import django.db.models.deletion
from django.db import migrations, models


def delete_orphan_rows(apps, schema_editor):
    Material = apps.get_model('core', 'Material')
    Session = apps.get_model('core', 'Session')
    Material.objects.filter(teacher__isnull=True).delete()
    Session.objects.filter(student__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_student_material_student_session_student_and_more'),
    ]

    operations = [
        migrations.RunPython(delete_orphan_rows, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='material',
            name='teacher',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='materials',
                to='core.teacherprofile',
                verbose_name='老師',
            ),
        ),
        migrations.AlterField(
            model_name='session',
            name='student',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='sessions',
                to='core.student',
                verbose_name='學生',
            ),
        ),
    ]
