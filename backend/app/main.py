from __future__ import annotations

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import get_db, init_db
from app.seed import seed_database


app = FastAPI(
    title="Agricultural Data Repository MVP",
    description="MVP-прототип репозитория сельскохозяйственных данных для ВКР.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db(retries=15, delay_seconds=2)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/seed", response_model=schemas.SeedResponse)
def seed(db: Session = Depends(get_db)) -> schemas.SeedResponse:
    seed_database(db)
    return schemas.SeedResponse(status="ok", message="Справочники и demo-пользователи созданы или уже существуют.")


@app.post("/auth/login", response_model=schemas.LoginResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)) -> schemas.LoginResponse:
    user = crud.authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Неверный email или пароль.")
    return schemas.LoginResponse(
        user_id=user.user_id,
        full_name=user.full_name,
        email=user.email,
        organization=user.organization,
        roles=[role.role_name for role in user.roles],
    )


@app.get("/references")
def references(db: Session = Depends(get_db)):
    return crud.get_references(db)


@app.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    return crud.get_dashboard_stats(db)


@app.get("/analytics")
def analytics(db: Session = Depends(get_db)):
    return crud.get_analytics_summary(db)


@app.get("/catalog/datasets", response_model=list[schemas.CatalogDataset])
def catalog_datasets(
    q: str | None = None,
    category_id: int | None = None,
    region_id: int | None = None,
    agro_object_id: int | None = None,
    indicator_id: int | None = None,
    status: str | None = None,
    access_level_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[schemas.CatalogDataset]:
    return crud.catalog_datasets(
        db,
        q=q,
        category_id=category_id,
        region_id=region_id,
        agro_object_id=agro_object_id,
        indicator_id=indicator_id,
        status=status,
        access_level_id=access_level_id,
    )


@app.post("/datasets", response_model=schemas.DatasetRead, status_code=201)
def create_dataset(payload: schemas.DatasetCreate, db: Session = Depends(get_db)) -> models.Dataset:
    if not crud.get_by_id(db, models.Category, "category_id", payload.category_id):
        raise HTTPException(status_code=400, detail="category_id не найден.")
    if not crud.get_by_id(db, models.User, "user_id", payload.created_by):
        raise HTTPException(status_code=400, detail="created_by не найден.")
    return crud.create_dataset(db, payload)


@app.post("/datasets/{dataset_id}/versions", response_model=schemas.VersionRead, status_code=201)
def create_version(dataset_id: int, payload: schemas.VersionCreate, db: Session = Depends(get_db)) -> models.DatasetVersion:
    if not crud.get_by_id(db, models.DatasetStatus, "status_id", payload.status_id):
        raise HTTPException(status_code=400, detail="status_id не найден.")
    if not crud.get_by_id(db, models.AccessLevel, "access_level_id", payload.access_level_id):
        raise HTTPException(status_code=400, detail="access_level_id не найден.")
    if payload.source_id and not crud.get_by_id(db, models.DataSource, "source_id", payload.source_id):
        raise HTTPException(status_code=400, detail="source_id не найден.")
    try:
        version = crud.create_version(db, dataset_id, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Версия с таким номером уже существует для набора данных.")
    if not version:
        raise HTTPException(status_code=404, detail="Набор данных не найден.")
    return version


@app.post("/versions/{version_id}/make-current", response_model=schemas.VersionRead)
def make_version_current(version_id: int, db: Session = Depends(get_db)) -> models.DatasetVersion:
    version = crud.set_current_version(db, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Версия не найдена.")
    return version


@app.post("/versions/{version_id}/metadata", response_model=schemas.MetadataRead)
def upsert_metadata(
    version_id: int,
    payload: schemas.MetadataUpsert,
    db: Session = Depends(get_db),
) -> models.DatasetMetadata:
    if payload.license_id and not crud.get_by_id(db, models.License, "license_id", payload.license_id):
        raise HTTPException(status_code=400, detail="license_id не найден.")
    metadata = crud.upsert_metadata(db, version_id, payload)
    if not metadata:
        raise HTTPException(status_code=404, detail="Версия не найдена.")
    return metadata


@app.post("/versions/{version_id}/files", response_model=schemas.FileUploadResponse, status_code=201)
async def upload_dataset_file(
    version_id: int,
    file: UploadFile = File(...),
    uploaded_by: int | None = Form(None),
    is_primary: bool = Form(True),
    db: Session = Depends(get_db),
) -> schemas.FileUploadResponse:
    if uploaded_by and not crud.get_by_id(db, models.User, "user_id", uploaded_by):
        raise HTTPException(status_code=400, detail="uploaded_by не найден.")
    result = await crud.save_and_validate_file(db, version_id, uploaded_by, file, is_primary)
    if not result:
        raise HTTPException(status_code=404, detail="Версия не найдена.")
    dataset_file, validation = result
    return schemas.FileUploadResponse(
        file=schemas.DatasetFileRead.model_validate(dataset_file),
        validation=schemas.ValidationResultRead.model_validate(validation),
    )


@app.post("/files/{file_id}/import-observations", response_model=schemas.ImportResponse)
def import_observations(file_id: int, db: Session = Depends(get_db)) -> schemas.ImportResponse:
    result = crud.import_observations_from_file(db, file_id)
    if not result:
        raise HTTPException(status_code=404, detail="Файл не найден.")
    imported_count, skipped_count, validation = result
    return schemas.ImportResponse(
        imported_count=imported_count,
        skipped_count=skipped_count,
        validation=schemas.ValidationResultRead.model_validate(validation),
    )


@app.get("/datasets/{dataset_id}", response_model=schemas.DatasetDetail)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)) -> schemas.DatasetDetail:
    dataset = crud.get_dataset_detail(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Набор данных не найден.")
    return dataset


def _require_admin(user_id: int | None, db: Session) -> None:
    if not crud.user_has_role(db, user_id, "admin"):
        raise HTTPException(status_code=403, detail="Операция доступна только администратору.")


@app.delete("/datasets/{dataset_id}", response_model=schemas.DeleteResponse)
def delete_dataset(
    dataset_id: int,
    user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> schemas.DeleteResponse:
    _require_admin(user_id, db)
    deleted = crud.delete_dataset(db, dataset_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Набор данных не найден.")
    return schemas.DeleteResponse(status="ok", message="Набор данных удален.")


@app.delete("/versions/{version_id}", response_model=schemas.DeleteResponse)
def delete_version(
    version_id: int,
    user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> schemas.DeleteResponse:
    _require_admin(user_id, db)
    deleted = crud.delete_dataset_version(db, version_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Версия не найдена.")
    return schemas.DeleteResponse(status="ok", message="Версия удалена.")


@app.delete("/files/{file_id}", response_model=schemas.DeleteResponse)
def delete_file(
    file_id: int,
    user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> schemas.DeleteResponse:
    _require_admin(user_id, db)
    deleted = crud.delete_dataset_file(db, file_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Файл не найден.")
    return schemas.DeleteResponse(status="ok", message="Файл удален.")


@app.get("/versions/{version_id}/observations")
def get_observations(
    version_id: int,
    region_id: int | None = None,
    agro_object_id: int | None = None,
    indicator_id: int | None = None,
    period_year: int | None = None,
    db: Session = Depends(get_db),
):
    if not crud.get_by_id(db, models.DatasetVersion, "version_id", version_id):
        raise HTTPException(status_code=404, detail="Версия не найдена.")
    return crud.list_observations(
        db,
        version_id=version_id,
        region_id=region_id,
        agro_object_id=agro_object_id,
        indicator_id=indicator_id,
        period_year=period_year,
    )


@app.get("/files/{file_id}/download")
def download_file(
    file_id: int,
    user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> FileResponse:
    result = crud.get_downloadable_file(db, file_id=file_id, user_id=user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Файл не найден.")
    dataset_file, path = result
    if not path.exists():
        raise HTTPException(status_code=404, detail="Файл отсутствует в storage.")
    return FileResponse(path=path, filename=dataset_file.file_name)


@app.get("/versions/{version_id}/export-observations")
def export_observations(
    version_id: int,
    user_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> FileResponse:
    path = crud.export_observations_to_csv(db, version_id=version_id, user_id=user_id)
    if not path:
        raise HTTPException(status_code=404, detail="Версия не найдена.")
    return FileResponse(path=path, filename=path.name, media_type="text/csv")


@app.get("/exports", response_model=list[schemas.ExportRead])
def list_exports(db: Session = Depends(get_db)) -> list[models.DataExport]:
    return db.scalars(select(models.DataExport).order_by(models.DataExport.requested_at.desc())).all()


@app.get("/exports/detailed")
def list_exports_detailed(db: Session = Depends(get_db)):
    return crud.list_exports_detailed(db)
