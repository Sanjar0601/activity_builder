from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_submission_tab_lock_violations'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='score',
            field=models.PositiveIntegerField(default=0, verbose_name='Score'),
        ),
        migrations.AddField(
            model_name='submission',
            name='total_questions',
            field=models.PositiveIntegerField(default=0, verbose_name='Total Questions'),
        ),
    ]
