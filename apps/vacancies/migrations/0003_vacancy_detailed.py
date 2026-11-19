from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('vacancies', '0002_vacancy_origin_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='vacancy',
            name='detailed',
            field=models.BooleanField(default=False, help_text='Страница вакансии загружена; иначе в описании только фрагмент из списка.', verbose_name='описание полное'),
        ),
    ]
