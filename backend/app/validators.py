from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import pandas as pd
from fastapi import UploadFile


REQUIRED_OBSERVATION_COLUMNS = {"region", "agro_object", "indicator", "unit", "period_year", "value"}
SUPPORTED_EXTENSIONS = {".csv": "CSV", ".xlsx": "XLSX"}


@dataclass
class FileValidationErrorItem:
    row_number: int | None
    column_name: str | None
    error_type: str
    error_message: str


@dataclass
class FileValidationReport:
    status: str
    rows_checked: int
    errors_count: int
    message: str
    errors: list[FileValidationErrorItem]


def project_root() -> Path:
    backend_dir = Path(__file__).resolve().parents[1]
    if backend_dir.name == "backend":
        return backend_dir.parent
    return backend_dir


def storage_dir() -> Path:
    return Path(os.getenv("STORAGE_DIR", str(project_root() / "storage"))).resolve()


def ensure_storage_dir() -> Path:
    directory = storage_dir()
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "exports").mkdir(parents=True, exist_ok=True)
    return directory


def clean_filename(filename: str) -> str:
    basename = Path(filename).name or "uploaded_file"
    return re.sub(r"[^A-Za-z0-9А-Яа-яЁё._-]+", "_", basename)


def infer_format_name(filename: str) -> str | None:
    return SUPPORTED_EXTENSIONS.get(Path(filename).suffix.lower())


def storage_uri_to_path(storage_uri: str) -> Path:
    if storage_uri.startswith("storage/"):
        return storage_dir() / storage_uri.removeprefix("storage/")
    return Path(storage_uri)


async def save_upload_file(upload_file: UploadFile) -> tuple[str, str, Path, int, str]:
    ensure_storage_dir()
    original_name = clean_filename(upload_file.filename or "uploaded_file")
    stored_name = f"{uuid4().hex}_{original_name}"
    full_path = storage_dir() / stored_name
    content = await upload_file.read()
    full_path.write_bytes(content)
    checksum = hashlib.sha256(content).hexdigest()
    storage_uri = f"storage/{stored_name}"
    return original_name, storage_uri, full_path, len(content), checksum


def read_observation_file(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix == ".xlsx":
        return pd.read_excel(path)
    raise ValueError("Поддерживаются только CSV и XLSX")


def normalize_observation_frame(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized.columns = [str(column).strip() for column in normalized.columns]
    for column in normalized.columns:
        if normalized[column].dtype == object:
            normalized[column] = normalized[column].map(lambda value: value.strip() if isinstance(value, str) else value)
    return normalized


def validate_observation_file(path: Path) -> FileValidationReport:
    errors: list[FileValidationErrorItem] = []
    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        errors.append(
            FileValidationErrorItem(None, None, "unsupported_format", "Файл должен быть в формате CSV или XLSX.")
        )
        return FileValidationReport("failed", 0, len(errors), "Файл не прошел проверку.", errors)

    try:
        df = normalize_observation_frame(read_observation_file(path))
    except Exception as exc:
        errors.append(FileValidationErrorItem(None, None, "read_error", f"Не удалось прочитать файл: {exc}"))
        return FileValidationReport("failed", 0, len(errors), "Файл не прошел проверку.", errors)

    rows_checked = int(len(df.index))
    if df.empty:
        errors.append(FileValidationErrorItem(None, None, "empty_file", "Файл не должен быть пустым."))

    missing_columns = sorted(REQUIRED_OBSERVATION_COLUMNS - set(df.columns))
    for column in missing_columns:
        errors.append(
            FileValidationErrorItem(None, column, "missing_column", f"Отсутствует обязательная колонка '{column}'.")
        )

    if not missing_columns:
        for idx, value in df["period_year"].items():
            if pd.isna(value) or pd.to_numeric(pd.Series([value]), errors="coerce").isna().iloc[0]:
                errors.append(
                    FileValidationErrorItem(
                        int(idx) + 2,
                        "period_year",
                        "invalid_number",
                        "period_year должен быть числом.",
                    )
                )

        for idx, value in df["value"].items():
            if pd.isna(value) or pd.to_numeric(pd.Series([value]), errors="coerce").isna().iloc[0]:
                errors.append(
                    FileValidationErrorItem(
                        int(idx) + 2,
                        "value",
                        "invalid_number",
                        "value должен быть числом для импорта в аналитический слой MVP.",
                    )
                )

    status = "success" if not errors else "failed"
    message = "Файл успешно прошел базовую проверку." if status == "success" else "Файл не прошел проверку."
    return FileValidationReport(status, rows_checked, len(errors), message, errors)
