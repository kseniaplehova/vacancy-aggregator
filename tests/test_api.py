import pytest
from rest_framework.test import APIClient

from apps.vacancies.models import Favorite, SavedSearch, Vacancy
from apps.vacancies.services.schemas import RawVacancy
from apps.vacancies.services.storage import deduplicate, save_vacancies

pytestmark = pytest.mark.django_db


def raw(source, source_id, title, company, **fields):
    return RawVacancy(
        source=source, source_id=source_id, url=f"https://{source}/{source_id}", title=title, company=company, **fields
    )


@pytest.fixture
def vacancies():
    save_vacancies(
        [
            raw("rabota.by", "1", "Python-разработчик", "ООО Авансум", city="Минск", salary="от 4 000 Br",
                description="Пишем сервисы на FastAPI. " * 30, detailed=True),
            raw("belmeta.com", "7", "Python-разработчик", "Авансум", city="Минск", origin="rabota.by"),
            raw("myjob.by", "2", "Аналитик продаж", "Аливария", city="Гомель", description="Отчёты в Excel"),
            raw("jobs.devby.io", "3", "Java developer", "АлюсофтБел"),
        ]
    )
    deduplicate()
    return {v.title: v for v in Vacancy.objects.filter(duplicate_of__isnull=True)}


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user("ksenia", "ksenia@example.org", "S3cure-passw0rd")


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def titles(response):
    return sorted(item["title"] for item in response.data["results"])


def test_list_hides_duplicates_and_shows_all_sources(client, vacancies):
    response = client.get("/api/v1/vacancies/")
    assert response.status_code == 200
    assert response.data["count"] == 3
    python = next(item for item in response.data["results"] if item["title"] == "Python-разработчик")
    assert python["sources"] == [
        {"source": "rabota.by", "url": "https://rabota.by/1"},
        {"source": "belmeta.com", "url": "https://belmeta.com/7"},
    ]
    assert python["is_favorite"] is False
    assert "description" not in python
    assert len(python["snippet"]) <= 301 and python["snippet"].endswith("…")


def test_detail_has_full_description(client, vacancies):
    response = client.get(f"/api/v1/vacancies/{vacancies['Python-разработчик'].pk}/")
    assert response.status_code == 200
    assert response.data["description"].startswith("Пишем сервисы на FastAPI.")


def test_duplicate_is_not_available_as_separate_vacancy(client, vacancies):
    copy = Vacancy.objects.get(source="belmeta.com")
    assert client.get(f"/api/v1/vacancies/{copy.pk}/").status_code == 404


@pytest.mark.parametrize(
    "params, expected",
    [
        ({"q": "аналитик"}, ["Аналитик продаж"]),
        ({"q": "PYTHON авансум"}, ["Python-разработчик"]),
        ({"q": "fastapi"}, ["Python-разработчик"]),
        ({"q": "бухгалтер"}, []),
        ({"city": "Гомель"}, ["Аналитик продаж"]),
        ({"source": "belmeta.com"}, ["Python-разработчик"]),
        ({"source": "rabota.by"}, ["Python-разработчик"]),
        ({"has_salary": "true"}, ["Python-разработчик"]),
        ({"has_salary": "false"}, ["Java developer", "Аналитик продаж"]),
        ({"q": "python", "city": "Гомель"}, []),
    ],
)
def test_filters(client, vacancies, params, expected):
    assert titles(client.get("/api/v1/vacancies/", params)) == expected


def test_filter_options(client, vacancies):
    data = client.get("/api/v1/filters/").data
    assert data["total"] == 3
    assert data["duplicates_merged"] == 1
    assert {"value": "Минск", "count": 1} in data["cities"]
    assert {option["value"] for option in data["sources"]} == {"rabota.by", "myjob.by", "jobs.devby.io"}


def test_registration_login_and_profile(client):
    payload = {"username": "ksenia", "email": "ksenia@example.org", "password": "S3cure-passw0rd"}
    assert client.post("/api/v1/auth/users/", payload).status_code == 201
    assert client.post("/api/v1/auth/users/", {**payload, "username": "other", "password": "12345"}).status_code == 400
    assert client.post("/api/v1/auth/users/", {**payload, "username": "other"}).status_code == 400

    tokens = client.post("/api/v1/auth/jwt/create/", {"username": "ksenia", "password": "S3cure-passw0rd"})
    assert tokens.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens.data['access']}")
    profile = client.get("/api/v1/auth/users/me/")
    assert profile.status_code == 200
    assert profile.data["username"] == "ksenia"
    assert "password" not in profile.data


def test_personal_endpoints_require_login(client, vacancies):
    pk = vacancies["Java developer"].pk
    assert client.post(f"/api/v1/vacancies/{pk}/favorite/").status_code == 401
    assert client.get("/api/v1/favorites/").status_code == 401
    assert client.get("/api/v1/searches/").status_code == 401


def test_favorites(auth_client, user, vacancies):
    pk = vacancies["Java developer"].pk
    assert auth_client.post(f"/api/v1/vacancies/{pk}/favorite/").status_code == 201
    assert auth_client.post(f"/api/v1/vacancies/{pk}/favorite/").status_code == 200
    assert Favorite.objects.filter(user=user).count() == 1

    assert titles(auth_client.get("/api/v1/favorites/")) == ["Java developer"]
    listed = auth_client.get("/api/v1/vacancies/", {"q": "java"}).data["results"][0]
    assert listed["is_favorite"] is True

    assert auth_client.delete(f"/api/v1/vacancies/{pk}/favorite/").status_code == 204
    assert auth_client.get("/api/v1/favorites/").data["count"] == 0


def test_saved_searches_belong_to_their_owner(auth_client, user, django_user_model):
    created = auth_client.post("/api/v1/searches/", {"name": "Python в Минске", "query": "python", "city": "Минск"})
    assert created.status_code == 201
    assert auth_client.post("/api/v1/searches/", {"name": "Пустой"}).status_code == 400

    stranger = django_user_model.objects.create_user("other", "other@example.org", "pass")
    foreign = SavedSearch.objects.create(user=stranger, name="Чужой", query="java")

    assert [item["name"] for item in auth_client.get("/api/v1/searches/").data] == ["Python в Минске"]
    assert auth_client.get(f"/api/v1/searches/{foreign.pk}/").status_code == 404
    assert auth_client.delete(f"/api/v1/searches/{foreign.pk}/").status_code == 404

    pk = created.data["id"]
    assert auth_client.patch(f"/api/v1/searches/{pk}/", {"city": "Гомель"}).data["city"] == "Гомель"
    assert auth_client.delete(f"/api/v1/searches/{pk}/").status_code == 204
    assert SavedSearch.objects.filter(user=user).count() == 0
