from app import models
from conftest import reference_id


def test_can_create_dataset_version_and_metadata(client):
    category_id = reference_id(models.Category, "category_name", "Статистические данные")
    user_id = reference_id(models.User, "email", "admin@example.com")

    dataset_response = client.post(
        "/datasets",
        json={
            "title": "Урожайность зерновых",
            "description": "Демонстрационный набор для ВКР",
            "category_id": category_id,
            "created_by": user_id,
        },
    )
    assert dataset_response.status_code == 201
    dataset = dataset_response.json()

    status_id = reference_id(models.DatasetStatus, "status_name", "draft")
    access_level_id = reference_id(models.AccessLevel, "access_level_name", "public")
    source_id = reference_id(models.DataSource, "source_name", "Пользовательская загрузка")

    version_response = client.post(
        f"/datasets/{dataset['dataset_id']}/versions",
        json={
            "version_number": "1.0",
            "status_id": status_id,
            "access_level_id": access_level_id,
            "source_id": source_id,
            "change_note": "Первичная загрузка",
        },
    )
    assert version_response.status_code == 201
    version = version_response.json()

    license_id = reference_id(models.License, "license_name", "CC BY 4.0")
    metadata_response = client.post(
        f"/versions/{version['version_id']}/metadata",
        json={
            "annotation": "Набор содержит показатели урожайности.",
            "methodology": "Данные собраны из демонстрационного CSV.",
            "temporal_coverage": "2024",
            "spatial_coverage": "Россия",
            "license_id": license_id,
            "quality_note": "MVP-проверка",
            "citation": "Repository MVP, 2026",
        },
    )
    assert metadata_response.status_code == 200
    metadata = metadata_response.json()
    assert metadata["version_id"] == version["version_id"]


def test_can_switch_current_dataset_version(client):
    created = client.post(
        "/datasets",
        json={
            "title": "Версионируемый набор",
            "description": "Проверка переключения текущей версии",
            "category_id": reference_id(models.Category, "category_name", "Статистические данные"),
            "created_by": reference_id(models.User, "email", "admin@example.com"),
        },
    ).json()
    status_id = reference_id(models.DatasetStatus, "status_name", "draft")
    access_level_id = reference_id(models.AccessLevel, "access_level_name", "public")
    source_id = reference_id(models.DataSource, "source_name", "Пользовательская загрузка")

    version_1_response = client.post(
        f"/datasets/{created['dataset_id']}/versions",
        json={
            "version_number": "1.0",
            "status_id": status_id,
            "access_level_id": access_level_id,
            "source_id": source_id,
        },
    )
    assert version_1_response.status_code == 201
    version_1 = version_1_response.json()

    version_2_response = client.post(
        f"/datasets/{created['dataset_id']}/versions",
        json={
            "version_number": "2.0",
            "status_id": status_id,
            "access_level_id": access_level_id,
            "source_id": source_id,
        },
    )
    assert version_2_response.status_code == 201
    version_2 = version_2_response.json()
    assert version_2["is_current"] is True

    switch_response = client.post(f"/versions/{version_1['version_id']}/make-current")
    assert switch_response.status_code == 200
    assert switch_response.json()["is_current"] is True

    detail_response = client.get(f"/datasets/{created['dataset_id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["current_version"]["version_id"] == version_1["version_id"]
    assert {item["version_number"] for item in detail["versions"]} == {"1.0", "2.0"}
    assert [item for item in detail["versions"] if item["is_current"]][0]["version_id"] == version_1["version_id"]
