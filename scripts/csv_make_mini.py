import pandas as pd
import os
import random

def create_test_dataset():
    """Создать тестовый датасет с 100 случайных строк"""

    input_csv = "../databases/job_ads.csv"
    output_csv = "../databases/mini_jobs.csv"

    print("🔍 Создание тестового датасета...")
    print(f"Исходный файл: {input_csv}")
    print(f"Тестовый файл: {output_csv}")

    if not os.path.exists(input_csv):
        print(f"❌ Исходный файл не найден: {input_csv}")
        return False

    try:
        print("📖 Читаем исходный файл...")
        df = pd.read_csv(input_csv, sep='\t')
        print(f"📊 Всего строк в исходном файле: {len(df)}")

        if len(df) <= 100:
            sample_df = df
            print(f"ℹ️  В файле меньше 100 строк, берем все {len(df)} строк")
        else:
            random_indices = random.sample(range(len(df)), 100)
            sample_df = df.iloc[random_indices]
            print(f"✅ Выбрано 100 случайных строк")

        print("💾 Сохраняем тестовый файл...")
        sample_df.to_csv(output_csv, sep='\t', index=False)

        print(f"✅ Тестовый датасет создан!")
        print(f"📊 Строк в тестовом файле: {len(sample_df)}")
        print(f"💾 Файл сохранен: {output_csv}")

        return True

    except Exception as e:
        print(f"❌ Ошибка создания тестового датасета: {e}")
        return False

if __name__ == "__main__":
    create_test_dataset()
