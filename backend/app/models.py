from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class User(Base, TimestampMixin):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    organization: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    roles: Mapped[list["Role"]] = relationship(secondary="user_roles", back_populates="users")
    datasets: Mapped[list["Dataset"]] = relationship(back_populates="creator")
    files: Mapped[list["DatasetFile"]] = relationship(back_populates="uploader")
    exports: Mapped[list["DataExport"]] = relationship(back_populates="user")


class Role(Base):
    __tablename__ = "roles"

    role_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    role_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    users: Mapped[list[User]] = relationship(secondary="user_roles", back_populates="roles")


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AccessLevel(Base):
    __tablename__ = "access_levels"

    access_level_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    access_level_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    versions: Mapped[list["DatasetVersion"]] = relationship(back_populates="access_level")


class Category(Base):
    __tablename__ = "categories"

    category_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    datasets: Mapped[list["Dataset"]] = relationship(back_populates="category")


class DataFormat(Base):
    __tablename__ = "formats"

    format_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    format_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(255))

    files: Mapped[list["DatasetFile"]] = relationship(back_populates="format")


class License(Base):
    __tablename__ = "licenses"

    license_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    license_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    metadata_records: Mapped[list["DatasetMetadata"]] = relationship(back_populates="license")


class Region(Base):
    __tablename__ = "regions"

    region_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    region_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    region_code: Mapped[str | None] = mapped_column(String(50))

    observations: Mapped[list["Observation"]] = relationship(back_populates="region")


class AgroObject(Base):
    __tablename__ = "agro_objects"

    agro_object_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    object_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    object_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    observations: Mapped[list["Observation"]] = relationship(back_populates="agro_object")


class Indicator(Base):
    __tablename__ = "indicators"

    indicator_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    indicator_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    observations: Mapped[list["Observation"]] = relationship(back_populates="indicator")


class MeasurementUnit(Base):
    __tablename__ = "measurement_units"

    unit_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    unit_name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_symbol: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    observations: Mapped[list["Observation"]] = relationship(back_populates="measurement_unit")


class DatasetStatus(Base):
    __tablename__ = "dataset_statuses"

    status_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    status_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    versions: Mapped[list["DatasetVersion"]] = relationship(back_populates="status")


class DataSource(Base):
    __tablename__ = "data_sources"

    source_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500))
    source_type: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)

    versions: Mapped[list["DatasetVersion"]] = relationship(back_populates="source")


class Dataset(Base):
    __tablename__ = "datasets"

    dataset_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.category_id"), nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    category: Mapped[Category] = relationship(back_populates="datasets")
    creator: Mapped[User] = relationship(back_populates="datasets")
    versions: Mapped[list["DatasetVersion"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"
    __table_args__ = (UniqueConstraint("dataset_id", "version_number", name="uq_dataset_version_number"),)

    version_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.dataset_id", ondelete="CASCADE"), nullable=False)
    version_number: Mapped[str] = mapped_column(String(50), nullable=False)
    status_id: Mapped[int] = mapped_column(ForeignKey("dataset_statuses.status_id"), nullable=False)
    access_level_id: Mapped[int] = mapped_column(ForeignKey("access_levels.access_level_id"), nullable=False)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("data_sources.source_id"))
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    change_note: Mapped[str | None] = mapped_column(Text)

    dataset: Mapped[Dataset] = relationship(back_populates="versions")
    status: Mapped[DatasetStatus] = relationship(back_populates="versions")
    access_level: Mapped[AccessLevel] = relationship(back_populates="versions")
    source: Mapped[DataSource | None] = relationship(back_populates="versions")
    metadata_record: Mapped["DatasetMetadata | None"] = relationship(
        back_populates="version", cascade="all, delete-orphan", uselist=False
    )
    files: Mapped[list["DatasetFile"]] = relationship(back_populates="version", cascade="all, delete-orphan")
    observations: Mapped[list["Observation"]] = relationship(back_populates="version", cascade="all, delete-orphan")
    keywords: Mapped[list["Keyword"]] = relationship(secondary="version_keywords", back_populates="versions")
    validation_results: Mapped[list["ValidationResult"]] = relationship(back_populates="version")
    exports: Mapped[list["DataExport"]] = relationship(back_populates="version")


class DatasetMetadata(Base):
    __tablename__ = "dataset_metadata"

    metadata_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("dataset_versions.version_id", ondelete="CASCADE"), unique=True)
    annotation: Mapped[str | None] = mapped_column(Text)
    methodology: Mapped[str | None] = mapped_column(Text)
    temporal_coverage: Mapped[str | None] = mapped_column(String(255))
    spatial_coverage: Mapped[str | None] = mapped_column(String(255))
    license_id: Mapped[int | None] = mapped_column(ForeignKey("licenses.license_id"))
    quality_note: Mapped[str | None] = mapped_column(Text)
    citation: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    version: Mapped[DatasetVersion] = relationship(back_populates="metadata_record")
    license: Mapped[License | None] = relationship(back_populates="metadata_records")


class DatasetFile(Base):
    __tablename__ = "dataset_files"

    file_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("dataset_versions.version_id", ondelete="CASCADE"), nullable=False)
    format_id: Mapped[int] = mapped_column(ForeignKey("formats.format_id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_uri: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("users.user_id"))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    version: Mapped[DatasetVersion] = relationship(back_populates="files")
    format: Mapped[DataFormat] = relationship(back_populates="files")
    uploader: Mapped[User | None] = relationship(back_populates="files")
    observations: Mapped[list["Observation"]] = relationship(back_populates="source_file")
    validation_results: Mapped[list["ValidationResult"]] = relationship(back_populates="file")
    exports: Mapped[list["DataExport"]] = relationship(back_populates="file")


class Keyword(Base):
    __tablename__ = "keywords"

    keyword_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    keyword_text: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    versions: Mapped[list[DatasetVersion]] = relationship(secondary="version_keywords", back_populates="keywords")


class VersionKeyword(Base):
    __tablename__ = "version_keywords"
    __table_args__ = (UniqueConstraint("version_id", "keyword_id", name="uq_version_keyword"),)

    version_id: Mapped[int] = mapped_column(ForeignKey("dataset_versions.version_id", ondelete="CASCADE"), primary_key=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.keyword_id", ondelete="CASCADE"), primary_key=True)


class Observation(Base):
    __tablename__ = "observations"

    observation_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("dataset_versions.version_id", ondelete="CASCADE"), nullable=False)
    source_file_id: Mapped[int | None] = mapped_column(ForeignKey("dataset_files.file_id", ondelete="SET NULL"))
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.region_id"), nullable=False)
    agro_object_id: Mapped[int] = mapped_column(ForeignKey("agro_objects.agro_object_id"), nullable=False)
    indicator_id: Mapped[int] = mapped_column(ForeignKey("indicators.indicator_id"), nullable=False)
    measurement_unit_id: Mapped[int] = mapped_column(ForeignKey("measurement_units.unit_id"), nullable=False)
    period_year: Mapped[int | None] = mapped_column(Integer)
    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date | None] = mapped_column(Date)
    value_numeric: Mapped[float | None] = mapped_column(Float)
    value_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    version: Mapped[DatasetVersion] = relationship(back_populates="observations")
    source_file: Mapped[DatasetFile | None] = relationship(back_populates="observations")
    region: Mapped[Region] = relationship(back_populates="observations")
    agro_object: Mapped[AgroObject] = relationship(back_populates="observations")
    indicator: Mapped[Indicator] = relationship(back_populates="observations")
    measurement_unit: Mapped[MeasurementUnit] = relationship(back_populates="observations")


class ValidationResult(Base):
    __tablename__ = "validation_results"

    validation_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    version_id: Mapped[int] = mapped_column(ForeignKey("dataset_versions.version_id", ondelete="CASCADE"), nullable=False)
    file_id: Mapped[int] = mapped_column(ForeignKey("dataset_files.file_id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    rows_checked: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    message: Mapped[str | None] = mapped_column(Text)

    version: Mapped[DatasetVersion] = relationship(back_populates="validation_results")
    file: Mapped[DatasetFile] = relationship(back_populates="validation_results")
    errors: Mapped[list["ValidationError"]] = relationship(back_populates="validation", cascade="all, delete-orphan")


class ValidationError(Base):
    __tablename__ = "validation_errors"

    error_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    validation_id: Mapped[int] = mapped_column(ForeignKey("validation_results.validation_id", ondelete="CASCADE"), nullable=False)
    row_number: Mapped[int | None] = mapped_column(Integer)
    column_name: Mapped[str | None] = mapped_column(String(255))
    error_type: Mapped[str] = mapped_column(String(100), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)

    validation: Mapped[ValidationResult] = relationship(back_populates="errors")


class DataExport(Base):
    __tablename__ = "data_exports"

    export_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.user_id", ondelete="SET NULL"))
    version_id: Mapped[int | None] = mapped_column(ForeignKey("dataset_versions.version_id", ondelete="SET NULL"))
    file_id: Mapped[int | None] = mapped_column(ForeignKey("dataset_files.file_id", ondelete="SET NULL"))
    export_scope: Mapped[str] = mapped_column(String(50), nullable=False)
    export_format: Mapped[str] = mapped_column(String(50), nullable=False)
    export_status: Mapped[str] = mapped_column(String(50), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User | None] = relationship(back_populates="exports")
    version: Mapped[DatasetVersion | None] = relationship(back_populates="exports")
    file: Mapped[DatasetFile | None] = relationship(back_populates="exports")
