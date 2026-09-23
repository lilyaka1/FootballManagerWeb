# Backend

## Запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Документация API будет доступна на `http://localhost:8000/docs`.

По умолчанию используется SQLite для локального старта. Для PostgreSQL задайте `DATABASE_URL`, например:

```text
postgresql+psycopg://postgres:postgres@localhost:5432/football_manager
```
