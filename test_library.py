import unittest
from datetime import date, timedelta

from library import FINE_PER_DAY, LOAN_DAYS, Library, LibraryError


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.lib = Library(":memory:")
        self.book = self.lib.add_book("Clean Code", "Robert Martin", "111", copies=1)
        self.member = self.lib.add_member("Asha", "asha@example.com")

    def tearDown(self):
        self.lib.close()

    def test_duplicate_isbn_rejected(self):
        with self.assertRaises(LibraryError):
            self.lib.add_book("Other", "Someone", "111")

    def test_search(self):
        self.assertEqual(len(self.lib.search_books("clean")), 1)
        self.assertEqual(self.lib.search_books("nothing"), [])

    def test_issue_and_availability(self):
        self.lib.issue_book(self.book, self.member)
        self.assertEqual(self.lib.available_copies(self.book), 0)
        with self.assertRaises(LibraryError):
            self.lib.issue_book(self.book, self.member)

    def test_return_on_time_has_no_fine(self):
        loan_id, _ = self.lib.issue_book(self.book, self.member)
        self.assertEqual(self.lib.return_book(loan_id), 0)
        self.assertEqual(self.lib.available_copies(self.book), 1)

    def test_late_return_fine(self):
        start = date(2026, 1, 1)
        loan_id, _ = self.lib.issue_book(self.book, self.member, today=start)
        late = start + timedelta(days=LOAN_DAYS + 5)
        self.assertEqual(self.lib.return_book(loan_id, today=late), 5 * FINE_PER_DAY)

    def test_double_return_rejected(self):
        loan_id, _ = self.lib.issue_book(self.book, self.member)
        self.lib.return_book(loan_id)
        with self.assertRaises(LibraryError):
            self.lib.return_book(loan_id)

    def test_overdue_list(self):
        start = date(2026, 1, 1)
        self.lib.issue_book(self.book, self.member, today=start)
        later = start + timedelta(days=LOAN_DAYS + 1)
        self.assertEqual(len(self.lib.overdue_loans(today=later)), 1)

    def test_cannot_remove_issued_book(self):
        self.lib.issue_book(self.book, self.member)
        with self.assertRaises(LibraryError):
            self.lib.remove_book(self.book)


if __name__ == "__main__":
    unittest.main()
