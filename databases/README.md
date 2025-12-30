# Databases

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