from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "database" / "job_ads.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    return conn


def init_tables() -> None:
    conn = get_connection()

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                company TEXT,
                city TEXT,
                salary_min INTEGER,
                salary_max INTEGER,
                experience_min INTEGER DEFAULT 0,
                experience_max INTEGER DEFAULT 0,
                label TEXT,
                mod_status TEXT DEFAULT 'ok',
                risk_score REAL DEFAULT 0,
                mod_reasons TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                job_title TEXT,
                user_name TEXT,
                phone TEXT,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_dialogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                job_title TEXT NOT NULL,
                applicant_id INTEGER NOT NULL,
                applicant_name TEXT NOT NULL,
                employer_id INTEGER NOT NULL,
                employer_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(job_id, applicant_id, employer_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dialog_id INTEGER NOT NULL,
                sender_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read INTEGER DEFAULT 0,
                FOREIGN KEY(dialog_id) REFERENCES chat_dialogs(id)
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_dialogs_users
            ON chat_dialogs(applicant_id, employer_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_messages_dialog_id
            ON chat_messages(dialog_id)
        """)

        seed_demo_chat(conn)

        conn.commit()
    finally:
        conn.close()


def seed_demo_chat(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM chat_dialogs
        WHERE job_id = 1
          AND applicant_id = 1
          AND employer_id = 2
    """)

    existing_dialog = cursor.fetchone()

    if existing_dialog:
        return

    cursor.execute("""
        INSERT INTO chat_dialogs (
            job_id,
            job_title,
            applicant_id,
            applicant_name,
            employer_id,
            employer_name
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        1,
        "Рабочий на ферму",
        1,
        "Иван Петров",
        2,
        "ООО АгроПлюс",
    ))

    dialog_id = cursor.lastrowid

    demo_messages = [
        (dialog_id, 1, "Здравствуйте! Меня заинтересовала вакансия рабочего на ферму. Подскажите, пожалуйста, актуальна ли она?"),
        (dialog_id, 2, "Здравствуйте, Иван! Да, вакансия актуальна. Опыт работы в сельском хозяйстве у вас есть?"),
        (dialog_id, 1, "Да, есть опыт сезонной работы и ухода за животными."),
        (dialog_id, 2, "Отлично. Тогда можем обсудить график и условия работы."),
    ]

    cursor.executemany("""
        INSERT INTO chat_messages (dialog_id, sender_id, text)
        VALUES (?, ?, ?)
    """, demo_messages)