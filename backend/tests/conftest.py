from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from app import models
from app.database import Base, SessionLocal, engine
from app.main import app
from app.seed import seed_database


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database(db)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    with SessionLocal() as db:
        yield db


def reference_id(model: type, field_name: str, value: str) -> int:
    with SessionLocal() as db:
        row = db.scalar(select(model).where(getattr(model, field_name) == value))
        assert row is not None
        id_columns = {
            models.User: "user_id",
            models.Category: "category_id",
            models.DatasetStatus: "status_id",
            models.AccessLevel: "access_level_id",
            models.DataSource: "source_id",
            models.License: "license_id",
        }
        return getattr(row, id_columns[model])


@pytest.fixture()
def create_version(client):
    def _create_version() -> dict:
        category_id = reference_id(models.Category, "category_name", "Статистические данные")
        user_id = reference_id(models.User, "email", "admin@example.com")
        dataset_response = client.post(
            "/datasets",
            json={
                "title": "Тестовый набор",
                "description": "Описание тестового набора",
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
                "change_note": "Первая версия",
            },
        )
        assert version_response.status_code == 201
        version = version_response.json()
        return {"dataset": dataset, "version": version, "user_id": user_id}

    return _create_version


@pytest.fixture()
def valid_csv_bytes() -> bytes:
    return (
        "region,agro_object,indicator,unit,period_year,value\n"
        "Краснодарский край,пшеница,урожайность,ц/га,2024,56.2\n"
    ).encode("utf-8")
