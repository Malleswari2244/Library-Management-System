"""Menu-driven command line interface for the Library Management System."""

from library import FINE_PER_DAY, Library, LibraryError

MENU = """
===== Library Management System =====
 1. Add book
 2. List books
 3. Search books
 4. Remove book
 5. Add member
 6. List members
 7. Issue book
 8. Return book
 9. Show active loans
10. Show overdue loans
 0. Exit
"""


def ask_int(prompt):
    try:
        return int(input(prompt).strip())
    except ValueError:
        raise LibraryError("Please enter a valid number.")


def print_books(books):
    if not books:
        print("No books found.")
        return
    print(f"{'ID':<4} {'Title':<30} {'Author':<22} {'ISBN':<15} Avail/Total")
    for b in books:
        print(f"{b['id']:<4} {b['title'][:29]:<30} {b['author'][:21]:<22} "
              f"{(b['isbn'] or '-'):<15} {b['available']}/{b['copies']}")


def print_loans(loans):
    if not loans:
        print("No loans found.")
        return
    print(f"{'Loan':<5} {'Book':<28} {'Member':<18} {'Issued':<11} Due")
    for l in loans:
        print(f"{l['id']:<5} {l['title'][:27]:<28} {l['member_name'][:17]:<18} "
              f"{l['issued_on']:<11} {l['due_on']}")


def handle(lib, choice):
    if choice == "1":
        title = input("Title: ")
        author = input("Author: ")
        isbn = input("ISBN (optional): ").strip()
        copies = ask_int("Copies: ")
        print(f"Book added with id {lib.add_book(title, author, isbn, copies)}.")
    elif choice == "2":
        print_books(lib.list_books())
    elif choice == "3":
        print_books(lib.search_books(input("Search term: ")))
    elif choice == "4":
        lib.remove_book(ask_int("Book id: "))
        print("Book removed.")
    elif choice == "5":
        name = input("Name: ")
        email = input("Email (optional): ").strip()
        print(f"Member added with id {lib.add_member(name, email)}.")
    elif choice == "6":
        members = lib.list_members()
        if not members:
            print("No members yet.")
        for m in members:
            print(f"{m['id']:<4} {m['name']:<25} {m['email'] or '-'}")
    elif choice == "7":
        loan_id, due = lib.issue_book(ask_int("Book id: "), ask_int("Member id: "))
        print(f"Issued. Loan id {loan_id}, due on {due}.")
    elif choice == "8":
        fine = lib.return_book(ask_int("Loan id: "))
        print("Returned on time." if fine == 0 else
              f"Returned late. Fine: {fine} ({FINE_PER_DAY}/day).")
    elif choice == "9":
        print_loans(lib.list_loans())
    elif choice == "10":
        print_loans(lib.overdue_loans())
    else:
        print("Invalid choice.")


def main():
    lib = Library()
    try:
        while True:
            print(MENU)
            choice = input("Choose an option: ").strip()
            if choice == "0":
                print("Goodbye!")
                break
            try:
                handle(lib, choice)
            except LibraryError as err:
                print(f"Error: {err}")
    finally:
        lib.close()


if __name__ == "__main__":
    main()
