"""Core logic for the Library Management System (SQLite backed)."""

import sqlite3
from datetime import date, timedelta

LOAN_DAYS = 14        # how long a book can be borrowed
FINE_PER_DAY = 2      # fine per overdue day (currency units)


class LibraryError(Exception):
    """Raised for any rule violation (missing book, no copies left, etc.)."""


class Library:
    def __init__(self, db_path="library.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS books (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                title   TEXT NOT NULL,
                author  TEXT NOT NULL,
                isbn    TEXT UNIQUE,
                copies  INTEGER NOT NULL DEFAULT 1 CHECK (copies >= 0)
            );
            CREATE TABLE IF NOT EXISTS members (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                name   TEXT NOT NULL,
                email  TEXT UNIQUE
            );
            CREATE TABLE IF NOT EXISTS loans (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id      INTEGER NOT NULL REFERENCES books(id),
                member_id    INTEGER NOT NULL REFERENCES members(id),
                issued_on    TEXT NOT NULL,
                due_on       TEXT NOT NULL,
                returned_on  TEXT,
                fine         INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        self.conn.commit()

    def close(self):
        self.conn.close()

    # ---------------------------------------------------------------- books
    def add_book(self, title, author, isbn=None, copies=1):
        if not title.strip() or not author.strip():
            raise LibraryError("Title and author are required.")
        if copies < 1:
            raise LibraryError("Copies must be at least 1.")
        try:
            cur = self.conn.execute(
                "INSERT INTO books (title, author, isbn, copies) VALUES (?, ?, ?, ?)",
                (title.strip(), author.strip(), isbn or None, copies),
            )
        except sqlite3.IntegrityError:
            raise LibraryError("A book with this ISBN already exists.")
        self.conn.commit()
        return cur.lastrowid

    def get_book(self, book_id):
        row = self.conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        if row is None:
            raise LibraryError(f"No book with id {book_id}.")
        return row

    def available_copies(self, book_id):
        book = self.get_book(book_id)
        out = self.conn.execute(
            "SELECT COUNT(*) FROM loans WHERE book_id = ? AND returned_on IS NULL",
            (book_id,),
        ).fetchone()[0]
        return book["copies"] - out

    def list_books(self):
        rows = self.conn.execute("SELECT * FROM books ORDER BY title").fetchall()
        return [dict(r, available=self.available_copies(r["id"])) for r in rows]

    def search_books(self, term):
        like = f"%{term}%"
        rows = self.conn.execute(
            "SELECT * FROM books WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ? ORDER BY title",
            (like, like, like),
        ).fetchall()
        return [dict(r, available=self.available_copies(r["id"])) for r in rows]

    def remove_book(self, book_id):
        self.get_book(book_id)
        active = self.conn.execute(
            "SELECT COUNT(*) FROM loans WHERE book_id = ? AND returned_on IS NULL",
            (book_id,),
        ).fetchone()[0]
        if active:
            raise LibraryError("Cannot remove a book that is currently issued.")
        self.conn.execute("DELETE FROM loans WHERE book_id = ?", (book_id,))
        self.conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
        self.conn.commit()

    # -------------------------------------------------------------- members
    def add_member(self, name, email=None):
        if not name.strip():
            raise LibraryError("Member name is required.")
        try:
            cur = self.conn.execute(
                "INSERT INTO members (name, email) VALUES (?, ?)",
                (name.strip(), email or None),
            )
        except sqlite3.IntegrityError:
            raise LibraryError("A member with this email already exists.")
        self.conn.commit()
        return cur.lastrowid

    def get_member(self, member_id):
        row = self.conn.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
        if row is None:
            raise LibraryError(f"No member with id {member_id}.")
        return row

    def list_members(self):
        return [dict(r) for r in self.conn.execute("SELECT * FROM members ORDER BY name")]

    # ---------------------------------------------------------------- loans
    def issue_book(self, book_id, member_id, today=None):
        today = today or date.today()
        self.get_member(member_id)
        if self.available_copies(book_id) < 1:
            raise LibraryError("No copies of this book are available.")
        due = today + timedelta(days=LOAN_DAYS)
        cur = self.conn.execute(
            "INSERT INTO loans (book_id, member_id, issued_on, due_on) VALUES (?, ?, ?, ?)",
            (book_id, member_id, today.isoformat(), due.isoformat()),
        )
        self.conn.commit()
        return cur.lastrowid, due

    def return_book(self, loan_id, today=None):
        """Returns the fine (0 if returned on time)."""
        today = today or date.today()
        loan = self.conn.execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()
        if loan is None:
            raise LibraryError(f"No loan with id {loan_id}.")
        if loan["returned_on"]:
            raise LibraryError("This book has already been returned.")
        due = date.fromisoformat(loan["due_on"])
        fine = max(0, (today - due).days) * FINE_PER_DAY
        self.conn.execute(
            "UPDATE loans SET returned_on = ?, fine = ? WHERE id = ?",
            (today.isoformat(), fine, loan_id),
        )
        self.conn.commit()
        return fine

    def list_loans(self, active_only=True):
        query = """
            SELECT loans.*, books.title, members.name AS member_name
            FROM loans
            JOIN books ON books.id = loans.book_id
            JOIN members ON members.id = loans.member_id
        """
        if active_only:
            query += " WHERE loans.returned_on IS NULL"
        query += " ORDER BY loans.due_on"
        return [dict(r) for r in self.conn.execute(query)]

    def overdue_loans(self, today=None):
        today = (today or date.today()).isoformat()
        return [l for l in self.list_loans(active_only=True) if l["due_on"] < today]
