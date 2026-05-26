from __future__ import annotations

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def _get_or_create(db: Session, model: type, lookup: dict, defaults: dict | None = None):
    instance = db.scalar(select(model).filter_by(**lookup))
    if instance:
        return instance
    values = {**lookup, **(defaults or {})}
    instance = model(**values)
    db.add(instance)
    db.flush()
    return instance


def seed_database(db: Session) -> None:
    roles = {
        "admin": "Администратор MVP",
        "user": "Пользователь репозитория",
        "moderator": "Модератор наборов данных",
    }
    role_objects = {
        name: _get_or_create(db, models.Role, {"role_name": name}, {"description": description})
        for name, description in roles.items()
    }

    for name, description in {
        "public": "Открытые данные",
        "registered": "Доступ после входа в систему",
        "restricted": "Ограниченный доступ",
        "private": "Приватный набор данных",
    }.items():
        _get_or_create(db, models.AccessLevel, {"access_level_name": name}, {"description": description})

    for name, description in {
        "Статистические данные": "Структурированные показатели сельского хозяйства",
        "Метеорологические данные": "Погодные и климатические наблюдения",
        "Геопространственные данные": "Данные с пространственной привязкой",
        "Справочные данные": "Классификаторы и нормативно-справочная информация",
    }.items():
        _get_or_create(db, models.Category, {"category_name": name}, {"description": description})

    for name, mime_type in {
        "CSV": "text/csv",
        "XLSX": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "JSON": "application/json",
        "GeoJSON": "application/geo+json",
    }.items():
        _get_or_create(db, models.DataFormat, {"format_name": name}, {"mime_type": mime_type})

    for name, description in {
        "CC BY 4.0": "Creative Commons Attribution 4.0",
        "CC0": "Public Domain Dedication",
        "Пользовательская лицензия": "Условия определяются владельцем данных",
    }.items():
        _get_or_create(db, models.License, {"license_name": name}, {"description": description})

    for name, code in {
        "Краснодарский край": "23",
        "Республика Татарстан": "16",
        "Московская область": "50",
    }.items():
        _get_or_create(db, models.Region, {"region_name": name}, {"region_code": code})

    for name, object_type, description in [
        ("пшеница", "crop", "Зерновая культура"),
        ("картофель", "crop", "Сельскохозяйственная культура"),
        ("молоко", "product", "Продукция животноводства"),
        ("КРС", "animal", "Крупный рогатый скот"),
        ("пашня", "land", "Сельскохозяйственные земли"),
    ]:
        _get_or_create(
            db,
            models.AgroObject,
            {"object_name": name},
            {"object_type": object_type, "description": description},
        )

    for name, description in {
        "урожайность": "Объем продукции с единицы площади",
        "посевная площадь": "Площадь посевов",
        "производство": "Общий объем производства",
        "осадки": "Количество атмосферных осадков",
        "температура": "Температура воздуха",
    }.items():
        _get_or_create(db, models.Indicator, {"indicator_name": name}, {"description": description})

    for unit_name, unit_symbol in {
        "центнер с гектара": "ц/га",
        "гектар": "га",
        "тонна": "т",
        "миллиметр": "мм",
        "градус Цельсия": "°C",
    }.items():
        _get_or_create(db, models.MeasurementUnit, {"unit_symbol": unit_symbol}, {"unit_name": unit_name})

    for name, description in {
        "draft": "Черновик версии",
        "uploaded": "Файл загружен",
        "validation_failed": "Проверка завершилась с ошибками",
        "on_moderation": "Версия находится на модерации",
        "published": "Опубликованная версия",
        "rejected": "Версия отклонена",
        "archived": "Архивная версия",
    }.items():
        _get_or_create(db, models.DatasetStatus, {"status_name": name}, {"description": description})

    for name, url, source_type, description in [
        ("ЕМИСС", "https://fedstat.ru", "official_statistics", "Единая межведомственная информационно-статистическая система"),
        ("FAOSTAT", "https://www.fao.org/faostat", "international_statistics", "Статистическая база FAO"),
        ("Росстат", "https://rosstat.gov.ru", "official_statistics", "Федеральная служба государственной статистики"),
        ("OpenWeather", "https://openweathermap.org", "weather_api", "Источник погодных данных"),
        ("Пользовательская загрузка", None, "user_upload", "Данные, загруженные пользователем"),
    ]:
        _get_or_create(
            db,
            models.DataSource,
            {"source_name": name},
            {"source_url": url, "source_type": source_type, "description": description},
        )

    demo_users = [
        ("Администратор", "admin@example.com", "admin123", "Демо-организация", ["admin", "moderator", "user"]),
        ("Пользователь", "user@example.com", "user123", "Демо-организация", ["user"]),
        ("Модератор", "moderator@example.com", "moderator123", "Демо-организация", ["moderator", "user"]),
    ]

    for full_name, email, password, organization, user_roles in demo_users:
        user = db.scalar(select(models.User).where(models.User.email == email))
        if not user:
            user = models.User(
                full_name=full_name,
                email=email,
                password_hash=hash_password(password),
                organization=organization,
                is_active=True,
            )
            db.add(user)
            db.flush()
        for role_name in user_roles:
            role = role_objects[role_name]
            _get_or_create(db, models.UserRole, {"user_id": user.user_id, "role_id": role.role_id})

    db.commit()
