import json


def try_parse_json(value):
    if value is None:
        return None

    if isinstance(value, (dict, list, int, float, bool)):
        return value

    if not isinstance(value, str):
        return value

    value = value.strip()
    if not value:
        return value

    if value.startswith("{") or value.startswith("["):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    return value


def format_salary(salary):
    if not salary or not isinstance(salary, dict):
        return "Не указана"

    salary_min = salary.get("min")
    salary_max = salary.get("max")
    currency = salary.get("currency", "RUB")

    currency_symbol = "₽" if currency == "RUB" else currency

    if salary_min and salary_max:
        if salary_min == salary_max:
            return f"{salary_min:,} {currency_symbol}".replace(",", " ")
        return f"{salary_min:,}–{salary_max:,} {currency_symbol}".replace(",", " ")

    if salary_min:
        return f"от {salary_min:,} {currency_symbol}".replace(",", " ")

    if salary_max:
        return f"до {salary_max:,} {currency_symbol}".replace(",", " ")

    return "Не указана"


def format_experience(experience):
    if not experience or not isinstance(experience, dict):
        return "Не указан"

    exp_min = experience.get("min")
    exp_max = experience.get("max")

    if exp_min == 0 and exp_max == 0:
        return "Без опыта"

    if exp_min is not None and exp_max is not None:
        return f"{exp_min}–{exp_max} лет"

    if exp_min is not None:
        return f"от {exp_min} лет"

    if exp_max is not None:
        return f"до {exp_max} лет"

    return "Не указан"


def make_short_description(text, max_len=220):
    if not text:
        return ""

    clean = " ".join(str(text).split())
    if len(clean) <= max_len:
        return clean

    return clean[:max_len].rstrip() + "..."


def normalize_job(row: dict) -> dict:
    job = dict(row)

    job["salary"] = try_parse_json(job.get("salary"))
    job["experience"] = try_parse_json(job.get("experience"))
    job["address_info"] = try_parse_json(job.get("address_info"))
    job["meta"] = try_parse_json(job.get("meta"))

    return job


def serialize_job_card(row: dict) -> dict:
    job = normalize_job(row)

    return {
        "id": job.get("id"),
        "title": job.get("title"),
        "company": job.get("company"),
        "city": job.get("city"),
        "region": job.get("region"),
        "label": job.get("label"),
        "type": job.get("type"),
        "salary": job.get("salary"),
        "salary_text": format_salary(job.get("salary")),
        "experience": job.get("experience"),
        "experience_text": format_experience(job.get("experience")),
        "short_description": make_short_description(job.get("description")),
        "latitude": job.get("latitude"),
        "longitude": job.get("longitude"),
    }