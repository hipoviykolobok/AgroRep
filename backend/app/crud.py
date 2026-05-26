from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
from fastapi import UploadFile
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.orm import Session, selectinload

from app import models, schemas
from app.seed import verify_password
from app.validators import (
    FileValidationErrorItem,
    ensure_storage_dir,
    infer_format_name,
    normalize_observation_frame,
    read_observation_file,
    save_upload_file,
    storage_uri_to_path,
    validate_observation_file,
)


def get_by_id(db: Session, model: type, field_name: str, value: int):
    return db.scalar(select(model).where(getattr(model, field_name) == value))


def authenticate_user(db: Session, email: str, password: str) -> models.User | None:
    user = db.scalar(select(models.User).where(models.User.email == email))
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def user_has_role(db: Session, user_id: int | None, role_name: str) -> bool:
    if not user_id:
        return False
    return bool(
        db.scalar(
            select(models.User.user_id)
            .join(models.UserRole, models.UserRole.user_id == models.User.user_id)
            .join(models.Role, models.Role.role_id == models.UserRole.role_id)
            .where(
                models.User.user_id == user_id,
                models.User.is_active.is_(True),
                models.Role.role_name == role_name,
            )
        )
    )


def create_dataset(db: Session, payload: schemas.DatasetCreate) -> models.Dataset:
    dataset = models.Dataset(**payload.model_dump())
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def create_version(db: Session, dataset_id: int, payload: schemas.VersionCreate) -> models.DatasetVersion | None:
    dataset = get_by_id(db, models.Dataset, "dataset_id", dataset_id)
    if not dataset:
        return None

    current_versions = db.scalars(
        select(models.DatasetVersion).where(
            models.DatasetVersion.dataset_id == dataset_id,
            models.DatasetVersion.is_current.is_(True),
        )
    ).all()
    for version in current_versions:
        version.is_current = False

    version = models.DatasetVersion(dataset_id=dataset_id, is_current=True, **payload.model_dump())
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def set_current_version(db: Session, version_id: int) -> models.DatasetVersion | None:
    version = get_by_id(db, models.DatasetVersion, "version_id", version_id)
    if not version:
        return None

    dataset_versions = db.scalars(
        select(models.DatasetVersion).where(models.DatasetVersion.dataset_id == version.dataset_id)
    ).all()
    for dataset_version in dataset_versions:
        dataset_version.is_current = dataset_version.version_id == version_id

    db.commit()
    db.refresh(version)
    return version


def upsert_metadata(db: Session, version_id: int, payload: schemas.MetadataUpsert) -> models.DatasetMetadata | None:
    version = get_by_id(db, models.DatasetVersion, "version_id", version_id)
    if not version:
        return None

    metadata = db.scalar(select(models.DatasetMetadata).where(models.DatasetMetadata.version_id == version_id))
    values = payload.model_dump()
    if metadata:
        for key, value in values.items():
            setattr(metadata, key, value)
        metadata.updated_at = datetime.utcnow()
    else:
        metadata = models.DatasetMetadata(version_id=version_id, **values)
        db.add(metadata)

    db.commit()
    db.refresh(metadata)
    return metadata


def _create_validation_result(
    db: Session,
    version_id: int,
    file_id: int,
    status: str,
    rows_checked: int,
    message: str,
    errors: list[FileValidationErrorItem],
) -> models.ValidationResult:
    validation = models.ValidationResult(
        version_id=version_id,
        file_id=file_id,
        status=status,
        rows_checked=rows_checked,
        errors_count=len(errors),
        message=message,
    )
    db.add(validation)
    db.flush()
    for error in errors:
        db.add(
            models.ValidationError(
                validation_id=validation.validation_id,
                row_number=error.row_number,
                column_name=error.column_name,
                error_type=error.error_type,
                error_message=error.error_message,
            )
        )
    db.flush()
    db.refresh(validation)
    return validation


def _status_by_name(db: Session, status_name: str) -> models.DatasetStatus | None:
    return db.scalar(select(models.DatasetStatus).where(models.DatasetStatus.status_name == status_name))


def _set_version_status_by_name(db: Session, version: models.DatasetVersion, status_name: str) -> None:
    status = _status_by_name(db, status_name)
    if status:
        version.status_id = status.status_id


async def save_and_validate_file(
    db: Session,
    version_id: int,
    uploaded_by: int | None,
    upload_file: UploadFile,
    is_primary: bool = True,
) -> tuple[models.DatasetFile, models.ValidationResult] | None:
    version = get_by_id(db, models.DatasetVersion, "version_id", version_id)
    if not version:
        return None

    original_name, storage_uri, full_path, file_size, checksum = await save_upload_file(upload_file)
    format_name = infer_format_name(original_name)
    data_format = None
    if format_name:
        data_format = db.scalar(select(models.DataFormat).where(models.DataFormat.format_name == format_name))

    if not data_format:
        data_format = db.scalar(select(models.DataFormat).where(models.DataFormat.format_name == "CSV"))

    dataset_file = models.DatasetFile(
        version_id=version_id,
        format_id=data_format.format_id,
        file_name=original_name,
        storage_uri=storage_uri,
        file_size=file_size,
        checksum=checksum,
        uploaded_by=uploaded_by,
        is_primary=is_primary,
    )
    db.add(dataset_file)
    db.flush()

    report = validate_observation_file(full_path)
    validation = _create_validation_result(
        db,
        version_id=version_id,
        file_id=dataset_file.file_id,
        status=report.status,
        rows_checked=report.rows_checked,
        message=report.message,
        errors=report.errors,
    )
    _set_version_status_by_name(db, version, "uploaded" if report.status == "success" else "validation_failed")
    db.commit()
    db.refresh(dataset_file)
    db.refresh(validation)
    return dataset_file, validation


def _lookup_map(db: Session, model: type, name_column: str):
    rows = db.scalars(select(model)).all()
    return {str(getattr(row, name_column)).strip().casefold(): row for row in rows}


def _find_latest_validation(db: Session, file_id: int) -> models.ValidationResult | None:
    return db.scalar(
        select(models.ValidationResult)
        .where(models.ValidationResult.file_id == file_id)
        .order_by(models.ValidationResult.validation_id.desc())
    )


def import_observations_from_file(db: Session, file_id: int) -> tuple[int, int, models.ValidationResult] | None:
    dataset_file = db.scalar(
        select(models.DatasetFile)
        .where(models.DatasetFile.file_id == file_id)
        .options(selectinload(models.DatasetFile.version))
    )
    if not dataset_file:
        return None

    full_path = storage_uri_to_path(dataset_file.storage_uri)
    structural_report = validate_observation_file(full_path)
    if structural_report.status == "failed":
        validation = _create_validation_result(
            db,
            version_id=dataset_file.version_id,
            file_id=file_id,
            status="failed",
            rows_checked=structural_report.rows_checked,
            message="Импорт отменен: файл не прошел структурную проверку.",
            errors=structural_report.errors,
        )
        _set_version_status_by_name(db, dataset_file.version, "validation_failed")
        db.commit()
        db.refresh(validation)
        return 0, structural_report.rows_checked, validation

    df = normalize_observation_frame(read_observation_file(full_path))
    regions = _lookup_map(db, models.Region, "region_name")
    agro_objects = _lookup_map(db, models.AgroObject, "object_name")
    indicators = _lookup_map(db, models.Indicator, "indicator_name")
    units = _lookup_map(db, models.MeasurementUnit, "unit_symbol")

    db.execute(delete(models.Observation).where(models.Observation.source_file_id == file_id))

    errors: list[FileValidationErrorItem] = []
    observations: list[models.Observation] = []
    skipped_rows = 0

    for idx, row in df.iterrows():
        row_number = int(idx) + 2
        region = regions.get(str(row["region"]).strip().casefold())
        agro_object = agro_objects.get(str(row["agro_object"]).strip().casefold())
        indicator = indicators.get(str(row["indicator"]).strip().casefold())
        unit = units.get(str(row["unit"]).strip().casefold())

        if not region:
            errors.append(
                FileValidationErrorItem(row_number, "region", "reference_not_found", "Регион не найден в справочнике.")
            )
        if not agro_object:
            errors.append(
                FileValidationErrorItem(
                    row_number, "agro_object", "reference_not_found", "Агрообъект не найден в справочнике."
                )
            )
        if not indicator:
            errors.append(
                FileValidationErrorItem(
                    row_number, "indicator", "reference_not_found", "Показатель не найден в справочнике."
                )
            )
        if not unit:
            errors.append(
                FileValidationErrorItem(row_number, "unit", "reference_not_found", "Единица измерения не найдена.")
            )

        if not all([region, agro_object, indicator, unit]):
            skipped_rows += 1
            continue

        observations.append(
            models.Observation(
                version_id=dataset_file.version_id,
                source_file_id=file_id,
                region_id=region.region_id,
                agro_object_id=agro_object.agro_object_id,
                indicator_id=indicator.indicator_id,
                measurement_unit_id=unit.unit_id,
                period_year=int(float(row["period_year"])),
                value_numeric=float(row["value"]),
                value_text=None,
            )
        )

    for observation in observations:
        db.add(observation)

    status = "success" if not errors else "failed"
    validation = _create_validation_result(
        db,
        version_id=dataset_file.version_id,
        file_id=file_id,
        status=status,
        rows_checked=len(df.index),
        message="Наблюдения импортированы." if status == "success" else "Импорт выполнен частично: есть ошибки справочников.",
        errors=errors,
    )
    if status == "failed":
        _set_version_status_by_name(db, dataset_file.version, "validation_failed")
    db.commit()
    db.refresh(validation)
    return len(observations), skipped_rows, validation


def current_version(dataset: models.Dataset) -> models.DatasetVersion | None:
    if not dataset.versions:
        return None
    current = next((version for version in dataset.versions if version.is_current), None)
    return current or max(dataset.versions, key=lambda version: version.version_id)


def observation_count(db: Session, version_id: int | None) -> int:
    if not version_id:
        return 0
    return int(
        db.scalar(select(func.count(models.Observation.observation_id)).where(models.Observation.version_id == version_id))
        or 0
    )


def catalog_datasets(
    db: Session,
    q: str | None = None,
    category_id: int | None = None,
    region_id: int | None = None,
    agro_object_id: int | None = None,
    indicator_id: int | None = None,
    status: str | None = None,
    access_level_id: int | None = None,
) -> list[schemas.CatalogDataset]:
    query = select(models.Dataset).options(
        selectinload(models.Dataset.category),
        selectinload(models.Dataset.versions).selectinload(models.DatasetVersion.status),
        selectinload(models.Dataset.versions).selectinload(models.DatasetVersion.access_level),
        selectinload(models.Dataset.versions).selectinload(models.DatasetVersion.source),
    )
    if q:
        pattern = f"%{q}%"
        query = query.where(or_(models.Dataset.title.ilike(pattern), models.Dataset.description.ilike(pattern)))
    if category_id:
        query = query.where(models.Dataset.category_id == category_id)

    datasets = db.scalars(query.order_by(models.Dataset.updated_at.desc())).all()
    result: list[schemas.CatalogDataset] = []

    for dataset in datasets:
        version = current_version(dataset)
        if status and (not version or not version.status or version.status.status_name != status):
            continue
        if access_level_id and (not version or version.access_level_id != access_level_id):
            continue

        if any([region_id, agro_object_id, indicator_id]):
            if not version:
                continue
            observation_query = select(func.count(models.Observation.observation_id)).where(
                models.Observation.version_id == version.version_id
            )
            if region_id:
                observation_query = observation_query.where(models.Observation.region_id == region_id)
            if agro_object_id:
                observation_query = observation_query.where(models.Observation.agro_object_id == agro_object_id)
            if indicator_id:
                observation_query = observation_query.where(models.Observation.indicator_id == indicator_id)
            if int(db.scalar(observation_query) or 0) == 0:
                continue

        result.append(
            schemas.CatalogDataset(
                dataset_id=dataset.dataset_id,
                title=dataset.title,
                description=dataset.description,
                category_id=dataset.category_id,
                category_name=dataset.category.category_name if dataset.category else None,
                current_version_id=version.version_id if version else None,
                version_number=version.version_number if version else None,
                status=version.status.status_name if version and version.status else None,
                access_level=version.access_level.access_level_name if version and version.access_level else None,
                source=version.source.source_name if version and version.source else None,
                observations_count=observation_count(db, version.version_id if version else None),
                created_at=dataset.created_at,
                updated_at=dataset.updated_at,
            )
        )
    return result


def get_dataset_detail(db: Session, dataset_id: int) -> schemas.DatasetDetail | None:
    dataset = db.scalar(
        select(models.Dataset)
        .where(models.Dataset.dataset_id == dataset_id)
        .options(
            selectinload(models.Dataset.category),
            selectinload(models.Dataset.versions).selectinload(models.DatasetVersion.status),
            selectinload(models.Dataset.versions).selectinload(models.DatasetVersion.access_level),
            selectinload(models.Dataset.versions).selectinload(models.DatasetVersion.source),
            selectinload(models.Dataset.versions).selectinload(models.DatasetVersion.metadata_record).selectinload(
                models.DatasetMetadata.license
            ),
            selectinload(models.Dataset.versions).selectinload(models.DatasetVersion.files).selectinload(
                models.DatasetFile.format
            ),
        )
    )
    if not dataset:
        return None

    version = current_version(dataset)
    metadata = version.metadata_record if version else None
    versions = [
        {
            "version_id": item.version_id,
            "version_number": item.version_number,
            "status": item.status.status_name if item.status else None,
            "access_level": item.access_level.access_level_name if item.access_level else None,
            "source": item.source.source_name if item.source else None,
            "is_current": item.is_current,
            "created_at": item.created_at,
            "published_at": item.published_at,
            "change_note": item.change_note,
            "files_count": len(item.files),
            "observations_count": observation_count(db, item.version_id),
        }
        for item in sorted(dataset.versions, key=lambda version_item: version_item.version_id)
    ]
    files = []
    if version:
        for dataset_file in version.files:
            latest_validation = _find_latest_validation(db, dataset_file.file_id)
            files.append(
                {
                    "file_id": dataset_file.file_id,
                    "file_name": dataset_file.file_name,
                    "format": dataset_file.format.format_name if dataset_file.format else None,
                    "file_size": dataset_file.file_size,
                    "checksum": dataset_file.checksum,
                    "uploaded_at": dataset_file.uploaded_at,
                    "is_primary": dataset_file.is_primary,
                    "validation_status": latest_validation.status if latest_validation else None,
                    "validation_message": latest_validation.message if latest_validation else None,
                    "errors_count": latest_validation.errors_count if latest_validation else 0,
                }
            )

    return schemas.DatasetDetail(
        dataset_id=dataset.dataset_id,
        title=dataset.title,
        description=dataset.description,
        category={
            "category_id": dataset.category.category_id,
            "category_name": dataset.category.category_name,
        }
        if dataset.category
        else None,
        created_by=dataset.created_by,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
        versions=versions,
        current_version={
            "version_id": version.version_id,
            "version_number": version.version_number,
            "status": version.status.status_name if version.status else None,
            "access_level": version.access_level.access_level_name if version.access_level else None,
            "source": version.source.source_name if version.source else None,
            "created_at": version.created_at,
            "published_at": version.published_at,
            "change_note": version.change_note,
        }
        if version
        else None,
        metadata={
            "metadata_id": metadata.metadata_id,
            "annotation": metadata.annotation,
            "methodology": metadata.methodology,
            "temporal_coverage": metadata.temporal_coverage,
            "spatial_coverage": metadata.spatial_coverage,
            "license": metadata.license.license_name if metadata.license else None,
            "quality_note": metadata.quality_note,
            "citation": metadata.citation,
        }
        if metadata
        else None,
        files=files,
        observations_count=observation_count(db, version.version_id if version else None),
    )


def list_observations(
    db: Session,
    version_id: int,
    region_id: int | None = None,
    agro_object_id: int | None = None,
    indicator_id: int | None = None,
    period_year: int | None = None,
) -> list[dict[str, Any]]:
    query = (
        select(models.Observation)
        .where(models.Observation.version_id == version_id)
        .options(
            selectinload(models.Observation.region),
            selectinload(models.Observation.agro_object),
            selectinload(models.Observation.indicator),
            selectinload(models.Observation.measurement_unit),
        )
    )
    if region_id:
        query = query.where(models.Observation.region_id == region_id)
    if agro_object_id:
        query = query.where(models.Observation.agro_object_id == agro_object_id)
    if indicator_id:
        query = query.where(models.Observation.indicator_id == indicator_id)
    if period_year:
        query = query.where(models.Observation.period_year == period_year)

    observations = db.scalars(query.order_by(models.Observation.observation_id)).all()
    return [
        {
            "observation_id": item.observation_id,
            "version_id": item.version_id,
            "source_file_id": item.source_file_id,
            "region_id": item.region_id,
            "region_name": item.region.region_name,
            "agro_object_id": item.agro_object_id,
            "agro_object_name": item.agro_object.object_name,
            "indicator_id": item.indicator_id,
            "indicator_name": item.indicator.indicator_name,
            "measurement_unit_id": item.measurement_unit_id,
            "unit_symbol": item.measurement_unit.unit_symbol,
            "period_year": item.period_year,
            "value_numeric": item.value_numeric,
            "value_text": item.value_text,
            "created_at": item.created_at,
        }
        for item in observations
    ]


def create_export_record(
    db: Session,
    user_id: int | None,
    version_id: int | None,
    file_id: int | None,
    export_scope: str,
    export_format: str,
    export_status: str,
) -> models.DataExport:
    export = models.DataExport(
        user_id=user_id,
        version_id=version_id,
        file_id=file_id,
        export_scope=export_scope,
        export_format=export_format,
        export_status=export_status,
    )
    db.add(export)
    db.commit()
    db.refresh(export)
    return export


def get_downloadable_file(db: Session, file_id: int, user_id: int | None) -> tuple[models.DatasetFile, Path] | None:
    dataset_file = get_by_id(db, models.DatasetFile, "file_id", file_id)
    if not dataset_file:
        return None
    path = storage_uri_to_path(dataset_file.storage_uri)
    status = "success" if path.exists() else "failed"
    create_export_record(
        db,
        user_id=user_id,
        version_id=dataset_file.version_id,
        file_id=file_id,
        export_scope="source_file",
        export_format=dataset_file.format.format_name if dataset_file.format else "CSV",
        export_status=status,
    )
    return dataset_file, path


def export_observations_to_csv(db: Session, version_id: int, user_id: int | None) -> Path | None:
    version = get_by_id(db, models.DatasetVersion, "version_id", version_id)
    if not version:
        return None

    rows = list_observations(db, version_id)
    export_directory = ensure_storage_dir() / "exports"
    export_path = export_directory / f"observations_version_{version_id}_{uuid4().hex}.csv"
    pd.DataFrame(rows).to_csv(export_path, index=False, encoding="utf-8-sig")
    create_export_record(
        db,
        user_id=user_id,
        version_id=version_id,
        file_id=None,
        export_scope="observations",
        export_format="CSV",
        export_status="success",
    )
    return export_path


def delete_dataset_file(db: Session, file_id: int) -> models.DatasetFile | None:
    dataset_file = get_by_id(db, models.DatasetFile, "file_id", file_id)
    if not dataset_file:
        return None

    path = storage_uri_to_path(dataset_file.storage_uri)
    validation_ids = select(models.ValidationResult.validation_id).where(models.ValidationResult.file_id == file_id)
    db.execute(delete(models.ValidationError).where(models.ValidationError.validation_id.in_(validation_ids)))
    db.execute(delete(models.ValidationResult).where(models.ValidationResult.file_id == file_id))
    db.execute(delete(models.Observation).where(models.Observation.source_file_id == file_id))
    db.execute(update(models.DataExport).where(models.DataExport.file_id == file_id).values(file_id=None))
    db.delete(dataset_file)
    db.commit()

    if path.exists():
        path.unlink()
    return dataset_file


def _delete_version_files(db: Session, version_id: int) -> list[Path]:
    files = db.scalars(select(models.DatasetFile).where(models.DatasetFile.version_id == version_id)).all()
    paths = [storage_uri_to_path(dataset_file.storage_uri) for dataset_file in files]
    file_ids = [dataset_file.file_id for dataset_file in files]
    if file_ids:
        validation_ids = select(models.ValidationResult.validation_id).where(models.ValidationResult.file_id.in_(file_ids))
        db.execute(delete(models.ValidationError).where(models.ValidationError.validation_id.in_(validation_ids)))
        db.execute(delete(models.ValidationResult).where(models.ValidationResult.file_id.in_(file_ids)))
        db.execute(update(models.DataExport).where(models.DataExport.file_id.in_(file_ids)).values(file_id=None))
        db.execute(delete(models.DatasetFile).where(models.DatasetFile.file_id.in_(file_ids)))
    return paths


def delete_dataset_version(db: Session, version_id: int) -> models.DatasetVersion | None:
    version = get_by_id(db, models.DatasetVersion, "version_id", version_id)
    if not version:
        return None

    dataset_id = version.dataset_id
    was_current = version.is_current
    file_paths = _delete_version_files(db, version_id)
    db.execute(update(models.DataExport).where(models.DataExport.version_id == version_id).values(version_id=None))
    db.execute(delete(models.Observation).where(models.Observation.version_id == version_id))
    db.execute(delete(models.DatasetMetadata).where(models.DatasetMetadata.version_id == version_id))
    db.execute(delete(models.VersionKeyword).where(models.VersionKeyword.version_id == version_id))
    db.execute(delete(models.DatasetVersion).where(models.DatasetVersion.version_id == version_id))

    if was_current:
        replacement = db.scalar(
            select(models.DatasetVersion)
            .where(models.DatasetVersion.dataset_id == dataset_id)
            .order_by(models.DatasetVersion.version_id.desc())
        )
        if replacement:
            replacement.is_current = True

    db.commit()
    for path in file_paths:
        if path.exists():
            path.unlink()
    return version


def delete_dataset(db: Session, dataset_id: int) -> models.Dataset | None:
    dataset = get_by_id(db, models.Dataset, "dataset_id", dataset_id)
    if not dataset:
        return None

    version_ids = db.scalars(select(models.DatasetVersion.version_id).where(models.DatasetVersion.dataset_id == dataset_id)).all()
    file_paths: list[Path] = []
    for version_id in version_ids:
        file_paths.extend(_delete_version_files(db, version_id))
        db.execute(update(models.DataExport).where(models.DataExport.version_id == version_id).values(version_id=None))
        db.execute(delete(models.Observation).where(models.Observation.version_id == version_id))
        db.execute(delete(models.DatasetMetadata).where(models.DatasetMetadata.version_id == version_id))
        db.execute(delete(models.VersionKeyword).where(models.VersionKeyword.version_id == version_id))
    db.execute(delete(models.DatasetVersion).where(models.DatasetVersion.dataset_id == dataset_id))
    db.execute(delete(models.Dataset).where(models.Dataset.dataset_id == dataset_id))
    db.commit()

    for path in file_paths:
        if path.exists():
            path.unlink()
    return dataset


def get_dashboard_stats(db: Session) -> dict[str, Any]:
    status_rows = db.execute(
        select(models.DatasetStatus.status_name, func.count(models.DatasetVersion.version_id))
        .join(models.DatasetVersion, models.DatasetVersion.status_id == models.DatasetStatus.status_id)
        .group_by(models.DatasetStatus.status_name)
        .order_by(models.DatasetStatus.status_name)
    ).all()

    return {
        "datasets_count": int(db.scalar(select(func.count(models.Dataset.dataset_id))) or 0),
        "versions_count": int(db.scalar(select(func.count(models.DatasetVersion.version_id))) or 0),
        "files_count": int(db.scalar(select(func.count(models.DatasetFile.file_id))) or 0),
        "observations_count": int(db.scalar(select(func.count(models.Observation.observation_id))) or 0),
        "exports_count": int(db.scalar(select(func.count(models.DataExport.export_id))) or 0),
        "validation_errors_count": int(db.scalar(select(func.count(models.ValidationError.error_id))) or 0),
        "versions_by_status": [
            {"status": status_name, "count": int(count)}
            for status_name, count in status_rows
        ],
    }


def get_analytics_summary(db: Session) -> dict[str, Any]:
    datasets_by_category = db.execute(
        select(models.Category.category_name, func.count(models.Dataset.dataset_id))
        .join(models.Dataset, models.Dataset.category_id == models.Category.category_id)
        .group_by(models.Category.category_name)
        .order_by(func.count(models.Dataset.dataset_id).desc(), models.Category.category_name)
    ).all()

    observations_by_region = db.execute(
        select(models.Region.region_name, func.count(models.Observation.observation_id))
        .join(models.Observation, models.Observation.region_id == models.Region.region_id)
        .group_by(models.Region.region_name)
        .order_by(func.count(models.Observation.observation_id).desc(), models.Region.region_name)
    ).all()

    observations_by_indicator = db.execute(
        select(models.Indicator.indicator_name, func.count(models.Observation.observation_id))
        .join(models.Observation, models.Observation.indicator_id == models.Indicator.indicator_id)
        .group_by(models.Indicator.indicator_name)
        .order_by(func.count(models.Observation.observation_id).desc(), models.Indicator.indicator_name)
    ).all()

    observations_by_agro_object = db.execute(
        select(models.AgroObject.object_name, models.AgroObject.object_type, func.count(models.Observation.observation_id))
        .join(models.Observation, models.Observation.agro_object_id == models.AgroObject.agro_object_id)
        .group_by(models.AgroObject.object_name, models.AgroObject.object_type)
        .order_by(func.count(models.Observation.observation_id).desc(), models.AgroObject.object_name)
    ).all()

    value_by_indicator = db.execute(
        select(models.Indicator.indicator_name, func.sum(models.Observation.value_numeric))
        .join(models.Observation, models.Observation.indicator_id == models.Indicator.indicator_id)
        .where(models.Observation.value_numeric.is_not(None))
        .group_by(models.Indicator.indicator_name)
        .order_by(func.sum(models.Observation.value_numeric).desc(), models.Indicator.indicator_name)
    ).all()

    return {
        "datasets_by_category": [
            {"category_name": category_name, "count": int(count)}
            for category_name, count in datasets_by_category
        ],
        "observations_by_region": [
            {"region_name": region_name, "count": int(count)}
            for region_name, count in observations_by_region
        ],
        "observations_by_indicator": [
            {"indicator_name": indicator_name, "count": int(count)}
            for indicator_name, count in observations_by_indicator
        ],
        "observations_by_agro_object": [
            {"agro_object_name": object_name, "object_type": object_type, "count": int(count)}
            for object_name, object_type, count in observations_by_agro_object
        ],
        "value_sum_by_indicator": [
            {"indicator_name": indicator_name, "value_numeric": float(value or 0)}
            for indicator_name, value in value_by_indicator
        ],
    }


def list_exports_detailed(db: Session) -> list[dict[str, Any]]:
    exports = db.scalars(
        select(models.DataExport)
        .options(
            selectinload(models.DataExport.user),
            selectinload(models.DataExport.version).selectinload(models.DatasetVersion.dataset),
            selectinload(models.DataExport.file),
        )
        .order_by(models.DataExport.requested_at.desc())
    ).all()

    result: list[dict[str, Any]] = []
    for export in exports:
        dataset = export.version.dataset if export.version else None
        result.append(
            {
                "export_id": export.export_id,
                "requested_at": export.requested_at,
                "user_id": export.user_id,
                "user_name": export.user.full_name if export.user else None,
                "dataset_id": dataset.dataset_id if dataset else None,
                "dataset_title": dataset.title if dataset else None,
                "version_id": export.version_id,
                "version_number": export.version.version_number if export.version else None,
                "file_id": export.file_id,
                "file_name": export.file.file_name if export.file else None,
                "export_scope": export.export_scope,
                "export_format": export.export_format,
                "export_status": export.export_status,
            }
        )
    return result


def get_references(db: Session) -> dict[str, Any]:
    def serialize(rows, id_name: str, name_name: str, extra: list[str] | None = None):
        result = []
        for row in rows:
            item = {id_name: getattr(row, id_name), name_name: getattr(row, name_name)}
            for key in extra or []:
                item[key] = getattr(row, key)
            result.append(item)
        return result

    return {
        "categories": serialize(db.scalars(select(models.Category).order_by(models.Category.category_name)).all(), "category_id", "category_name"),
        "statuses": serialize(db.scalars(select(models.DatasetStatus).order_by(models.DatasetStatus.status_id)).all(), "status_id", "status_name"),
        "access_levels": serialize(db.scalars(select(models.AccessLevel).order_by(models.AccessLevel.access_level_id)).all(), "access_level_id", "access_level_name"),
        "sources": serialize(db.scalars(select(models.DataSource).order_by(models.DataSource.source_name)).all(), "source_id", "source_name"),
        "licenses": serialize(db.scalars(select(models.License).order_by(models.License.license_name)).all(), "license_id", "license_name"),
        "regions": serialize(db.scalars(select(models.Region).order_by(models.Region.region_name)).all(), "region_id", "region_name", ["region_code"]),
        "agro_objects": serialize(db.scalars(select(models.AgroObject).order_by(models.AgroObject.object_name)).all(), "agro_object_id", "object_name", ["object_type"]),
        "indicators": serialize(db.scalars(select(models.Indicator).order_by(models.Indicator.indicator_name)).all(), "indicator_id", "indicator_name"),
        "formats": serialize(db.scalars(select(models.DataFormat).order_by(models.DataFormat.format_name)).all(), "format_id", "format_name", ["mime_type"]),
        "units": serialize(db.scalars(select(models.MeasurementUnit).order_by(models.MeasurementUnit.unit_symbol)).all(), "unit_id", "unit_symbol", ["unit_name"]),
    }
