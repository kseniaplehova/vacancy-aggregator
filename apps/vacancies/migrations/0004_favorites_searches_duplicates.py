import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('vacancies', '0003_vacancy_detailed'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='vacancy',
            name='duplicate_of',
            field=models.ForeignKey(blank=True, help_text='Основная запись этой же вакансии из другого источника; пусто, если запись сама основная.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='duplicates', to='vacancies.vacancy', verbose_name='дубликат вакансии'),
        ),
        migrations.AddField(
            model_name='vacancy',
            name='search_text',
            field=models.TextField(blank=True, default='', editable=False, help_text='Название, компания и описание в нижнем регистре без знаков препинания.', verbose_name='текст для поиска'),
        ),
        migrations.CreateModel(
            name='SavedSearch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='название')),
                ('query', models.CharField(blank=True, max_length=200, verbose_name='слова для поиска')),
                ('city', models.CharField(blank=True, max_length=200, verbose_name='город')),
                ('source', models.CharField(blank=True, max_length=64, verbose_name='источник')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='создан')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='searches', to=settings.AUTH_USER_MODEL, verbose_name='пользователь')),
            ],
            options={
                'verbose_name': 'сохранённый поиск',
                'verbose_name_plural': 'сохранённые поиски',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='Favorite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='добавлена')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorites', to=settings.AUTH_USER_MODEL, verbose_name='пользователь')),
                ('vacancy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorites', to='vacancies.vacancy', verbose_name='вакансия')),
            ],
            options={
                'verbose_name': 'избранная вакансия',
                'verbose_name_plural': 'избранные вакансии',
                'ordering': ['-created'],
                'constraints': [models.UniqueConstraint(fields=('user', 'vacancy'), name='unique_favorite')],
            },
        ),
    ]
