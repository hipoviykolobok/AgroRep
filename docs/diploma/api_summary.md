# Сводка API MVP-прототипа

API реализовано в `backend/app/main.py`. Frontend обращается к backend через переменную окружения `BACKEND_URL`.

## Полный список endpoints

| Метод | Путь | Назначение | Используется frontend | Группа |
|---|---|---|---|---|
| `GET` | `/health` | Проверка работоспособности backend | Нет | Сервисный |
| `POST` | `/seed` | Заполнение справочников и demo-пользователей | Да | Справочники |
| `POST` | `/auth/login` | Авторизация пользователя | Да | Авторизация |
| `GET` | `/references` | Получение справочников | Да | Справочники |
| `GET` | `/dashboard` | Сводные показатели репозитория | Да | Аналитика |
| `GET` | `/analytics` | Агрегации для диаграмм | Да | Аналитика |
| `GET` | `/catalog/datasets` | Каталог наборов с фильтрами | Да | Каталог |
| `POST` | `/datasets` | Создание карточки набора | Да | Наборы данных |
| `POST` | `/datasets/{dataset_id}/versions` | Создание версии набора | Да | Версии |
| `POST` | `/versions/{version_id}/metadata` | Создание или обновление метаданных версии | Да | Метаданные |
| `POST` | `/versions/{version_id}/files` | Загрузка файла и валидация | Да | Загрузка и проверка |
| `POST` | `/files/{file_id}/import-observations` | Импорт файла в observations | Да | Импорт |
| `GET` | `/datasets/{dataset_id}` | Карточка набора данных | Да | Каталог |
| `GET` | `/versions/{version_id}/observations` | Наблюдения версии с фильтрами | Да | Наблюдения |
| `GET` | `/files/{file_id}/download` | Скачивание исходного файла | Да | Экспорт |
| `GET` | `/versions/{version_id}/export-observations` | Экспорт observations в CSV | Да | Экспорт |
| `GET` | `/exports` | Базовый список экспортов | Нет, используется тестом | Экспорт |
| `GET` | `/exports/detailed` | Детальный журнал экспортов | Да | Экспорт |

## Endpoints по функциональным группам

### Авторизация и справочники

- `POST /auth/login`
- `POST /seed`
- `GET /references`

### Каталог и карточки наборов

- `GET /catalog/datasets`
- `POST /datasets`
- `GET /datasets/{dataset_id}`

### Версии и метаданные

- `POST /datasets/{dataset_id}/versions`
- `POST /versions/{version_id}/metadata`

### Загрузка, проверка и импорт

- `POST /versions/{version_id}/files`
- `POST /files/{file_id}/import-observations`

### Наблюдения и аналитика

- `GET /versions/{version_id}/observations`
- `GET /dashboard`
- `GET /analytics`

### Экспорт и журнал экспортов

- `GET /files/{file_id}/download`
- `GET /versions/{version_id}/export-observations`
- `GET /exports`
- `GET /exports/detailed`

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
- `POST /versions/{version_id}/metadata` при сохранении метаданных;
- `POST /versions/{version_id}/files` при загрузке файла;
- `POST /files/{file_id}/import-observations` при импорте observations;
- `GET /datasets/{dataset_id}` на странице карточки;
- `GET /versions/{version_id}/observations` на странице наблюдений и в карточке;
- `GET /files/{file_id}/download` при скачивании исходного файла;
- `GET /versions/{version_id}/export-observations` при экспорте observations;
- `GET /exports/detailed` на страницах обзора и журнала экспортов.
