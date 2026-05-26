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
