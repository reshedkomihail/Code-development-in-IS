import os
import csv
import hashlib
import sqlite3
from io import StringIO

from styles import STATUS_MAP


class Database:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        db_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(db_dir, 'hr_database.db')
        
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        
        self.execute("PRAGMA foreign_keys = ON", commit=True)
        
        tables = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password_hash TEXT,
                role TEXT CHECK(role IN ('admin','manager','viewer')) DEFAULT 'viewer',
                full_name TEXT,
                is_active INTEGER DEFAULT 1,
                last_login TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_name TEXT NOT NULL,
                first_name TEXT NOT NULL,
                patronymic TEXT,
                birth_date DATE,
                position TEXT,
                department TEXT,
                phone TEXT,
                email TEXT,
                hire_date DATE,
                salary DECIMAL(10,2),
                status TEXT CHECK(status IN ('active','on_vacation','sick_leave','fired')) DEFAULT 'active'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS vacations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                type TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
            )
            """
        ]

        for sql in tables:
            self.execute(sql, commit=True)

        self.create_default_admin()

    def execute(self, sql, params=None, commit=False):
        cursor = self.connection.cursor()
        
        if params is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql, params)
        
        if commit:
            self.connection.commit()
            result = cursor.lastrowid
        else:
            result = cursor.fetchall()
            if result and isinstance(result[0], sqlite3.Row):
                result = [list(row) for row in result]
        
        cursor.close()
        return result

    def create_default_admin(self):
        if not self.execute("SELECT id FROM users WHERE username='admin'"):
            password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
            self.execute(
                "INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, 'admin', 'Администратор')",
                ('admin', password_hash),
                commit=True
            )

    def authenticate(self, username, password):
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user = self.execute(
            "SELECT * FROM users WHERE username=? AND password_hash=? AND is_active=1",
            (username, password_hash)
        )

        if user:
            self.execute(
                "UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=?",
                (user[0][0],),
                commit=True
            )
            return {
                'id': user[0][0],
                'username': user[0][1],
                'role': user[0][3],
                'full_name': user[0][4]
            }

        return None

    def add_employee(self, data):
        sql = """
            INSERT INTO employees (
                last_name, first_name, patronymic, birth_date,
                position, department, phone, email, hire_date, salary, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute(sql, data, commit=True)

    def get_employees(self, search=None, status_filter=None, department_filter=None):
        conditions = []
        params = []
        
        if search:
            conditions.append("(last_name LIKE ? OR first_name LIKE ? OR position LIKE ?)")
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])
        
        if status_filter:
            conditions.append("status = ?")
            params.append(status_filter)
        
        if department_filter:
            conditions.append("department = ?")
            params.append(department_filter)
        
        if conditions:
            sql = f"SELECT * FROM employees WHERE {' AND '.join(conditions)} ORDER BY last_name"
            return self.execute(sql, params)
        else:
            sql = "SELECT * FROM employees ORDER BY last_name"
            return self.execute(sql)

    def get_employee(self, employee_id):
        result = self.execute("SELECT * FROM employees WHERE id=?", (employee_id,))
        return result[0] if result else None

    def update_employee(self, employee_id, data):
        sql = """
            UPDATE employees SET
                last_name=?, first_name=?, patronymic=?, birth_date=?,
                position=?, department=?, phone=?, email=?, hire_date=?,
                salary=?, status=?
            WHERE id=?
        """
        self.execute(sql, (*data, employee_id), commit=True)

    def delete_employee(self, employee_id):
        self.execute("DELETE FROM employees WHERE id=?", (employee_id,), commit=True)

    def get_departments(self):
        result = self.execute(
            "SELECT DISTINCT department FROM employees WHERE department IS NOT NULL"
        )
        return [row[0] for row in result]

    def add_vacation(self, employee_id, start_date, end_date, vacation_type):
        sql = """
            INSERT INTO vacations (employee_id, start_date, end_date, type)
            VALUES (?, ?, ?, ?)
        """
        return self.execute(sql, (employee_id, start_date, end_date, vacation_type), commit=True)

    def update_vacation(self, vacation_id, start_date, end_date, vacation_type):
        sql = """
            UPDATE vacations SET
                start_date=?, end_date=?, type=?
            WHERE id=?
        """
        self.execute(sql, (start_date, end_date, vacation_type, vacation_id), commit=True)

    def delete_vacation(self, vacation_id):
        self.execute("DELETE FROM vacations WHERE id=?", (vacation_id,), commit=True)

    def get_vacation(self, vacation_id):
        result = self.execute("SELECT * FROM vacations WHERE id=?", (vacation_id,))
        return result[0] if result else None

    def get_vacations(self, employee_id):
        return self.execute(
            "SELECT * FROM vacations WHERE employee_id=? ORDER BY start_date DESC",
            (employee_id,)
        )

    def get_statistics(self):
        stats = {}
        stats['total'] = self.execute("SELECT COUNT(*) FROM employees")[0][0]
        stats['active'] = self.execute("SELECT COUNT(*) FROM employees WHERE status='active'")[0][0]
        stats['on_vacation'] = self.execute("SELECT COUNT(*) FROM employees WHERE status='on_vacation'")[0][0]
        stats['sick_leave'] = self.execute("SELECT COUNT(*) FROM employees WHERE status='sick_leave'")[0][0]
        stats['fired'] = self.execute("SELECT COUNT(*) FROM employees WHERE status='fired'")[0][0]
        return stats

    def export_to_csv(self, filters=None):
        employees = self.get_employees()
        output = StringIO()
        writer = csv.writer(output)

        writer.writerow(['ID', 'Фамилия', 'Имя', 'Отчество', 'Дата рождения',
                         'Должность', 'Отдел', 'Телефон', 'Email', 'Дата приема',
                         'Зарплата', 'Статус'])

        for emp in employees:
            writer.writerow([
                emp[0], emp[1], emp[2], emp[3] or '', emp[4] or '',
                emp[5] or '', emp[6] or '', emp[7] or '', emp[8] or '',
                emp[9] or '', emp[10] or '', STATUS_MAP.get(emp[11], emp[11])
            ])

        return output.getvalue()

    def close(self):
        if self.connection:
            self.connection.close()