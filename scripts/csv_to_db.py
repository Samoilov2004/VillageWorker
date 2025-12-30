import pandas as pd
import sqlite3
import time
import os
import json
from tqdm import tqdm

def clean_column_names(df):
    """Очистка имен колонок от лишних символов"""
    df.columns = [col.strip().lstrip(',') for col in df.columns]
    return df

def remove_first_column(df):
    """Удаление первой колонки (индексы 0,1,2...)"""
    if df.columns[0] == '' or df.columns[0].startswith(','):
        df = df.drop(df.columns[0], axis=1)
        print("✅ Удалена первая колонка с индексами")
    return df

def process_json_columns(df):
    """Обработка JSON колонок для лучшего поиска"""
    if 'salary' in df.columns:
        try:
            def extract_salary_min(x):
                if pd.isna(x) or x == '':
                    return None
                try:
                    data = json.loads(x.replace('""', '"'))
                    return data.get('min')
                except:
                    return None

            def extract_salary_max(x):
                if pd.isna(x) or x == '':
                    return None
                try:
                    data = json.loads(x.replace('""', '"'))
                    return data.get('max')
                except:
                    return None

            def extract_salary_currency(x):
                if pd.isna(x) or x == '':
                    return None
                try:
                    data = json.loads(x.replace('""', '"'))
                    return data.get('currency')
                except:
                    return None

            df['salary_min'] = df['salary'].apply(extract_salary_min)
            df['salary_max'] = df['salary'].apply(extract_salary_max)
            df['salary_currency'] = df['salary'].apply(extract_salary_currency)
        except Exception as e:
            print(f"⚠️  Не удалось обработать колонку salary: {e}")

    if 'experience' in df.columns:
        try:
            def extract_exp_min(x):
                if pd.isna(x) or x == '':
                    return None
                try:
                    data = json.loads(x.replace('""', '"'))
                    return data.get('min')
                except:
                    return None

            def extract_exp_max(x):
                if pd.isna(x) or x == '':
                    return None
                try:
                    data = json.loads(x.replace('""', '"'))
                    return data.get('max')
                except:
                    return None

            df['experience_min'] = df['experience'].apply(extract_exp_min)
            df['experience_max'] = df['experience'].apply(extract_exp_max)
        except Exception as e:
            print(f"⚠️  Не удалось обработать колонку experience: {e}")

    if 'address_info' in df.columns:
        try:
            def extract_city(x):
                if pd.isna(x) or x == '':
                    return None
                try:
                    data = json.loads(x.replace('""', '"'))
                    return data.get('city')
                except:
                    return None

            def extract_state(x):
                if pd.isna(x) or x == '':
                    return None
                try:
                    data = json.loads(x.replace('""', '"'))
                    return data.get('state')
                except:
                    return None

            df['city'] = df['address_info'].apply(extract_city)
            df['state'] = df['address_info'].apply(extract_state)
        except Exception as e:
            print(f"⚠️  Не удалось обработать колонку address_info: {e}")

    return df

def csv_to_sqlite(csv_path: str = "data/jobs.csv", db_path: str = "data/jobs.db"):
    """Конвертировать CSV в SQLite базу данных"""

    if not os.path.exists(csv_path):
        print(f"❌ Файл {csv_path} не найден!")
        print(f"Текущая директория: {os.getcwd()}")
        return False

    print(f"🚀 Начинаем конвертацию {csv_path} в SQLite...")
    start_time = time.time()

    try:
        data_dir = os.path.dirname(db_path)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir)
            print(f"📁 Создана папка: {data_dir}")

        print("📖 Читаем CSV файл...")
        df = pd.read_csv(csv_path, sep='\t')
        print(f"📊 Прочитано строк: {len(df)}")
        print(f"📋 Исходные колонки: {list(df.columns)}")

        df = clean_column_names(df)
        df = remove_first_column(df)

        print(f"📋 Колонки после очистки: {list(df.columns)}")

        print("🔧 Обработка JSON колонок...")
        df = process_json_columns(df)

        conn = sqlite3.connect(db_path)
        print(f"✅ Подключено к базе данных: {db_path}")

        print("💾 Сохраняем в базу данных...")
        df.to_sql('jobs', conn, if_exists='replace', index=False)

        print(".CreateIndexes...")
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(jobs)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        print(f"🔍 Найденные колонки в базе: {existing_columns}")

        possible_indexes = [
            ('id', 'idx_id'),
            ('title', 'idx_title'),
            ('description', 'idx_description'),
            ('city', 'idx_city'),
            ('company', 'idx_company'),
            ('type', 'idx_type'),
            ('salary_min', 'idx_salary_min')
        ]

        created_indexes = []
        for column, index_name in possible_indexes:
            if column in existing_columns:
                try:
                    cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON jobs({column})")
                    created_indexes.append(column)
                    print(f"✅ Создан индекс для {column}")
                except Exception as e:
                    print(f"⚠️  Не удалось создать индекс для {column}: {e}")
            else:
                print(f"ℹ️  Колонка {column} отсутствует в данных")

        conn.commit()
        conn.close()

        end_time = time.time()

        print(f"\n✅ Конвертация завершена!")
        print(f"📊 Обработано строк: {len(df):,}")
        print(f"📋 Созданы индексы для: {created_indexes}")
        print(f"⏱️  Время выполнения: {end_time - start_time:.2f} секунд")
        print(f"💾 База данных сохранена в: {db_path}")

        # Показываем размер файлов
        csv_size = os.path.getsize(csv_path) / (1024*1024)
        db_size = os.path.getsize(db_path) / (1024*1024)
        print(f"📏 Размер CSV: {csv_size:.1f} MB")
        print(f"📏 Размер DB: {db_size:.1f} MB")

        return True

    except Exception as e:
        print(f"❌ Ошибка конвертации: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_csv_info(csv_path: str = "data/jobs.csv"):
    """Показать информацию о CSV файле"""
    if not os.path.exists(csv_path):
        print(f"❌ Файл {csv_path} не найден!")
        print(f"Текущая директория: {os.getcwd()}")
        return

    print("📋 Информация о CSV файле:")
    try:
        df = pd.read_csv(csv_path, sep='\t', nrows=3)
        df = clean_column_names(df)
        df = remove_first_column(df)
        print(f"Колонки: {list(df.columns)}")
        print(f"Первые 3 строки:")
        print(df.head(3))
        total_rows = len(pd.read_csv(csv_path, sep='\t'))
        print(f"\nОбщее количество строк: {total_rows}")
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    csv_file = "../databases/job_ads.csv"
    db_file = "../databases/job_ads.db"

    print("🔍 Проверяем файлы...")
    print(f"CSV файл: {csv_file}")
    print(f"Путь существует: {os.path.exists(csv_file)}")

    show_csv_info(csv_file)
    print("\n" + "="*50 + "\n")

    csv_to_sqlite(csv_file, db_file)
