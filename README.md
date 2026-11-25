# Library Management System

A simple command-line library management system written in Python with SQLite.
No third-party dependencies — only the Python standard library.

## Features

- Add, list, search and remove books (with multiple copies per title)
- Register and list members
- Issue and return books (14-day loan period)
- Automatic fine calculation for late returns (2 per day)
- View active and overdue loans
- Unit tests included

## Requirements

- Python 3.8+

## Run

```bash
python main.py
```

Data is stored in `library.db` (created automatically on first run).

## Test

```bash
python -m unittest -v
```

## Project structure

| File              | Purpose                                   |
|-------------------|-------------------------------------------|
| `library.py`      | Core logic and database layer             |
| `main.py`         | Menu-driven command-line interface        |
| `test_library.py` | Unit tests                                |

## Configuration

Change `LOAN_DAYS` and `FINE_PER_DAY` at the top of `library.py`.

## License

MIT
