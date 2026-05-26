# Сводка базы данных MVP-прототипа

Модели базы данных реализованы в `backend/app/models.py` с использованием SQLAlchemy 2.x. В MVP таблицы создаются при старте backend через `Base.metadata.create_all`.

## Реализованные таблицы

| Таблица | SQLAlchemy-класс | Назначение | Реализовано в MVP |
|---|---|---|---|
| `users` | `User` | Пользователи системы | Да |
| `roles` | `Role` | Роли пользователей | Да |
| `user_roles` | `UserRole` | Связь пользователей и ролей | Да |
| `access_levels` | `AccessLevel` | Уровни доступа | Да |
| `categories` | `Category` | Категории наборов | Да |
| `formats` | `DataFormat` | Форматы файлов | Да |
| `licenses` | `License` | Лицензии | Да |
| `regions` | `Region` | Регионы | Да |
| `agro_objects` | `AgroObject` | Агрообъекты | Да |
| `indicators` | `Indicator` | Показатели | Да |
| `measurement_units` | `MeasurementUnit` | Единицы измерения | Да |
| `dataset_statuses` | `DatasetStatus` | Статусы версий | Да |
| `data_sources` | `DataSource` | Источники данных | Да |
| `datasets` | `Dataset` | Постоянные карточки наборов | Да |
| `dataset_versions` | `DatasetVersion` | Версии наборов | Да |
| `dataset_metadata` | `DatasetMetadata` | Метаданные версий | Да |
| `dataset_files` | `DatasetFile` | Файлы версий | Да |
| `keywords` | `Keyword` | Ключевые слова | Да, только модель БД |
| `version_keywords` | `VersionKeyword` | Связь версий и ключевых слов | Да, только модель БД |
| `observations` | `Observation` | Аналитический слой наблюдений | Да |
| `validation_results` | `ValidationResult` | Результаты проверки файлов | Да |
| `validation_errors` | `ValidationError` | Ошибки проверки файлов | Да |
| `data_exports` | `DataExport` | Журнал экспорта и скачивания | Да |

## Ключевые связи

| Связь | Назначение |
|---|---|
| `users` -> `datasets` | Пользователь создает карточки наборов |
| `users` -> `dataset_files` | Пользователь загружает файлы |
| `users` -> `data_exports` | Пользователь инициирует экспорт или скачивание |
| `users` <-> `roles` через `user_roles` | Упрощенная ролевая модель |
| `categories` -> `datasets` | Набор относится к категории |
| `datasets` -> `dataset_versions` | Набор имеет одну или несколько версий |
| `dataset_statuses` -> `dataset_versions` | Статус хранится на версии |
| `access_levels` -> `dataset_versions` | Уровень доступа хранится на версии |
| `data_sources` -> `dataset_versions` | Источник в MVP хранится на версии |
| `dataset_versions` -> `dataset_metadata` | Метаданные относятся к версии |
| `licenses` -> `dataset_metadata` | Метаданные могут ссылаться на лицензию |
| `dataset_versions` -> `dataset_files` | Файлы относятся к версии |
| `formats` -> `dataset_files` | Файл имеет формат |
| `dataset_files` -> `observations` | Наблюдения могут ссылаться на исходный файл |
| `dataset_versions` -> `observations` | Наблюдения относятся к версии |
| `regions` -> `observations` | Наблюдение связано с регионом |
| `agro_objects` -> `observations` | Наблюдение связано с агрообъектом |
| `indicators` -> `observations` | Наблюдение связано с показателем |
| `measurement_units` -> `observations` | Наблюдение связано с единицей измерения |
| `dataset_versions` -> `validation_results` | Проверка относится к версии |
| `dataset_files` -> `validation_results` | Проверка относится к файлу |
| `validation_results` -> `validation_errors` | Ошибки относятся к конкретной проверке |
| `dataset_versions` -> `data_exports` | Экспорт может относиться к версии |
| `dataset_files` -> `data_exports` | Экспорт может относиться к исходному файлу |
| `dataset_versions` <-> `keywords` через `version_keywords` | Ключевые слова версии, реализованы на уровне модели |

## Соотношение с полной идеей v4.1

### Реализовано в MVP

В MVP реализована основная архитектурная идея v4.1:

- `datasets` как постоянная карточка набора;
- `dataset_versions` как изменяемое состояние набора;
- статус версии в `dataset_versions`;
- доступ версии в `dataset_versions`;
- источник версии через `source_id`;
- метаданные на уровне версии;
- файлы на уровне версии;
- аналитический слой `observations`;
- результаты проверки `validation_results` и `validation_errors`;
- фиксация скачиваний и экспортов в `data_exports`;
- универсальные `agro_objects` вместо узкой сущности `crops`.

### Частично реализовано

- `keywords` и `version_keywords` присутствуют как модели БД, но отдельные API endpoints и UI для управления ключевыми словами не реализованы.
- Ролевая модель присутствует как таблицы `users`, `roles`, `user_roles`, но не является промышленной RBAC-системой.

### Оставлено для развития после MVP

В текущем коде отсутствуют следующие элементы полной модели или промышленной реализации:

- `version_sources`;
- `version_status_history`;
- `validation_rules`;
- `audit_log`;
- расширенные геопространственные таблицы/PostGIS;
- таблицы и сервисы интеграции с внешними API/ФГИС;
- полноценная модель прав доступа;
- миграции Alembic;
- интеллектуальные подсказки метаданных.
