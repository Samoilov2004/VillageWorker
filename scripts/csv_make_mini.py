import pandas as pd
import random
from pathlib import Path


def create_test_dataset():
    """Создать тестовый датасет с 100 случайных строк"""

    script_dir = Path(__file__).resolve().parent

    # Пути относительно расположения скрипта
    input_csv = script_dir / "../database/job_ads.csv"
    output_csv = script_dir / "../database/mini_jobs.csv"

    input_csv = input_csv.resolve()
    output_csv = output_csv.resolve()

    print("🔍 Создание тестового датасета...")
    print(f"Исходный файл: {input_csv}")
    print(f"Тестовый файл: {output_csv}")

    if not input_csv.exists():
        print(f"❌ Исходный файл не найден: {input_csv}")
        return False

    try:
        print("📖 Читаем исходный файл...")
        df = pd.read_csv(input_csv, sep='\t')
        print(f"📊 Всего строк в исходном файле: {len(df)}")

        if len(df) <= 100:
            sample_df = df
            print(f"ℹ️ В файле меньше 100 строк, берем все {len(df)} строк")
        else:
            random_indices = random.sample(range(len(df)), 100)
            sample_df = df.iloc[random_indices]
            print("✅ Выбрано 100 случайных строк")

        output_csv.parent.mkdir(parents=True, exist_ok=True)

        print("💾 Сохраняем тестовый файл...")
        sample_df.to_csv(output_csv, sep='\t', index=False)

        print("✅ Тестовый датасет создан!")
        print(f"📊 Строк в тестовом файле: {len(sample_df)}")
        print(f"💾 Файл сохранен: {output_csv}")

        return True

    except Exception as e:
        print(f"❌ Ошибка создания тестового датасета: {e}")
        return False


if __name__ == "__main__":
    create_test_dataset()
