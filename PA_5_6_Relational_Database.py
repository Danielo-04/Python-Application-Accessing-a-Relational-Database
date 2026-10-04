# Name: Daniel Baez-Perez
# Assignment: 5.6 Performance Assessment - Python Application Accessing a Relational Database
# Date: 10/03/2026
# Purpose: Import JSON review data into SQLite and perform CRUD/database operations.

import sqlite3
import json
import glob
from datetime import datetime

DB_NAME = "EN_ReviewData.db"


# Locate the dataset in the same folder as this Python file.
def get_dataset():
    files = sorted(glob.glob("dataset_en_dev*.json"))
    if not files:
        print("ERROR: Put dataset_en_dev.json in the same folder as this program.")
        return None
    return files[0]


# Create the four required relational tables.
def create_tables(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Reviewers (
            reviewer_id TEXT PRIMARY KEY
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Categories (
            product_category TEXT PRIMARY KEY
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Products (
            product_id TEXT PRIMARY KEY,
            product_category TEXT,
            FOREIGN KEY (product_category)
                REFERENCES Categories(product_category)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Reviews (
            review_id TEXT PRIMARY KEY,
            product_id TEXT,
            reviewer_id TEXT,
            stars INTEGER,
            review_body TEXT,
            review_title TEXT,
            FOREIGN KEY (product_id)
                REFERENCES Products(product_id),
            FOREIGN KEY (reviewer_id)
                REFERENCES Reviewers(reviewer_id)
        )
    """)


# Import the JSON dataset only when the Reviews table is empty.
def import_data(conn, cur, filename):
    cur.execute("SELECT COUNT(*) FROM Reviews")
    if cur.fetchone()[0] != 0:
        return

    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            row = json.loads(line)

            cur.execute(
                "INSERT OR IGNORE INTO Reviewers VALUES (?)",
                (row["reviewer_id"],)
            )

            cur.execute(
                "INSERT OR IGNORE INTO Categories VALUES (?)",
                (row["product_category"],)
            )

            cur.execute(
                "INSERT OR IGNORE INTO Products VALUES (?, ?)",
                (row["product_id"], row["product_category"])
            )

            cur.execute("""
                INSERT OR IGNORE INTO Reviews
                (review_id, product_id, reviewer_id, stars, review_body, review_title)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                row["review_id"],
                row["product_id"],
                row["reviewer_id"],
                int(row["stars"]),
                row["review_body"],
                row["review_title"]
            ))

    conn.commit()


def show_menu():
    print()
    print("Type in a number and press enter to execute the menu option.")
    print("1. Insert a new record")
    print("2. Display product count per category")
    print("3. Enter a query")
    print("4. Delete reviews from a category")
    print("5. Delete all tables")
    print("6. Exit the program")


def insert_record(conn, cur):
    print()
    print("Type in a number to insert into the associated table:")
    print("1. Reviews")
    print("2. Reviewers")
    print("3. Products")
    print("4. Categories")
    choice = input()

    try:
        if choice == "1":
            review_id = input("Enter the ID of the Review:\n")
            product_id = input("Enter the ID of the Product:\n")
            reviewer_id = input("Enter the ID of the Reviewer:\n")
            stars = int(input("Enter the number of Stars:\n"))
            title = input("Enter the Title:\n")
            body = input("Enter the Content:\n")

            cur.execute("""
                INSERT INTO Reviews
                (review_id, product_id, reviewer_id, stars, review_body, review_title)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (review_id, product_id, reviewer_id, stars, body, title))

        elif choice == "2":
            reviewer_id = input("Enter the Reviewer ID:\n")
            cur.execute("INSERT INTO Reviewers VALUES (?)", (reviewer_id,))

        elif choice == "3":
            product_id = input("Enter the Product ID:\n")
            category = input("Enter the Product Category:\n")
            cur.execute("INSERT INTO Products VALUES (?, ?)", (product_id, category))

        elif choice == "4":
            category = input("Enter the Product Category:\n")
            cur.execute("INSERT INTO Categories VALUES (?)", (category,))

        else:
            print("Invalid selection.")
            return

        conn.commit()
        print("Record inserted successfully!")

    except (sqlite3.Error, ValueError) as e:
        print("Error:", e)


def product_count(cur):
    try:
        minimum = int(input("\nWhat is the minimum product count?\n"))
    except ValueError:
        print("Please enter a whole number.")
        return

    cur.execute("""
        SELECT product_category, COUNT(*) AS product_count
        FROM Products
        GROUP BY product_category
        HAVING COUNT(*) >= ?
        ORDER BY product_category
    """, (minimum,))

    print()
    print(f"Displaying Categories with {minimum}+ products:")
    for row in cur.fetchall():
        print(row)


def run_select(cur):
    query = input("\nEnter the query you wish to run on the EN_ReviewData database:\n")

    if not query.strip().lower().startswith("select"):
        print("Only SELECT statements are allowed here.")
        return

    try:
        cur.execute(query)
        for row in cur.fetchall():
            print(row)
    except sqlite3.Error as e:
        print("SQL error:", e)


def delete_category_reviews(conn, cur):
    category = input(
        "\nEnter the name of the product category to remove reviews from:\n"
    )

    cur.execute("SELECT COUNT(*) FROM Reviews")
    before = cur.fetchone()

    cur.execute("""
        DELETE FROM Reviews
        WHERE product_id IN (
            SELECT product_id
            FROM Products
            WHERE product_category = ?
        )
    """, (category,))

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM Reviews")
    after = cur.fetchone()

    print("Previous Review Count:")
    print(before)
    print("Current Review Count:")
    print(after)


def delete_tables(conn, cur):
    print("\nRemoving the Tables from the database...")
    cur.execute("DROP TABLE IF EXISTS Reviews")
    cur.execute("DROP TABLE IF EXISTS Products")
    cur.execute("DROP TABLE IF EXISTS Reviewers")
    cur.execute("DROP TABLE IF EXISTS Categories")
    conn.commit()
    print("Complete!")


def main():
    dataset = get_dataset()
    if dataset is None:
        return

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")

    create_tables(cur)
    conn.commit()
    import_data(conn, cur, dataset)

    # The assignment requires the screenshot to show the system date/time.
    print("System Date and Time:", datetime.now().strftime("%m/%d/%Y %I:%M:%S %p"))

    while True:
        show_menu()
        choice = input()

        if choice == "1":
            insert_record(conn, cur)
        elif choice == "2":
            product_count(cur)
        elif choice == "3":
            run_select(cur)
        elif choice == "4":
            delete_category_reviews(conn, cur)
        elif choice == "5":
            delete_tables(conn, cur)
            break
        elif choice == "6":
            print("Exiting program.")
            break
        else:
            print("Invalid selection. Enter 1 through 6.")

    conn.close()


if __name__ == "__main__":
    main()
