"""
Модуль с тестами для функций работы с базой данных.
"""
import unittest
import sqlite3
import os


class TestDatabase(unittest.TestCase):
    """Тесты для функций работы с БД библиотеки."""

    def setUp(self):
        """
        Выполняется ПЕРЕД каждым тестом.
        Создаёт чистую тестовую базу данных.
        """
        if os.path.exists('test_library.db'):
            os.remove('test_library.db')
        self.conn = sqlite3.connect('test_library.db')
        cursor = self.conn.cursor()

        cursor.execute('''
        CREATE TABLE books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            year INTEGER,
            quantity INTEGER DEFAULT 1
        )
        ''')

        cursor.execute('''
        CREATE TABLE readers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_name TEXT NOT NULL,
            first_name TEXT NOT NULL,
            student_card TEXT UNIQUE NOT NULL,
            group_name TEXT,
            phone TEXT
        )
        ''')

        cursor.execute('''
        CREATE TABLE issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            reader_id INTEGER NOT NULL,
            issue_date DATE NOT NULL,
            due_date DATE NOT NULL,
            return_date DATE,
            FOREIGN KEY (book_id) REFERENCES books (id),
            FOREIGN KEY (reader_id) REFERENCES readers (id)
        )
        ''')

        self.conn.commit()

    def tearDown(self):
        """
        Выполняется ПОСЛЕ каждого теста.
        Закрывает соединение и удаляет тестовую БД.
        """
        self.conn.close()
        if os.path.exists('test_library.db'):
            os.remove('test_library.db')

    # ==========================================
    # ТЕСТЫ ДЛЯ ТАБЛИЦЫ BOOKS
    # ==========================================

    def test_add_book(self):
        """Проверяет добавление книги в БД."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO books (title, author, year, quantity) VALUES (?, ?, ?, ?)",
            ('Война и мир', 'Лев Толстой', 1869, 3)
        )
        self.conn.commit()
        cursor.execute("SELECT * FROM books WHERE title = 'Война и мир'")
        book = cursor.fetchone()

        self.assertIsNotNone(book, "Книга должна быть найдена в БД")
        self.assertEqual(book[1], 'Война и мир')
        self.assertEqual(book[2], 'Лев Толстой')
        self.assertEqual(book[3], 1869)
        self.assertEqual(book[4], 3)

    def test_book_count(self):
        """Проверяет количество книг в БД."""
        cursor = self.conn.cursor()
        books = [
            ('Книга 1', 'Автор 1', 2000, 1),
            ('Книга 2', 'Автор 2', 2001, 2),
            ('Книга 3', 'Автор 3', 2002, 3),
        ]
        cursor.executemany(
            "INSERT INTO books (title, author, year, quantity) VALUES (?, ?, ?, ?)",
            books
        )
        self.conn.commit()

        cursor.execute("SELECT COUNT(*) FROM books")
        count = cursor.fetchone()[0]

        self.assertEqual(count, 3, "В БД должно быть 3 книги")

    def test_delete_book(self):
        """Проверяет удаление книги."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO books (title, author, year, quantity) VALUES (?, ?, ?, ?)",
            ('Тестовая книга', 'Тестовый автор', 2024, 1)
        )
        self.conn.commit()
        book_id = cursor.lastrowid

        cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
        self.conn.commit()

        cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        book = cursor.fetchone()

        self.assertIsNone(book, "Книга должна быть удалена")

    # ==========================================
    # ТЕСТЫ ДЛЯ ТАБЛИЦЫ READERS
    # ==========================================

    def test_add_reader(self):
        """Проверяет добавление читателя."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO readers (last_name, first_name, student_card, group_name, phone) "
            "VALUES (?, ?, ?, ?, ?)",
            ('Антонов', 'Артём', 'СБ-101', '3ИСП4', '+7-916-111-22-33')
        )
        self.conn.commit()

        cursor.execute("SELECT * FROM readers WHERE student_card = 'СБ-101'")
        reader = cursor.fetchone()
        self.assertIsNotNone(reader)
        self.assertEqual(reader[1], 'Антонов')
        self.assertEqual(reader[3], 'СБ-101')  # индекс 3 - student_card

    def test_unique_student_card(self):
        """Проверяет, что студенческий билет уникален."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO readers (last_name, first_name, student_card) VALUES (?, ?, ?)",
            ('Антонов', 'Артём', 'СБ-101')
        )
        self.conn.commit()

        # второй читатель с тем же билетом должен вызвать ошибку
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO readers (last_name, first_name, student_card) VALUES (?, ?, ?)",
                ('Петров', 'Пётр', 'СБ-101')
            )

    # ==========================================
    # ТЕСТЫ ДЛЯ ТАБЛИЦЫ ISSUES
    # ==========================================

    def test_issue_book(self):
        """Проверяет оформление выдачи книги."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO books (title, author, year, quantity) VALUES (?, ?, ?, ?)",
            ('Война и мир', 'Лев Толстой', 1869, 3)
        )
        book_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO readers (last_name, first_name, student_card) VALUES (?, ?, ?)",
            ('Антонов', 'Артём', 'СБ-101')
        )
        reader_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO issues (book_id, reader_id, issue_date, due_date) VALUES (?, ?, ?, ?)",
            (book_id, reader_id, '2026-09-01', '2026-10-01')
        )
        self.conn.commit()

        cursor.execute("SELECT COUNT(*) FROM issues")
        count = cursor.fetchone()[0]

        self.assertEqual(count, 1, "Должна быть 1 выдача")

    def test_return_book(self):
        """Проверяет оформление возврата книги."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO books (title, author, year, quantity) VALUES (?, ?, ?, ?)",
            ('Тестовая книга', 'Автор', 2024, 1)
        )
        book_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO readers (last_name, first_name, student_card) VALUES (?, ?, ?)",
            ('Антонов', 'Артём', 'СБ-101')
        )
        reader_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO issues (book_id, reader_id, issue_date, due_date) VALUES (?, ?, ?, ?)",
            (book_id, reader_id, '2026-09-01', '2026-10-01')
        )
        issue_id = cursor.lastrowid
        self.conn.commit()

        # оформляем возврат
        cursor.execute(
            "UPDATE issues SET return_date = ? WHERE id = ?",
            ('2026-09-15', issue_id)
        )
        self.conn.commit()

        cursor.execute("SELECT return_date FROM issues WHERE id = ?", (issue_id,))
        return_date = cursor.fetchone()[0]

        self.assertEqual(return_date, '2026-09-15')


if __name__ == '__main__':
    unittest.main()


class TestSearch(unittest.TestCase):
    """Тесты для поиска данных."""

    def setUp(self):
        self.conn = sqlite3.connect(':memory:')  # БД в оперативной памяти
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            year INTEGER,
            quantity INTEGER DEFAULT 1
        )
        ''')
        books = [
            ('Война и мир', 'Лев Толстой', 1869, 3),
            ('Анна Каренина', 'Лев Толстой', 1877, 2),
            ('Преступление и наказание', 'Федор Достоевский', 1866, 1),
        ]
        cursor.executemany(
            "INSERT INTO books (title, author, year, quantity) VALUES (?, ?, ?, ?)",
            books
        )
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_search_by_author_tolstoy(self):
        """Поиск книг Льва Толстого."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM books WHERE author LIKE ?", ('%Толстой%',))
        books = cursor.fetchall()

        self.assertEqual(len(books), 2, "Должно быть 2 книги Толстого")

    def test_search_by_author_not_found(self):
        """Поиск несуществующего автора."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM books WHERE author LIKE ?", ('%Пушкин%',))
        books = cursor.fetchall()

        self.assertEqual(len(books), 0, "Книг Пушкина нет в БД")

    def test_search_partial_name(self):
        """Поиск по части фамилии (своя проверка)."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT title FROM books WHERE author LIKE ?", ('%Достоев%',))
        titles = [row[0] for row in cursor.fetchall()]

        self.assertTrue('Преступление и наказание' in titles)
