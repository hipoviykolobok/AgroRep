from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OrmModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    user_id: int
    full_name: str
    email: EmailStr
    organization: str | None = None
    roles: list[str]


class DatasetCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    category_id: int
    created_by: int


class DatasetRead(OrmModel):
    dataset_id: int
    title: str
    description: str | None
    category_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime


class VersionCreate(BaseModel):
    version_number: str = Field(min_length=1, max_length=50)
    status_id: int
    access_level_id: int
    source_id: int | None = None
    change_note: str | None = None


class VersionRead(OrmModel):
    version_id: int
    dataset_id: int
    version_number: str
    status_id: int
    access_level_id: int
    source_id: int | None
    is_current: bool
    created_at: datetime
    published_at: datetime | None
    change_note: str | None


class MetadataUpsert(BaseModel):
    annotation: str | None = None
    methodology: str | None = None
    temporal_coverage: str | None = None
    spatial_coverage: str | None = None
    license_id: int | None = None
    quality_note: str | None = None
    citation: str | None = None


class MetadataRead(OrmModel):
    metadata_id: int
    version_id: int
    annotation: str | None
    methodology: str | None
    temporal_coverage: str | None
    spatial_coverage: str | None
    license_id: int | None
    quality_note: str | None
    citation: str | None
    created_at: datetime
    updated_at: datetime


class ValidationErrorRead(OrmModel):
    error_id: int
    validation_id: int
    row_number: int | None
    column_name: str | None
    error_type: str
    error_message: str


class ValidationResultRead(OrmModel):
    validation_id: int
    version_id: int
    file_id: int
    status: str
    checked_at: datetime
    rows_checked: int
    errors_count: int
    message: str | None
    errors: list[ValidationErrorRead] = Field(default_factory=list)


class DatasetFileRead(OrmModel):
    file_id: int
    version_id: int
    format_id: int
    file_name: str
    storage_uri: str
    file_size: int
    checksum: str
    uploaded_by: int | None
    uploaded_at: datetime
    is_primary: bool


class FileUploadResponse(BaseModel):
    file: DatasetFileRead
    validation: ValidationResultRead


class ObservationRead(OrmModel):
    observation_id: int
    version_id: int
    source_file_id: int | None
    region_id: int
    region_name: str | None = None
    agro_object_id: int
    agro_object_name: str | None = None
    indicator_id: int
    indicator_name: str | None = None
    measurement_unit_id: int
    unit_symbol: str | None = None
    period_year: int | None
    value_numeric: float | None
    value_text: str | None
    created_at: datetime


class ImportResponse(BaseModel):
    imported_count: int
    skipped_count: int
    validation: ValidationResultRead


class CatalogDataset(BaseModel):
    dataset_id: int
    title: str
    description: str | None
    category_id: int
    category_name: str | None
    current_version_id: int | None
    version_number: str | None
    status: str | None
    access_level: str | None
    source: str | None
    observations_count: int
    created_at: datetime
    updated_at: datetime


class DatasetDetail(BaseModel):
    dataset_id: int
    title: str
    description: str | None
    category: dict[str, Any] | None
    created_by: int
    created_at: datetime
    updated_at: datetime
    versions: list[dict[str, Any]]
    current_version: dict[str, Any] | None
    metadata: dict[str, Any] | None
    files: list[dict[str, Any]]
    observations_count: int


class ExportRead(OrmModel):
    export_id: int
    user_id: int | None
    version_id: int | None
    file_id: int | None
    export_scope: str
    export_format: str
    export_status: str
    requested_at: datetime


class SeedResponse(BaseModel):
    status: str
    message: str


class DeleteResponse(BaseModel):
    status: str
    message: str
