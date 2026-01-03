# Databases

## Описание данных
| Column | RU (Описание) | EN (Description) |
|---|---|---|
| `id` | Уникальный идентификатор вакансии | Unique job posting identifier |
| `title` | Название вакансии | Job title |
| `salary` | Зарплата в формате JSON: `min`, `max`, `currency` (часто `max` может быть `null`) | Salary as JSON: `min`, `max`, `currency` (`max` can be `null`) |
| `experience` | Требуемый опыт (лет) в формате JSON: `min`, `max` (если верхней границы нет — `null`) | Required experience (years) as JSON: `min`, `max` (`null` if not specified) |
| `description` | Полный текст описания вакансии | Full job description text |
| `key_skills` | Ключевые навыки (строка/список, как указано в источнике) | Key skills (string/list as provided by the source) |
| `company` | Название компании/работодателя | Employer/company name |
| `type` | Тип/статус вакансии (например, `open`) | Posting type/status (e.g., `open`) |
| `address_info` | Геоданные в JSON (координаты, страна, город, регион и др.), получены через geopy; содержит `status` геокодирования | Geodata in JSON (coords, country, city, region, etc.) via geopy; includes geocoding `status` |
| `meta` | Метаданные в JSON: `publication_time`, `last_edit_time`, `total_views`, `views_last_week` (синтетические) | Metadata in JSON: `publication_time`, `last_edit_time`, `total_views`, `views_last_week` (synthetic) |
| `label` | Категория вакансии (из списка), присвоена LLM по `title/description` | Job category label (from a fixed list), assigned by an LLM using `title/description` |

## Хранение данных

Сдесь использовал Git LFS (у меня мак, на винде мб по-другому бы было)

Зачем нужен Git LFS?
По сути это тулза для уменьшения нагрузки по памяти на репу, а у нас мб ваще большой датасет будет, так что надо так делать

```bash
brew install git-lfs
git lfs install 

# Проверка установки 
git lfs version
# Вывело - git-lfs/3.7.1 (GitHub; darwin arm64; go 1.25.3)

# Будем отслеживать такие вот файлы
git lfs track "*.csv" 
git lfs track "*.db" 

# Cоздаст файл .gitattributes
git add .gitattributes
```


По репе
- `job_ads.csv` - csv файл мб понадобится
- `job_ads.db` - SQLite версия (по сути всегда должна быть клоном с job_ads)
- `mini_jobs.db` - мини версия на 100 строк в csv для тестирования