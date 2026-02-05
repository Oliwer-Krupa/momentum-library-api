# Momentum Library API

Simple REST API for a library system -- track books and their lending status.
Built with **FastAPI**, **SQLAlchemy 2.0**, **PostgreSQL**, and **Docker Compose**.

## Quickstart

```bash
git clone <repo-url> && cd momentum-library-api
docker compose up --build
```

The API is available at **http://localhost:8000**.
Interactive docs: [Swagger UI](http://localhost:8000/docs) | [ReDoc](http://localhost:8000/redoc)
When the stack starts, a one-time smoke test container runs basic API checks. It will
exit with code `0` on success and log the steps to the console.

## API Endpoints

| Method | Path | Body | Success | Errors |
|--------|------|------|---------|--------|
| `POST` | `/books/` | `{serial_number, title, author}` | `201` | `409` duplicate, `422` validation |
| `GET` | `/books/` | -- | `200` | -- |
| `DELETE` | `/books/{serial_number}` | -- | `204` | `404` not found |
| `PATCH` | `/books/{serial_number}/borrow` | `{borrower_card_number}` | `200` | `404`, `409` already borrowed |
| `PATCH` | `/books/{serial_number}/return` | -- | `200` | `404`, `409` not borrowed |
| `GET` | `/health` | -- | `200` | -- |

### Query parameters

`GET /books/` accepts an optional `?status=AVAILABLE` or `?status=BORROWED` filter.
Results are always sorted by `serial_number` ascending.

## Example usage (curl)

```bash
# Add a book
curl -X POST http://localhost:8000/books/ \
  -H "Content-Type: application/json" \
  -d '{"serial_number": "000001", "title": "The Pragmatic Programmer", "author": "David Thomas"}'

# List all books
curl http://localhost:8000/books/

# Borrow a book
curl -X PATCH http://localhost:8000/books/000001/borrow \
  -H "Content-Type: application/json" \
  -d '{"borrower_card_number": "654321"}'

# Return a book
curl -X PATCH http://localhost:8000/books/000001/return

# Delete a book
curl -X DELETE http://localhost:8000/books/000001

# Filter by status
curl "http://localhost:8000/books/?status=BORROWED"
```

## Validation rules

- **`serial_number`**: exactly 6 digits (`^\d{6}$`), unique across all books.
- **`borrower_card_number`**: exactly 6 digits (`^\d{6}$`).
- **`title`**: 1-300 characters.
- **`author`**: 1-200 characters.

Invalid input returns `422` with detailed Pydantic error messages.

## Error semantics

| Code | Meaning |
|------|---------|
| `404` | Book with the given `serial_number` does not exist. |
| `409` | State conflict: duplicate `serial_number` on create, borrowing an already-borrowed book, or returning a book that is not borrowed. |
| `422` | Request validation failed (malformed `serial_number`, missing fields, etc.). |

## Book response model

```json
{
  "serial_number": "000001",
  "title": "The Pragmatic Programmer",
  "author": "David Thomas",
  "status": "AVAILABLE",
  "borrowed_at": null,
  "borrower_card_number": null
}
```

When borrowed, `status` becomes `"BORROWED"`, `borrowed_at` is set to an ISO-8601 UTC timestamp
(e.g. `"2026-02-05T14:30:00+00:00"`), and `borrower_card_number` contains the borrower's card number.

## Design decisions

- **No Alembic migrations.** For this MVP, tables are created idempotently on startup via
  `Base.metadata.create_all()`. In production, Alembic would manage schema evolution.
- **`serial_number` and `borrower_card_number` stored as STRING**, not INTEGER, to preserve
  leading zeros (e.g. `"000123"`).
- **Status consistency enforced at two levels:**
  - Application logic (API returns 409 on invalid state transitions).
  - Database CHECK constraints ensure `AVAILABLE` books have `NULL` borrow fields, and
    `BORROWED` books have both fields set.
- **`SELECT ... FOR UPDATE`** on borrow/return endpoints prevents race conditions when two
  concurrent requests target the same book.
- **Production deployment:** The included credentials are for **local development only**.
  For production:
  - Use Docker secrets or external secret management (e.g., AWS Secrets Manager, HashiCorp Vault)
  - Set `DATABASE_URL` via environment variable
  - Never commit production credentials to version control

## Running tests

```bash
pip install -e ".[dev]"
pytest -v
```

Tests use an in-memory SQLite database (no Docker or PostgreSQL required).

### Smoke test (Docker)

The `smoke` service runs automatically on `docker compose up`. It sends a short
sequence of HTTP requests to verify the API end-to-end.

## Linting

```bash
ruff check app/ tests/
black --check app/ tests/
```

## Project structure

```
momentum-library-api/
├── app/
│   ├── main.py              # FastAPI application + lifespan
│   ├── config.py             # Settings (pydantic-settings)
│   ├── database.py           # Engine, session, Base, init_db
│   ├── models.py             # SQLAlchemy Book model
│   ├── schemas.py            # Pydantic request/response models
│   └── routers/
│       └── books.py          # All book endpoints
├── tests/
│   ├── conftest.py           # Test fixtures (SQLite override)
│   └── test_books.py         # 17 endpoint tests
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── .env.example
└── .github/workflows/ci.yml  # Ruff + Black + Pytest
```

## License

MIT
