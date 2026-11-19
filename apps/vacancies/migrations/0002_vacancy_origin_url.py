from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('vacancies', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='vacancy',
            name='origin_url',
            field=models.URLField(blank=True, help_text='Адрес этой же вакансии на площадке-первоисточнике.', max_length=500, null=True, verbose_name='ссылка на первоисточник'),
        ),
    ]
