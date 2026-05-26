# Сводка API MVP-прототипа

API реализовано в `backend/app/main.py`. Frontend обращается к backend через переменную окружения `BACKEND_URL`. Текущая реализация является API-слоем MVP-прототипа и предназначена для локальной демонстрации основного жизненного цикла данных.

## Полный список endpoints

| Метод | Путь | Назначение | Используется frontend | Группа |
|---|---|---|---|---|
| `GET` | `/health` | Проверка работоспособности backend | Нет | Сервисный |
| `POST` | `/seed` | Заполнение справочников и demo-пользователей | Да | Справочники |
| `POST` | `/auth/login` | Demo-авторизация пользователя | Да | Авторизация |
| `GET` | `/references` | Получение справочников для интерфейса | Да | Справочники |
| `GET` | `/dashboard` | Сводные показатели репозитория для страницы обзора | Да | Обзор |
| `GET` | `/analytics` | Агрегированные данные для демонстрационной аналитики | Да | Аналитика |
| `GET` | `/catalog/datasets` | Каталог наборов данных с фильтрами | Да | Каталог |
| `POST` | `/datasets` | Создание постоянной карточки набора данных | Да | Наборы данных |
| `POST` | `/datasets/{dataset_id}/versions` | Создание версии набора данных | Да | Версии |
| `POST` | `/versions/{version_id}/make-current` | Назначение версии текущей для набора данных | Да | Версии |
| `POST` | `/versions/{version_id}/metadata` | Создание или обновление метаданных версии | Да | Метаданные |
| `POST` | `/versions/{version_id}/files` | Загрузка CSV/XLSX-файла, расчет checksum и базовая проверка | Да | Загрузка и проверка |
| `POST` | `/files/{file_id}/import-observations` | Импорт строк файла в таблицу `observations` | Да | Импорт |
| `GET` | `/datasets/{dataset_id}` | Получение карточки набора данных | Да | Карточка |
| `DELETE` | `/datasets/{dataset_id}` | Удаление набора данных администратором | Да | Администрирование |
| `DELETE` | `/versions/{version_id}` | Удаление версии администратором | Да | Администрирование |
| `DELETE` | `/files/{file_id}` | Удаление файла администратором | Да | Администрирование |
| `GET` | `/versions/{version_id}/observations` | Получение наблюдений версии с фильтрами | Да | Наблюдения |
| `GET` | `/files/{file_id}/download` | Скачивание исходного файла с записью в `data_exports` | Да | Экспорт |
| `GET` | `/versions/{version_id}/export-observations` | Экспорт observations в CSV с записью в `data_exports` | Да | Экспорт |
| `GET` | `/exports` | Базовый список экспортных операций | Нет, используется тестами | Экспорт |
| `GET` | `/exports/detailed` | Детальный журнал экспортов для интерфейса | Да | Экспорт |

## Endpoints по функциональным группам

### Авторизация и справочники

- `POST /auth/login`
- `POST /seed`
- `GET /references`

Авторизация является демонстрационной: пользователь входит по email и паролю demo-учетной записи. JWT/OAuth и промышленная RBAC-модель не реализованы.

### Каталог и карточки наборов

- `GET /catalog/datasets`
- `POST /datasets`
- `GET /datasets/{dataset_id}`

### Версии и метаданные

- `POST /datasets/{dataset_id}/versions`
- `POST /versions/{version_id}/make-current`
- `POST /versions/{version_id}/metadata`

Endpoint `POST /versions/{version_id}/make-current` используется для переключения текущей версии набора данных. Это позволяет пользователю вернуться к предыдущей версии или назначить актуальной другую уже созданную версию.

### Загрузка, проверка и импорт

- `POST /versions/{version_id}/files`
- `POST /files/{file_id}/import-observations`

При загрузке файла вычисляется SHA-256 checksum. Если в пределах версии уже есть файл с такой же контрольной суммой, backend возвращает информацию о дубликате, а frontend показывает предупреждение пользователю. Повторно загруженный файл сохраняется отдельной записью в `dataset_files`.

### Наблюдения и аналитика

- `GET /versions/{version_id}/observations`
- `GET /dashboard`
- `GET /analytics`

### Скачивание, экспорт и журнал экспортов

- `GET /files/{file_id}/download`
- `GET /versions/{version_id}/export-observations`
- `GET /exports`
- `GET /exports/detailed`

Скачивание исходного файла и экспорт структурированных наблюдений фиксируются в таблице `data_exports`.

### Административное удаление

- `DELETE /datasets/{dataset_id}`
- `DELETE /versions/{version_id}`
- `DELETE /files/{file_id}`

Удаление доступно пользователю с ролью `admin`. В MVP удаление физическое: soft delete, восстановление удаленных данных, журнал причин удаления и полноценный `audit_log` не реализованы.

## Использование API во frontend

Frontend использует:

- `POST /auth/login` на странице входа;
- `POST /seed` на странице входа;
- `GET /references` для заполнения списков справочников;
- `GET /dashboard` на странице `Обзор`;
- `GET /analytics` на странице `Аналитика`;
- `GET /catalog/datasets` на страницах каталога, создания версии, метаданных, загрузки, карточки и наблюдений;
- `POST /datasets` при создании набора;
- `POST /datasets/{dataset_id}/versions` при создании версии;
- `POST /versions/{version_id}/make-current` при переключении текущей версии;
- `POST /versions/{version_id}/metadata` при сохранении метаданных;
- `POST /versions/{version_id}/files` при загрузке файла;
- `POST /files/{file_id}/import-observations` при импорте observations;
- `GET /datasets/{dataset_id}` на странице карточки;
- `DELETE /datasets/{dataset_id}` при удалении набора администратором;
- `DELETE /versions/{version_id}` при удалении версии администратором;
- `DELETE /files/{file_id}` при удалении файла администратором;
- `GET /versions/{version_id}/observations` на странице наблюдений и в карточке;
- `GET /files/{file_id}/download` при скачивании исходного файла;
- `GET /versions/{version_id}/export-observations` при экспорте observations;
- `GET /exports/detailed` на страницах обзора и журнала экспортов.

## Что не реализовано на уровне API

- Полноценная серверная авторизация через JWT/OAuth.
- Production-grade RBAC.
- API для управления `keywords` и `version_keywords`.
- API для `validation_rules`.
- API для `version_sources`.
- API для `version_status_history`.
- Общий `audit_log` всех действий.
- Интеграции с внешними ФГИС/API.
