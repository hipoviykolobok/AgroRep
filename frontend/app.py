from __future__ import annotations

import os
from typing import Any

import pandas as pd
import requests
import streamlit as st


API_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
DISPLAY_TIMEZONE = "Europe/Moscow"
DATETIME_KEYS = {
    "created_at",
    "updated_at",
    "published_at",
    "uploaded_at",
    "checked_at",
    "requested_at",
}
FIELD_LABELS = {
    "dataset_id": "ID набора",
    "title": "Название",
    "description": "Описание",
    "category_id": "ID категории",
    "category_name": "Категория",
    "current_version_id": "ID текущей версии",
    "version_id": "ID версии",
    "version_number": "Версия",
    "status": "Статус",
    "access_level": "Уровень доступа",
    "source": "Источник",
    "source_name": "Источник",
    "is_current": "Текущая",
    "observations_count": "Количество наблюдений",
    "datasets_count": "Наборов данных",
    "versions_count": "Версий",
    "files_count": "Файлов",
    "exports_count": "Экспортов",
    "validation_errors_count": "Ошибок проверки",
    "versions_by_status": "Версии по статусам",
    "count": "Количество",
    "created_at": "Создано",
    "updated_at": "Обновлено",
    "published_at": "Опубликовано",
    "metadata_id": "ID метаданных",
    "annotation": "Аннотация",
    "methodology": "Методика",
    "temporal_coverage": "Временной охват",
    "spatial_coverage": "Территориальное покрытие",
    "license": "Лицензия",
    "license_id": "ID лицензии",
    "quality_note": "Заметка о качестве",
    "citation": "Цитирование",
    "file_id": "ID файла",
    "file_name": "Имя файла",
    "display_file_name": "Имя файла",
    "format": "Формат",
    "format_id": "ID формата",
    "file_size": "Размер файла",
    "file_size_readable": "Размер",
    "checksum": "Контрольная сумма",
    "uploaded_by": "Кем загружен",
    "uploaded_at": "Загружено",
    "is_primary": "Основной файл",
    "validation_status": "Статус проверки",
    "validation_message": "Сообщение проверки",
    "validation_id": "ID проверки",
    "checked_at": "Проверено",
    "rows_checked": "Строк проверено",
    "errors_count": "Количество ошибок",
    "message": "Сообщение",
    "errors": "Ошибки",
    "error_id": "ID ошибки",
    "row_number": "Номер строки",
    "column_name": "Колонка",
    "error_type": "Тип ошибки",
    "error_message": "Описание ошибки",
    "imported_count": "Импортировано строк",
    "skipped_count": "Пропущено строк",
    "validation": "Результат проверки",
    "file": "Файл",
    "export_id": "ID экспорта",
    "requested_at": "Дата экспорта",
    "user_id": "ID пользователя",
    "user_name": "Пользователь",
    "dataset_title": "Набор данных",
    "export_scope": "Что экспортировано",
    "export_format": "Формат экспорта",
    "export_status": "Статус экспорта",
    "observation_id": "ID наблюдения",
    "source_file_id": "ID исходного файла",
    "region_id": "ID региона",
    "region_name": "Регион",
    "agro_object_id": "ID агрообъекта",
    "agro_object_name": "Агрообъект",
    "indicator_id": "ID показателя",
    "indicator_name": "Показатель",
    "measurement_unit_id": "ID единицы измерения",
    "unit_symbol": "Единица измерения",
    "period_year": "Год",
    "value_numeric": "Числовое значение",
    "value_sum": "Сумма значений",
    "value_text": "Текстовое значение",
    "object_type": "Тип объекта",
}
TABLE_COLUMNS = {
    "catalog": [
        "title",
        "description",
        "category_name",
        "version_number",
        "status",
        "access_level",
        "source",
        "observations_count",
        "created_at",
        "updated_at",
    ],
    "observations": [
        "region_name",
        "agro_object_name",
        "indicator_name",
        "unit_symbol",
        "period_year",
        "value_numeric",
        "value_text",
        "created_at",
    ],
    "files": [
        "display_file_name",
        "format",
        "file_size_readable",
        "uploaded_at",
        "is_primary",
        "validation_status",
        "errors_count",
    ],
    "exports": [
        "requested_at",
        "user_name",
        "dataset_title",
        "version_number",
        "file_name",
        "export_scope",
        "export_format",
        "export_status",
    ],
    "status_counts": [
        "status",
        "count",
    ],
    "versions": [
        "version_number",
        "is_current",
        "status",
        "access_level",
        "source",
        "observations_count",
        "files_count",
        "created_at",
        "published_at",
        "change_note",
    ],
}
HIDDEN_TABLE_COLUMNS = {
    "dataset_id",
    "category_id",
    "current_version_id",
    "version_id",
    "metadata_id",
    "license_id",
    "file_id",
    "format_id",
    "uploaded_by",
    "validation_id",
    "error_id",
    "export_id",
    "user_id",
    "source_file_id",
    "region_id",
    "agro_object_id",
    "indicator_id",
    "measurement_unit_id",
}
VALUE_LABELS = {
    "status": {
        "draft": "черновик",
        "uploaded": "загружено",
        "validation_failed": "ошибка проверки",
        "on_moderation": "на модерации",
        "published": "опубликовано",
        "rejected": "отклонено",
        "archived": "в архиве",
        "success": "успешно",
        "failed": "ошибка",
    },
    "validation_status": {
        "success": "успешно",
        "failed": "ошибка",
    },
    "export_status": {
        "success": "успешно",
        "failed": "ошибка",
    },
    "access_level": {
        "public": "открытый",
        "registered": "для зарегистрированных",
        "restricted": "ограниченный",
        "private": "приватный",
    },
    "export_scope": {
        "source_file": "исходный файл",
        "observations": "наблюдения",
        "metadata": "метаданные",
    },
    "is_current": {
        True: "да",
        False: "нет",
    },
    "is_primary": {
        True: "да",
        False: "нет",
    },
}
CREATION_FLOW_STEPS = [
    "Набор данных",
    "Версия",
    "Метаданные",
    "Файл",
    "Импорт наблюдений",
    "Проверка результата",
]
CREATION_FLOW_KEYS = [
    "creation_step",
    "creation_dataset_id",
    "creation_dataset_title",
    "creation_version_id",
    "creation_version_label",
    "creation_file_id",
    "creation_flow_message",
]


st.set_page_config(page_title="Репозиторий агроданных MVP", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --repo-border: rgba(120, 132, 153, 0.24);
        --repo-muted: #64748b;
        --repo-soft: rgba(15, 118, 110, 0.08);
    }

    .block-container {
        padding-top: 3rem;
        padding-bottom: 2.5rem;
    }

    .repo-page-title {
        font-size: 1.65rem;
        font-weight: 720;
        margin: 0 0 0.2rem 0;
        letter-spacing: 0;
        line-height: 1.25;
    }

    .repo-page-caption {
        color: var(--repo-muted);
        font-size: 0.96rem;
        margin: 0 0 1.2rem 0;
        line-height: 1.45;
    }

    .repo-panel {
        border: 1px solid var(--repo-border);
        border-radius: 8px;
        padding: 1rem 1.05rem;
        margin: 0.6rem 0 1rem 0;
        background: rgba(255, 255, 255, 0.02);
    }

    .repo-section-title {
        font-size: 1.05rem;
        font-weight: 700;
        margin: 0 0 0.6rem 0;
    }

    .repo-muted {
        color: var(--repo-muted);
    }

    div[data-testid="stMetric"] {
        border: 1px solid var(--repo-border);
        border-radius: 8px;
        padding: 0.85rem 0.95rem;
        background: rgba(255, 255, 255, 0.025);
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--repo-border);
        border-radius: 8px;
        overflow: hidden;
    }

    .stButton > button,
    .stDownloadButton > button,
    div[data-testid="stFormSubmitButton"] > button {
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def format_api_error(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text or str(response.status_code)

    detail = payload.get("detail", payload)
    if isinstance(detail, list):
        messages = []
        for item in detail:
            location = ".".join(str(part) for part in item.get("loc", []))
            message = item.get("msg", item)
            messages.append(f"{location}: {message}" if location else str(message))
        return "; ".join(messages)
    return str(detail)


def api_get(path: str, **params):
    response = requests.get(f"{API_URL}{path}", params={k: v for k, v in params.items() if v not in [None, "", 0]})
    if not response.ok:
        raise RuntimeError(format_api_error(response))
    return response.json()


def api_post(path: str, json: dict | None = None, files: dict | None = None, data: dict | None = None):
    response = requests.post(f"{API_URL}{path}", json=json, files=files, data=data)
    if not response.ok:
        raise RuntimeError(format_api_error(response))
    return response.json()


def api_delete(path: str, **params):
    response = requests.delete(f"{API_URL}{path}", params={k: v for k, v in params.items() if v not in [None, "", 0]})
    if not response.ok:
        raise RuntimeError(format_api_error(response))
    return response.json()


def page_header(title: str, caption: str | None = None) -> None:
    st.markdown(f'<div class="repo-page-title">{title}</div>', unsafe_allow_html=True)
    if caption:
        st.markdown(f'<div class="repo-page-caption">{caption}</div>', unsafe_allow_html=True)


def section_title(title: str) -> None:
    st.markdown(f'<div class="repo-section-title">{title}</div>', unsafe_allow_html=True)


def format_file_size(value: Any) -> str:
    try:
        size = int(value or 0)
    except (TypeError, ValueError):
        return "-"
    if size < 1024:
        return f"{size} Б"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} КБ"
    return f"{size / (1024 * 1024):.1f} МБ"


def format_datetime(value: Any) -> str:
    if value in [None, ""]:
        return "-"
    try:
        timestamp = pd.to_datetime(value, utc=True)
        return timestamp.tz_convert(DISPLAY_TIMEZONE).strftime("%d.%m.%Y %H:%M")
    except Exception:
        return str(value)


def format_value(key: str, value: Any) -> Any:
    if key in VALUE_LABELS:
        return VALUE_LABELS[key].get(value, value)
    return value


def format_nested_datetimes(value: Any) -> Any:
    if isinstance(value, list):
        return [format_nested_datetimes(item) for item in value]
    if isinstance(value, dict):
        formatted = {}
        for key, item in value.items():
            formatted[key] = format_datetime(item) if key in DATETIME_KEYS else format_nested_datetimes(item)
        return formatted
    return value


def localize_payload(value: Any) -> Any:
    if isinstance(value, list):
        return [localize_payload(item) for item in value]
    if isinstance(value, dict):
        localized = {}
        for key, item in value.items():
            label = FIELD_LABELS.get(key, key)
            localized[label] = localize_payload(format_value(key, item))
        return localized
    return value


def format_table(rows: list[dict[str, Any]], table_name: str | None = None) -> pd.DataFrame:
    dataframe = pd.DataFrame(rows)
    if dataframe.empty:
        return dataframe
    if "file_size" in dataframe.columns and "file_size_readable" not in dataframe.columns:
        dataframe["file_size_readable"] = dataframe["file_size"].map(format_file_size)
    for column in dataframe.columns:
        if column in DATETIME_KEYS:
            dataframe[column] = dataframe[column].map(format_datetime)
        elif column in VALUE_LABELS:
            dataframe[column] = dataframe[column].map(lambda item, key=column: format_value(key, item))
    hidden_columns = [column for column in HIDDEN_TABLE_COLUMNS if column in dataframe.columns]
    if hidden_columns:
        dataframe = dataframe.drop(columns=hidden_columns)
    if table_name in TABLE_COLUMNS:
        columns = [column for column in TABLE_COLUMNS[table_name] if column in dataframe.columns]
        dataframe = dataframe[columns]
    dataframe = dataframe.rename(columns={column: FIELD_LABELS.get(column, column) for column in dataframe.columns})
    return dataframe


def make_options(items: list[dict[str, Any]], label_key: str, value_key: str) -> dict[str, int]:
    labels_seen: dict[str, int] = {}
    result: dict[str, int] = {}
    for item in items:
        base_label = str(item.get(label_key) or f"ID {item[value_key]}")
        labels_seen[base_label] = labels_seen.get(base_label, 0) + 1
        label = base_label
        if labels_seen[base_label] > 1:
            label = f"{base_label} ({labels_seen[base_label]})"
        result[label] = item[value_key]
    return result


def option_map(items: list[dict[str, Any]], id_key: str, label_key: str) -> dict[str, int]:
    return {item[label_key]: item[id_key] for item in items}


def select_reference(
    label: str,
    items: list[dict[str, Any]],
    id_key: str,
    label_key: str,
    include_all: bool = False,
    key: str | None = None,
):
    labels = ["Все"] if include_all else []
    labels += [item[label_key] for item in items]
    selected = st.selectbox(label, labels, key=key)
    if selected == "Все":
        return None
    return option_map(items, id_key, label_key)[selected]


def load_references():
    try:
        return api_get("/references")
    except Exception as exc:
        st.error(f"Backend недоступен или справочники не созданы: {exc}")
        return None


def current_versions_from_catalog(datasets: list[dict[str, Any]]) -> dict[str, int]:
    version_items = [
        {
            "label": f"{item['title']} / версия {item['version_number']}",
            "version_id": item["current_version_id"],
        }
        for item in datasets
        if item.get("current_version_id")
    ]
    return make_options(version_items, "label", "version_id")


def option_index_by_value(options: dict[str, int], value: int | None) -> int:
    values = list(options.values())
    if value in values:
        return values.index(value)
    return 0


def go_to_page(page: str, **state: Any) -> None:
    st.session_state.pop("next_action", None)
    for key, value in state.items():
        st.session_state[key] = value
    st.session_state.page = page
    st.rerun()


def next_page_button(label: str, page: str, key: str, **state: Any) -> None:
    st.session_state.next_action = {
        "label": label,
        "page": page,
        "state": state,
    }


def render_next_action(key: str) -> None:
    action = st.session_state.get("next_action")
    if not action:
        return

    st.info("Доступен следующий шаг сценария.")
    if st.button(action["label"], key=key):
        page = action["page"]
        state = action.get("state", {})
        go_to_page(page, **state)


def clear_creation_flow() -> None:
    for key in CREATION_FLOW_KEYS:
        st.session_state.pop(key, None)
    st.rerun()


def advance_creation_flow(step: int, message: str) -> None:
    st.session_state.creation_step = step
    st.session_state.creation_flow_message = message
    st.rerun()


def render_creation_progress() -> None:
    current_step = int(st.session_state.get("creation_step", 0))
    labels = []
    for index, title in enumerate(CREATION_FLOW_STEPS):
        if index < current_step:
            labels.append(f"✓ {title}")
        elif index == current_step:
            labels.append(f"→ {title}")
        else:
            labels.append(title)
    st.caption(" / ".join(labels))

    message = st.session_state.pop("creation_flow_message", None)
    if message:
        st.success(message)


def is_admin_user() -> bool:
    return "admin" in st.session_state.get("user", {}).get("roles", [])


def display_validation_result(validation: dict[str, Any], title: str = "Результат проверки") -> None:
    st.subheader(title)
    status = format_value("status", validation.get("status"))
    col1, col2, col3 = st.columns(3)
    col1.metric("Статус", status or "-")
    col2.metric("Проверено строк", validation.get("rows_checked", 0))
    col3.metric("Ошибок", validation.get("errors_count", 0))
    if validation.get("message"):
        st.write(validation["message"])

    errors = validation.get("errors") or []
    if errors:
        st.write("Ошибки проверки")
        st.dataframe(format_table(errors), use_container_width=True, hide_index=True)


def dashboard_page():
    page_header(
        "Обзор репозитория",
        "Краткое состояние MVP: сколько наборов и версий создано, сколько наблюдений импортировано и какие выгрузки уже зафиксированы.",
    )
    stats = api_get("/dashboard")
    datasets = api_get("/catalog/datasets")
    exports = api_get("/exports/detailed")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Наборов", stats["datasets_count"])
    col2.metric("Версий", stats["versions_count"])
    col3.metric("Файлов", stats["files_count"])
    col4.metric("Наблюдений", stats["observations_count"])
    col5.metric("Экспортов", stats["exports_count"])

    if stats.get("validation_errors_count"):
        st.warning(f"В журнале проверок есть ошибки: {stats['validation_errors_count']}")

    left, right = st.columns(2)
    with left:
        section_title("Версии по статусам")
        st.dataframe(format_table(stats.get("versions_by_status", []), "status_counts"), use_container_width=True, hide_index=True)
    with right:
        section_title("Последние наборы")
        st.dataframe(format_table(datasets[:5], "catalog"), use_container_width=True, hide_index=True)

    section_title("Последние экспорты")
    if exports:
        st.dataframe(format_table(exports[:5], "exports"), use_container_width=True, hide_index=True)
    else:
        st.info("Экспортов пока не было.")


def chart_from_rows(rows: list[dict[str, Any]], label_key: str, value_key: str, title: str) -> None:
    section_title(title)
    if not rows:
        st.info("Данных для диаграммы пока нет.")
        return
    dataframe = pd.DataFrame(rows)
    dataframe = dataframe.rename(columns={label_key: "Показатель", value_key: "Значение"})
    st.bar_chart(dataframe, x="Показатель", y="Значение", use_container_width=True)


def analytics_page():
    page_header(
        "Аналитика",
        "Простые диаграммы по уже импортированному аналитическому слою observations. Они помогают показать, зачем репозиторию нужны структурированные наблюдения.",
    )
    analytics = api_get("/analytics")

    top1, top2 = st.columns(2)
    with top1:
        chart_from_rows(
            analytics.get("datasets_by_category", []),
            "category_name",
            "count",
            "Наборы данных по категориям",
        )
    with top2:
        chart_from_rows(
            analytics.get("observations_by_region", []),
            "region_name",
            "count",
            "Наблюдения по регионам",
        )

    bottom1, bottom2 = st.columns(2)
    with bottom1:
        chart_from_rows(
            analytics.get("observations_by_indicator", []),
            "indicator_name",
            "count",
            "Наблюдения по показателям",
        )
    with bottom2:
        chart_from_rows(
            analytics.get("observations_by_agro_object", []),
            "agro_object_name",
            "count",
            "Наблюдения по агрообъектам",
        )

    section_title("Сумма числовых значений по показателям")
    value_rows = analytics.get("value_sum_by_indicator", [])
    if value_rows:
        value_table = pd.DataFrame(value_rows).rename(
            columns={
                "indicator_name": "Показатель",
                "value_numeric": "Сумма значений",
            }
        )
        st.dataframe(value_table, use_container_width=True, hide_index=True)
    else:
        st.info("Числовых значений для сводной таблицы пока нет.")


def login_page():
    page_header(
        "Репозиторий сельскохозяйственных данных",
        "MVP-прототип для загрузки, проверки, описания и экспорта аграрных наборов данных.",
    )
    with st.form("login_form"):
        email = st.text_input("Email", value="admin@example.com")
        password = st.text_input("Password", type="password", value="admin123")
        submitted = st.form_submit_button("Войти")
    if submitted:
        try:
            user = api_post("/auth/login", json={"email": email, "password": password})
            st.session_state.user = user
            st.success(f"Вход выполнен: {user['full_name']}")
            st.rerun()
        except Exception as exc:
            st.error(f"Не удалось войти: {exc}")

    if st.button("Заполнить справочники и demo-пользователей"):
        try:
            result = api_post("/seed")
            st.success(result["message"])
        except Exception as exc:
            st.error(f"Seed не выполнен: {exc}")


def catalog_page(refs: dict[str, Any]):
    page_header(
        "Каталог данных",
        "Поиск по карточкам наборов и фильтрация по текущей версии, справочникам и импортированным наблюдениям.",
    )
    with st.expander("Фильтры каталога", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            q = st.text_input("Поиск по названию")
            category_id = select_reference("Категория", refs["categories"], "category_id", "category_name", include_all=True)
        with col2:
            status_options = ["Все"] + [format_value("status", item["status_name"]) for item in refs["statuses"]]
            status_lookup = {format_value("status", item["status_name"]): item["status_name"] for item in refs["statuses"]}
            status = st.selectbox("Статус", status_options)
            region_id = select_reference("Регион", refs["regions"], "region_id", "region_name", include_all=True)
        with col3:
            agro_object_id = select_reference("Агрообъект", refs["agro_objects"], "agro_object_id", "object_name", include_all=True)
            indicator_id = select_reference("Показатель", refs["indicators"], "indicator_id", "indicator_name", include_all=True)

    datasets = api_get(
        "/catalog/datasets",
        q=q,
        category_id=category_id,
        status=None if status == "Все" else status_lookup[status],
        region_id=region_id,
        agro_object_id=agro_object_id,
        indicator_id=indicator_id,
    )
    st.caption(f"Найдено наборов: {len(datasets)}")
    st.dataframe(format_table(datasets, "catalog"), use_container_width=True, hide_index=True)

    if datasets:
        dataset_map = make_options(datasets, "title", "dataset_id")
        selected = st.selectbox("Открыть карточку", list(dataset_map))
        if st.button("Открыть"):
            st.session_state.selected_dataset_id = dataset_map[selected]
            st.session_state.page = "Карточка набора данных"
            st.rerun()


def create_dataset_page(refs: dict[str, Any]):
    page_header(
        "Создание набора данных",
        "Пошаговое создание полного набора: карточка, версия, метаданные, файл, импорт наблюдений и проверка результата.",
    )
    st.session_state.setdefault("creation_step", 0)
    render_creation_progress()

    dataset_id = st.session_state.get("creation_dataset_id")
    version_id = st.session_state.get("creation_version_id")
    file_id = st.session_state.get("creation_file_id")
    step = int(st.session_state.get("creation_step", 0))

    control_left, control_right = st.columns([1, 3])
    with control_left:
        if st.button("Начать заново", key="restart_creation_flow"):
            clear_creation_flow()
    with control_right:
        if dataset_id:
            st.caption(f"Текущий сценарий: {st.session_state.get('creation_dataset_title', 'набор данных')}")

    if step == 0:
        section_title("Шаг 1. Набор данных")
        with st.form("create_dataset_wizard"):
            title = st.text_input("Название")
            description = st.text_area("Описание")
            category_id = select_reference(
                "Категория",
                refs["categories"],
                "category_id",
                "category_name",
                key="wizard_dataset_category",
            )
            submitted = st.form_submit_button("Создать набор и перейти к версии")
        if submitted:
            title = title.strip()
            description = description.strip() or None
            if not title:
                st.warning("Укажите название набора данных.")
                return
            try:
                payload = {
                    "title": title,
                    "description": description,
                    "category_id": category_id,
                    "created_by": st.session_state.user["user_id"],
                }
                result = api_post("/datasets", json=payload)
                st.session_state.creation_dataset_id = result["dataset_id"]
                st.session_state.creation_dataset_title = result["title"]
                st.session_state.selected_dataset_id = result["dataset_id"]
                advance_creation_flow(1, f"Набор создан: {result['title']}.")
            except Exception as exc:
                st.error(f"Не удалось создать набор: {exc}")

    elif step == 1:
        if not dataset_id:
            st.warning("Сначала создайте набор данных.")
            st.session_state.creation_step = 0
            st.rerun()
        section_title("Шаг 2. Версия")
        st.write("Версия будет создана для выбранного набора данных.")
        with st.form("create_version_wizard"):
            version_number = st.text_input("Номер версии", value="1.0")
            source_id = select_reference("Источник", refs["sources"], "source_id", "source_name", key="wizard_version_source")
            access_map = {
                format_value("access_level", item["access_level_name"]): item["access_level_id"]
                for item in refs["access_levels"]
            }
            status_map = {
                format_value("status", item["status_name"]): item["status_id"]
                for item in refs["statuses"]
            }
            access_level_id = access_map[st.selectbox("Уровень доступа", list(access_map), key="wizard_access_level")]
            status_id = status_map[st.selectbox("Статус", list(status_map), key="wizard_status")]
            change_note = st.text_area("Комментарий изменений", value="Первичная версия набора.")
            submitted = st.form_submit_button("Создать версию и перейти к метаданным")
        if submitted:
            try:
                payload = {
                    "version_number": version_number,
                    "status_id": status_id,
                    "access_level_id": access_level_id,
                    "source_id": source_id,
                    "change_note": change_note,
                }
                result = api_post(f"/datasets/{dataset_id}/versions", json=payload)
                st.session_state.creation_version_id = result["version_id"]
                st.session_state.creation_version_label = f"{st.session_state.creation_dataset_title} / версия {result['version_number']}"
                advance_creation_flow(2, f"Версия создана: {result['version_number']}.")
            except Exception as exc:
                st.error(f"Не удалось создать версию: {exc}")

    elif step == 2:
        if not version_id:
            st.warning("Сначала создайте версию.")
            st.session_state.creation_step = 1
            st.rerun()
        section_title("Шаг 3. Метаданные")
        with st.form("metadata_wizard"):
            annotation = st.text_area("Аннотация")
            methodology = st.text_area("Методика")
            spatial_coverage = st.text_input("Территориальное покрытие")
            temporal_coverage = st.text_input("Временной охват")
            license_id = select_reference("Лицензия", refs["licenses"], "license_id", "license_name", key="wizard_license")
            quality_note = st.text_area("Заметка о качестве")
            citation = st.text_area("Цитирование")
            submitted = st.form_submit_button("Сохранить метаданные и перейти к файлу")
        if submitted:
            try:
                payload = {
                    "annotation": annotation,
                    "methodology": methodology,
                    "temporal_coverage": temporal_coverage,
                    "spatial_coverage": spatial_coverage,
                    "license_id": license_id,
                    "quality_note": quality_note,
                    "citation": citation,
                }
                api_post(f"/versions/{version_id}/metadata", json=payload)
                advance_creation_flow(3, "Метаданные версии сохранены.")
            except Exception as exc:
                st.error(f"Не удалось сохранить метаданные: {exc}")

    elif step == 3:
        if not version_id:
            st.warning("Сначала создайте версию.")
            st.session_state.creation_step = 1
            st.rerun()
        section_title("Шаг 4. Файл")
        uploaded = st.file_uploader("CSV/XLSX файл", type=["csv", "xlsx"], key="wizard_file_upload")
        if st.button("Загрузить файл и перейти к импорту", key="wizard_upload_file"):
            if not uploaded:
                st.warning("Выберите файл для загрузки.")
                return
            try:
                files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type or "application/octet-stream")}
                data = {"uploaded_by": str(st.session_state.user["user_id"]), "is_primary": "true"}
                result = api_post(f"/versions/{version_id}/files", files=files, data=data)
                st.session_state.creation_file_id = result["file"]["file_id"]
                st.session_state.last_uploaded_file_id = result["file"]["file_id"]
                if result.get("duplicate_message"):
                    st.warning(result["duplicate_message"])
                display_validation_result(result["validation"], "Проверка загруженного файла")
                advance_creation_flow(4, "Файл загружен и проверен.")
            except Exception as exc:
                st.error(f"Не удалось загрузить файл: {exc}")

    elif step == 4:
        if not file_id:
            st.warning("Сначала загрузите файл.")
            st.session_state.creation_step = 3
            st.rerun()
        section_title("Шаг 5. Импорт наблюдений")
        st.write("Импорт переносит проверенный файл в аналитический слой observations.")
        if st.button("Импортировать наблюдения и проверить результат", key="wizard_import_observations"):
            try:
                result = api_post(f"/files/{file_id}/import-observations")
                display_validation_result(result["validation"], "Проверка импорта наблюдений")
                advance_creation_flow(5, f"Импортировано строк: {result['imported_count']}.")
            except Exception as exc:
                st.error(f"Не удалось импортировать наблюдения: {exc}")

    else:
        if not dataset_id:
            st.warning("Сначала создайте набор данных.")
            st.session_state.creation_step = 0
            st.rerun()
        section_title("Шаг 6. Проверка результата")
        detail = api_get(f"/datasets/{dataset_id}")
        col1, col2, col3 = st.columns(3)
        current_version = detail.get("current_version")
        col1.metric("Набор данных", detail["title"])
        col2.metric("Текущая версия", current_version.get("version_number") if current_version else "-")
        col3.metric("Наблюдений", detail["observations_count"])
        action1, action2 = st.columns(2)
        if action1.button("Открыть карточку набора", key="wizard_open_dataset_card"):
            go_to_page("Карточка набора данных", selected_dataset_id=dataset_id)
        if action2.button("Создать еще один набор", key="wizard_create_another_dataset"):
            clear_creation_flow()


def create_version_page(refs: dict[str, Any]):
    page_header(
        "Создание версии",
        "Версия фиксирует изменяемое состояние набора: статус, уровень доступа, источник, файлы и метаданные.",
    )
    datasets = api_get("/catalog/datasets")
    if not datasets:
        st.info("Сначала создайте набор данных.")
        return
    dataset_map = make_options(datasets, "title", "dataset_id")
    default_dataset_id = st.session_state.get("creation_dataset_id") or st.session_state.get("selected_dataset_id")
    default_dataset_index = option_index_by_value(dataset_map, default_dataset_id)
    with st.form("create_version"):
        dataset_label = st.selectbox("Набор данных", list(dataset_map), index=default_dataset_index)
        dataset_id = dataset_map[dataset_label]
        version_number = st.text_input("Номер версии", value="1.0")
        source_id = select_reference("Источник", refs["sources"], "source_id", "source_name")
        access_map = {
            format_value("access_level", item["access_level_name"]): item["access_level_id"]
            for item in refs["access_levels"]
        }
        status_map = {
            format_value("status", item["status_name"]): item["status_id"]
            for item in refs["statuses"]
        }
        access_level_id = access_map[st.selectbox("Уровень доступа", list(access_map))]
        status_id = status_map[st.selectbox("Статус", list(status_map))]
        change_note = st.text_area("Комментарий изменений")
        submitted = st.form_submit_button("Создать версию")
    if submitted:
        try:
            payload = {
                "version_number": version_number,
                "status_id": status_id,
                "access_level_id": access_level_id,
                "source_id": source_id,
                "change_note": change_note,
            }
            result = api_post(f"/datasets/{dataset_id}/versions", json=payload)
            st.session_state.creation_dataset_id = dataset_id
            st.session_state.creation_version_id = result["version_id"]
            st.session_state.creation_version_label = f"{dataset_label} / версия {result['version_number']}"
            st.success(f"Версия создана: {result['version_number']}")
            next_page_button(
                "Заполнить метаданные для этой версии",
                "Метаданные версии",
                "go_metadata_after_version_create",
                creation_version_id=result["version_id"],
            )
        except Exception as exc:
            st.error(f"Не удалось создать версию: {exc}")

    render_next_action("create_version_next_action")


def metadata_page(refs: dict[str, Any]):
    page_header(
        "Метаданные версии",
        "Описание методики, охвата, лицензии и качества хранится у конкретной версии набора данных.",
    )
    datasets = api_get("/catalog/datasets")
    version_map = current_versions_from_catalog(datasets)
    if not version_map:
        st.info("Нет версий для заполнения метаданных.")
        return
    default_version_index = option_index_by_value(version_map, st.session_state.get("creation_version_id"))
    with st.form("metadata"):
        version_label = st.selectbox("Версия", list(version_map), index=default_version_index)
        version_id = version_map[version_label]
        annotation = st.text_area("Аннотация")
        methodology = st.text_area("Методика")
        spatial_coverage = st.text_input("Территориальное покрытие")
        temporal_coverage = st.text_input("Временной охват")
        license_id = select_reference("Лицензия", refs["licenses"], "license_id", "license_name")
        quality_note = st.text_area("Заметка о качестве")
        citation = st.text_area("Цитирование")
        submitted = st.form_submit_button("Сохранить метаданные")
    if submitted:
        try:
            payload = {
                "annotation": annotation,
                "methodology": methodology,
                "temporal_coverage": temporal_coverage,
                "spatial_coverage": spatial_coverage,
                "license_id": license_id,
                "quality_note": quality_note,
                "citation": citation,
            }
            result = api_post(f"/versions/{version_id}/metadata", json=payload)
            st.session_state.creation_version_id = version_id
            st.session_state.creation_version_label = version_label
            st.success("Метаданные версии сохранены.")
            next_page_button(
                "Загрузить файл для этой версии",
                "Загрузка файла",
                "go_upload_after_metadata",
                creation_version_id=version_id,
            )
        except Exception as exc:
            st.error(f"Не удалось сохранить метаданные: {exc}")

    render_next_action("metadata_next_action")


def upload_page():
    page_header(
        "Загрузка файла",
        "Файл сохраняется в storage, получает checksum и проходит базовую проверку перед импортом в аналитический слой.",
    )
    datasets = api_get("/catalog/datasets")
    version_map = current_versions_from_catalog(datasets)
    if not version_map:
        st.info("Нет версий для загрузки файла.")
        return

    default_version_index = option_index_by_value(version_map, st.session_state.get("creation_version_id"))
    version_label = st.selectbox("Версия", list(version_map), index=default_version_index)
    version_id = version_map[version_label]
    dataset_id = next((item["dataset_id"] for item in datasets if item.get("current_version_id") == version_id), None)
    uploaded = st.file_uploader("CSV/XLSX файл", type=["csv", "xlsx"])
    if st.button("Загрузить и проверить") and uploaded:
        try:
            files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type or "application/octet-stream")}
            data = {"uploaded_by": str(st.session_state.user["user_id"]), "is_primary": "true"}
            result = api_post(f"/versions/{version_id}/files", files=files, data=data)
            st.session_state.last_uploaded_file_id = result["file"]["file_id"]
            st.session_state.creation_version_id = version_id
            st.session_state.creation_file_id = result["file"]["file_id"]
            if result.get("duplicate_message"):
                st.warning(result["duplicate_message"])
            display_validation_result(result["validation"], "Проверка загруженного файла")
            st.info("Теперь можно импортировать наблюдения из загруженного файла.")
        except Exception as exc:
            st.error(f"Не удалось загрузить файл: {exc}")

    file_id = st.session_state.get("last_uploaded_file_id")
    if file_id and st.button("Импортировать наблюдения"):
        try:
            result = api_post(f"/files/{file_id}/import-observations")
            st.success(f"Импортировано строк: {result['imported_count']}")
            display_validation_result(result["validation"], "Проверка импорта наблюдений")
            if dataset_id:
                next_page_button(
                    "Открыть карточку набора данных",
                    "Карточка набора данных",
                    "go_dataset_card_after_import",
                    selected_dataset_id=dataset_id,
                    creation_dataset_id=dataset_id,
                    creation_version_id=version_id,
                )
        except Exception as exc:
            st.error(f"Не удалось импортировать наблюдения: {exc}")

    render_next_action("upload_next_action")


def dataset_card_page():
    page_header(
        "Карточка набора данных",
        "Сводная страница набора: постоянная карточка, текущая версия, метаданные, файлы, наблюдения и экспорт.",
    )
    datasets = api_get("/catalog/datasets")
    if not datasets:
        st.info("Наборы данных пока не созданы.")
        return
    dataset_map = make_options(datasets, "title", "dataset_id")
    default_id = st.session_state.get("selected_dataset_id")
    default_label = next((label for label, value in dataset_map.items() if value == default_id), list(dataset_map)[0])
    selected = st.selectbox("Набор данных", list(dataset_map), index=list(dataset_map).index(default_label))
    dataset_id = dataset_map[selected]
    detail = api_get(f"/datasets/{dataset_id}")
    admin_mode = is_admin_user()

    st.subheader(detail["title"])
    summary1, summary2, summary3, summary4 = st.columns(4)
    summary1.metric("Категория", detail.get("category", {}).get("category_name") if detail.get("category") else "-")
    summary2.metric("Наблюдений", detail["observations_count"])
    summary3.metric("Файлов", len(detail.get("files", [])))
    current_version = detail.get("current_version")
    versions = detail.get("versions", [])
    summary4.metric("Текущая версия", current_version.get("version_number") if current_version else "-")

    general_tab, version_tab, files_tab, observations_tab = st.tabs(
        ["Общая информация", "Версия и метаданные", "Файлы и экспорт", "Наблюдения"]
    )

    with general_tab:
        section_title("Карточка набора")
        st.write(detail.get("description") or "Описание не заполнено.")
        info_rows = [
            {"Параметр": "Категория", "Значение": detail.get("category", {}).get("category_name") if detail.get("category") else "-"},
            {"Параметр": "Создан", "Значение": format_datetime(detail.get("created_at"))},
            {"Параметр": "Обновлен", "Значение": format_datetime(detail.get("updated_at"))},
            {"Параметр": "Количество наблюдений", "Значение": detail["observations_count"]},
        ]
        st.dataframe(pd.DataFrame(info_rows), use_container_width=True, hide_index=True)

        if admin_mode:
            with st.expander("Администрирование набора данных"):
                st.warning("Удаление набора удалит его версии, файлы, метаданные и наблюдения. Журнал экспортов сохранится без ссылок на удаленные объекты.")
                confirm_dataset_delete = st.text_input(
                    "Для удаления набора введите УДАЛИТЬ",
                    key=f"delete_dataset_confirm_{dataset_id}",
                )
                if st.button(
                    "Удалить набор данных",
                    key=f"delete_dataset_{dataset_id}",
                    disabled=confirm_dataset_delete != "УДАЛИТЬ",
                ):
                    try:
                        api_delete(f"/datasets/{dataset_id}", user_id=st.session_state.user["user_id"])
                        st.session_state.pop("selected_dataset_id", None)
                        st.session_state.page = "Каталог данных"
                        st.success("Набор данных удален.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Не удалось удалить набор данных: {exc}")

    with version_tab:
        if not current_version:
            st.info("У этого набора пока нет версии.")
        else:
            section_title("Текущая версия")
            version_rows = [
                {"Параметр": "Версия", "Значение": current_version.get("version_number")},
                {"Параметр": "Статус", "Значение": format_value("status", current_version.get("status")) or "-"},
                {"Параметр": "Источник", "Значение": current_version.get("source") or "-"},
                {"Параметр": "Уровень доступа", "Значение": format_value("access_level", current_version.get("access_level")) or "-"},
                {"Параметр": "Создана", "Значение": format_datetime(current_version.get("created_at"))},
                {"Параметр": "Опубликована", "Значение": format_datetime(current_version.get("published_at"))},
                {"Параметр": "Комментарий изменений", "Значение": current_version.get("change_note") or "-"},
            ]
            st.dataframe(pd.DataFrame(version_rows), use_container_width=True, hide_index=True)

        if versions:
            section_title("Все версии набора")
            st.dataframe(format_table(versions, "versions"), use_container_width=True, hide_index=True)
            version_options = {
                (
                    f"Версия {item.get('version_number') or '-'}"
                    f" - {item.get('observations_count', 0)} наблюдений"
                    f"{' - текущая' if item.get('is_current') else ''}"
                ): item["version_id"]
                for item in versions
            }
            selected_version_label = st.selectbox(
                "Версия для переключения",
                list(version_options),
                key=f"version_switch_select_{dataset_id}",
            )
            selected_version_id = version_options[selected_version_label]
            selected_version = next(item for item in versions if item["version_id"] == selected_version_id)
            if st.button(
                "Сделать выбранную версию текущей",
                key=f"make_current_version_{dataset_id}",
                disabled=bool(selected_version.get("is_current")),
                help="Переключает карточку набора, файлы, наблюдения и экспорт на выбранную сохраненную версию.",
            ):
                try:
                    result = api_post(f"/versions/{selected_version_id}/make-current")
                    st.success(f"Текущая версия изменена на {result['version_number']}.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Не удалось переключить версию: {exc}")

            if admin_mode:
                with st.expander("Удаление версии"):
                    st.warning("Удаление версии удалит ее файлы, метаданные, проверки и наблюдения. Если удалить текущую версию, текущей станет последняя оставшаяся версия набора.")
                    delete_version_options = {
                        (
                            f"Версия {item.get('version_number') or '-'}"
                            f"{' - текущая' if item.get('is_current') else ''}"
                        ): item["version_id"]
                        for item in versions
                    }
                    delete_version_label = st.selectbox(
                        "Версия для удаления",
                        list(delete_version_options),
                        key=f"version_delete_select_{dataset_id}",
                    )
                    delete_version_id = delete_version_options[delete_version_label]
                    confirm_version_delete = st.text_input(
                        "Для удаления версии введите УДАЛИТЬ ВЕРСИЮ",
                        key=f"delete_version_confirm_{delete_version_id}",
                    )
                    if st.button(
                        "Удалить выбранную версию",
                        key=f"delete_version_{delete_version_id}",
                        disabled=confirm_version_delete != "УДАЛИТЬ ВЕРСИЮ",
                    ):
                        try:
                            api_delete(f"/versions/{delete_version_id}", user_id=st.session_state.user["user_id"])
                            st.success("Версия удалена.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Не удалось удалить версию: {exc}")

        section_title("Метаданные")
        metadata = detail.get("metadata")
        if metadata:
            metadata_rows = [
                {"Параметр": FIELD_LABELS.get(key, key), "Значение": format_datetime(value) if key in DATETIME_KEYS else (value or "-")}
                for key, value in metadata.items()
                if key != "metadata_id"
            ]
            st.dataframe(pd.DataFrame(metadata_rows), use_container_width=True, hide_index=True)
        else:
            st.info("Метаданные для текущей версии пока не заполнены.")

    with files_tab:
        files = detail.get("files", [])
        if not files:
            st.info("К текущей версии пока не загружены файлы.")
        else:
            section_title("Файлы версии")
            st.dataframe(format_table(files, "files"), use_container_width=True, hide_index=True)
            file_map = make_options(files, "display_file_name", "file_id")
            selected_file = st.selectbox("Файл для скачивания", list(file_map))
            file_id = file_map[selected_file]
            selected_file_record = next(item for item in files if item["file_id"] == file_id)

            action1, action2 = st.columns(2)
            if action1.button(
                "Скачать исходный файл",
                key=f"download_{file_id}",
                help="Скачивает исходный CSV/XLSX-файл, который был загружен в репозиторий.",
            ):
                response = requests.get(
                    f"{API_URL}/files/{file_id}/download",
                    params={"user_id": st.session_state.user["user_id"]},
                )
                if response.ok:
                    st.download_button("Сохранить файл", response.content, file_name=selected_file_record["file_name"])
                else:
                    st.error(response.text)

            if current_version and action2.button(
                "Экспортировать наблюдения",
                key=f"export_{current_version['version_id']}",
                help=(
                    "Выгружает не исходный файл, а структурированные наблюдения из аналитического слоя: "
                    "регион, агрообъект, показатель, единица измерения, год и значение."
                ),
            ):
                response = requests.get(
                    f"{API_URL}/versions/{current_version['version_id']}/export-observations",
                    params={"user_id": st.session_state.user["user_id"]},
                )
                if response.ok:
                    st.download_button("Сохранить CSV", response.content, file_name="observations_export.csv")
                else:
                    st.error(response.text)

            if admin_mode:
                with st.expander("Удаление файла версии"):
                    st.warning("Удаление файла удалит связанные проверки и наблюдения, импортированные из этого файла.")
                    confirm_file_delete = st.text_input(
                        "Для удаления файла введите УДАЛИТЬ ФАЙЛ",
                        key=f"delete_file_confirm_{file_id}",
                    )
                    if st.button(
                        "Удалить выбранный файл",
                        key=f"delete_file_{file_id}",
                        disabled=confirm_file_delete != "УДАЛИТЬ ФАЙЛ",
                    ):
                        try:
                            api_delete(f"/files/{file_id}", user_id=st.session_state.user["user_id"])
                            st.success("Файл удален.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Не удалось удалить файл: {exc}")

    with observations_tab:
        if not current_version:
            st.info("Сначала создайте версию и импортируйте наблюдения.")
        else:
            rows = api_get(f"/versions/{current_version['version_id']}/observations")
            if not rows:
                st.info("В текущей версии пока нет импортированных наблюдений.")
            else:
                section_title("Первые строки аналитического слоя")
                st.dataframe(format_table(rows[:20], "observations"), use_container_width=True, hide_index=True)


def observations_page(refs: dict[str, Any]):
    page_header(
        "Наблюдения",
        "Просмотр аналитического слоя: регион, агрообъект, показатель, период и значение после импорта из файлов.",
    )
    datasets = api_get("/catalog/datasets")
    version_map = current_versions_from_catalog(datasets)
    if not version_map:
        st.info("Нет версий с наблюдениями.")
        return
    version_id = version_map[st.selectbox("Версия", list(version_map))]
    with st.expander("Фильтры наблюдений", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            region_id = select_reference("Регион", refs["regions"], "region_id", "region_name", include_all=True)
        with col2:
            agro_object_id = select_reference("Агрообъект", refs["agro_objects"], "agro_object_id", "object_name", include_all=True)
        with col3:
            indicator_id = select_reference("Показатель", refs["indicators"], "indicator_id", "indicator_name", include_all=True)
        with col4:
            period_year = st.number_input("Год", min_value=1900, max_value=2100, value=2024, step=1)
            use_year = st.checkbox("Фильтровать по году", value=False)

    rows = api_get(
        f"/versions/{version_id}/observations",
        region_id=region_id,
        agro_object_id=agro_object_id,
        indicator_id=indicator_id,
        period_year=period_year if use_year else None,
    )
    st.caption(f"Найдено наблюдений: {len(rows)}")
    st.dataframe(format_table(rows, "observations"), use_container_width=True, hide_index=True)


def exports_page():
    page_header(
        "Журнал экспортов",
        "Фиксация скачиваний исходных файлов и выгрузок структурированных наблюдений из репозитория.",
    )
    exports = api_get("/exports/detailed")
    if not exports:
        st.info("Экспортов пока не было. Скачайте исходный файл или экспортируйте наблюдения из карточки набора.")
        return

    st.dataframe(format_table(exports, "exports"), use_container_width=True, hide_index=True)


if "user" not in st.session_state:
    login_page()
else:
    st.sidebar.markdown("### Репозиторий агроданных")
    st.sidebar.caption("MVP для загрузки, проверки и экспорта сельскохозяйственных данных")
    st.sidebar.write(f"Пользователь: {st.session_state.user['full_name']}")
    if st.sidebar.button("Выйти"):
        st.session_state.clear()
        st.rerun()

    refs = load_references()
    if refs:
        pages = [
            "Обзор",
            "Аналитика",
            "Каталог данных",
            "Создание набора данных",
            "Создание версии",
            "Метаданные версии",
            "Загрузка файла",
            "Карточка набора данных",
            "Наблюдения",
            "Журнал экспортов",
        ]
        initial = pages.index(st.session_state.get("page", "Обзор")) if st.session_state.get("page") in pages else 0
        page = st.sidebar.radio("Раздел", pages, index=initial)
        st.session_state.page = page

        if page == "Обзор":
            dashboard_page()
        elif page == "Аналитика":
            analytics_page()
        elif page == "Каталог данных":
            catalog_page(refs)
        elif page == "Создание набора данных":
            create_dataset_page(refs)
        elif page == "Создание версии":
            create_version_page(refs)
        elif page == "Метаданные версии":
            metadata_page(refs)
        elif page == "Загрузка файла":
            upload_page()
        elif page == "Карточка набора данных":
            dataset_card_page()
        elif page == "Наблюдения":
            observations_page(refs)
        elif page == "Журнал экспортов":
            exports_page()
