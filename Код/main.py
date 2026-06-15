import sys
import os
import re
import csv
import hashlib
from datetime import date, datetime
from io import StringIO

import mysql.connector
from mysql.connector import Error
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QDialog, QFormLayout, QDateEdit, QComboBox, QMessageBox,
    QGroupBox, QHeaderView, QTabWidget, QMenu,
    QFileDialog, QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt, QDate, QRegularExpression
from PySide6.QtGui import QColor, QRegularExpressionValidator, QAction, QBrush


STATUS_MAP = {
    'active': 'Активен',
    'on_vacation': 'В отпуске',
    'sick_leave': 'На больничном',
    'fired': 'Уволен'
}

STATUS_REV = {v: k for k, v in STATUS_MAP.items()}

COLOR_MAP = {
    'active': (40, 60, 40, 100, 255, 100),
    'on_vacation': (40, 40, 60, 100, 100, 255),
    'sick_leave': (60, 50, 30, 255, 200, 100),
    'fired': (60, 30, 30, 255, 100, 100)
}

STYLESHEET = """
QMainWindow, QDialog {
    background-color: #f0f0f0;
}
QLabel {
    color: #000000;
}
QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {
    padding: 8px;
    border: 1px solid #cccccc;
    border-radius: 4px;
    background-color: #ffffff;
    color: #000000;
}
QPushButton {
    padding: 8px 15px;
    border-radius: 4px;
    font-weight: bold;
    background-color: #e0e0e0;
    color: #000000;
}
QPushButton:hover {
    background-color: #d0d0d0;
}
QTableWidget {
    background-color: #ffffff;
    color: #000000;
    gridline-color: #dddddd;
}
QHeaderView::section {
    background-color: #e0e0e0;
    color: #000000;
    border-bottom: 2px solid #0078D7;
}
"""


class Database:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        self.connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', '127.0.0.1'),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', '12345')
        )
        self.execute(f"CREATE DATABASE IF NOT EXISTS hr", commit=True)
        self.execute("USE hr", commit=True)

        tables = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(50) UNIQUE,
                password_hash VARCHAR(255),
                role ENUM('admin','manager','viewer') DEFAULT 'viewer',
                full_name VARCHAR(100),
                is_active BOOLEAN DEFAULT TRUE,
                last_login TIMESTAMP NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS employees (
                id INT PRIMARY KEY AUTO_INCREMENT,
                last_name VARCHAR(100) NOT NULL,
                first_name VARCHAR(100) NOT NULL,
                patronymic VARCHAR(100),
                birth_date DATE,
                position VARCHAR(100),
                department VARCHAR(100),
                phone VARCHAR(20),
                email VARCHAR(100),
                hire_date DATE,
                salary DECIMAL(10,2),
                status ENUM('active','on_vacation','sick_leave','fired') DEFAULT 'active'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS vacations (
                id INT PRIMARY KEY AUTO_INCREMENT,
                employee_id INT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                type VARCHAR(50),
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
            )
            """
        ]

        for sql in tables:
            self.execute(sql, commit=True)

        self.create_default_admin()

    def execute(self, sql, params=None, commit=False):
        cursor = self.connection.cursor()
        cursor.execute(sql, params or ())

        if commit:
            self.connection.commit()
            result = cursor.lastrowid
        else:
            result = cursor.fetchall()

        cursor.close()
        return result

    def create_default_admin(self):
        if not self.execute("SELECT id FROM users WHERE username='admin'"):
            password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
            self.execute(
                "INSERT INTO users (username, password_hash, role, full_name) VALUES (%s, %s, 'admin', 'Администратор')",
                ('admin', password_hash),
                commit=True
            )

    def authenticate(self, username, password):
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user = self.execute(
            "SELECT * FROM users WHERE username=%s AND password_hash=%s AND is_active=1",
            (username, password_hash)
        )

        if user:
            self.execute(
                "UPDATE users SET last_login=NOW() WHERE id=%s",
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
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.execute(sql, data, commit=True)

    def get_employees(self, search=None):
        sql = "SELECT * FROM employees ORDER BY last_name"
        if search:
            sql = f"SELECT * FROM employees WHERE last_name LIKE '%{search}%' ORDER BY last_name"
        return self.execute(sql)

    def get_employee(self, employee_id):
        result = self.execute("SELECT * FROM employees WHERE id=%s", (employee_id,))
        return result[0] if result else None

    def update_employee(self, employee_id, data):
        sql = """
            UPDATE employees SET
                last_name=%s, first_name=%s, patronymic=%s, birth_date=%s,
                position=%s, department=%s, phone=%s, email=%s, hire_date=%s,
                salary=%s, status=%s
            WHERE id=%s
        """
        self.execute(sql, (*data, employee_id), commit=True)

    def delete_employee(self, employee_id):
        self.execute("DELETE FROM employees WHERE id=%s", (employee_id,), commit=True)

    def get_departments(self):
        result = self.execute(
            "SELECT DISTINCT department FROM employees WHERE department IS NOT NULL"
        )
        return [row[0] for row in result]

    def add_vacation(self, employee_id, start_date, end_date, vacation_type):
        sql = """
            INSERT INTO vacations (employee_id, start_date, end_date, type)
            VALUES (%s, %s, %s, %s)
        """
        self.execute(sql, (employee_id, start_date, end_date, vacation_type), commit=True)

    def get_vacations(self, employee_id):
        return self.execute(
            "SELECT * FROM vacations WHERE employee_id=%s ORDER BY start_date DESC",
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


def validate_name(name, field_name):
    if len(name.strip()) < 2:
        return False, f"{field_name} должен содержать минимум 2 символа"
    if not re.match(r'^[а-яёА-ЯЁa-zA-Z\-\'\s]+$', name):
        return False, f"{field_name} может содержать только буквы"
    return True, ""


def validate_birth_date(birth_date):
    today = date.today()
    birth = birth_date.toPython()
    age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

    if age < 16:
        return False, "Возраст должен быть не менее 16 лет"
    if age > 100:
        return False, "Возраст не может быть более 100 лет"
    return True, ""


def validate_salary(salary_text):
    if not salary_text.strip():
        return False, "Зарплата обязательна"

    try:
        salary = float(salary_text.replace(',', '.'))
    except ValueError:
        return False, "Зарплата должна быть числом"

    if salary < 16000:
        return False, "Зарплата не может быть меньше 16 000 рублей"
    if salary > 10000000:
        return False, "Зарплата не может быть больше 10 000 000 рублей"

    return True, ""


class LoginDialog(QDialog):
    def __init__(self, database):
        super().__init__()
        self.database = database
        self.authenticated_user = None
        self.setWindowTitle("Авторизация")
        self.setFixedSize(400, 250)
        self.setStyleSheet(STYLESHEET),
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title_label = QLabel("Вход в систему")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #0078D7;")
        layout.addWidget(title_label)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Логин")

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Пароль")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.returnPressed.connect(self.login)

        form_layout = QFormLayout()
        form_layout.addRow("Логин:", self.username_edit)
        form_layout.addRow("Пароль:", self.password_edit)
        layout.addLayout(form_layout)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff4444;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)

        login_button = QPushButton("Войти")
        login_button.clicked.connect(self.login)
        login_button.setStyleSheet("background-color: #0078D7; color: white; font-weight: bold;")
        layout.addWidget(login_button)

        info_label = QLabel("admin / admin123")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #888888;")
        layout.addWidget(info_label)

        self.setLayout(layout)

    def login(self):
        username = self.username_edit.text()
        password = self.password_edit.text()

        if not username or not password:
            self.error_label.setText("Введите логин и пароль")
            self.error_label.setVisible(True)
            return

        user = self.database.authenticate(username, password)

        if user:
            self.authenticated_user = user
            self.accept()
        else:
            self.error_label.setText("Неверный логин или пароль")
            self.error_label.setVisible(True)
            self.password_edit.clear()


class EmployeeDialog(QDialog):
    def __init__(self, parent, employee_id=None):
        super().__init__(parent)
        self.database = parent.database
        self.employee_id = employee_id
        self.setWindowTitle("Добавление сотрудника" if not employee_id else "Редактирование сотрудника")
        self.setMinimumWidth(500)
        self.setStyleSheet(STYLESHEET)
        self.init_ui()

        if employee_id:
            self.load_employee_data()

    def init_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.last_name_edit = QLineEdit()
        self.last_name_edit.setPlaceholderText("Иванов")
        form_layout.addRow("Фамилия:", self.last_name_edit)

        self.first_name_edit = QLineEdit()
        self.first_name_edit.setPlaceholderText("Иван")
        form_layout.addRow("Имя:", self.first_name_edit)

        self.patronymic_edit = QLineEdit()
        self.patronymic_edit.setPlaceholderText("Иванович")
        form_layout.addRow("Отчество:", self.patronymic_edit)

        self.birth_date_edit = QDateEdit()
        self.birth_date_edit.setCalendarPopup(True)
        self.birth_date_edit.setDate(QDate.currentDate().addYears(-30))
        form_layout.addRow("Дата рождения:", self.birth_date_edit)

        self.position_edit = QLineEdit()
        self.position_edit.setPlaceholderText("Инженер")
        form_layout.addRow("Должность:", self.position_edit)

        self.department_combo = QComboBox()
        self.department_combo.setEditable(True)
        form_layout.addRow("Отдел:", self.department_combo)

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("+7 (999) 123-45-67")
        form_layout.addRow("Телефон:", self.phone_edit)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("ivanov@example.com")
        form_layout.addRow("Email:", self.email_edit)

        self.hire_date_edit = QDateEdit()
        self.hire_date_edit.setCalendarPopup(True)
        self.hire_date_edit.setDate(QDate.currentDate())
        form_layout.addRow("Дата приема:", self.hire_date_edit)

        self.salary_edit = QLineEdit()
        self.salary_edit.setPlaceholderText("50000")
        form_layout.addRow("Зарплата:", self.salary_edit)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Активен", "В отпуске", "На больничном", "Уволен"])
        form_layout.addRow("Статус:", self.status_combo)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ff4444;")
        self.error_label.setVisible(False)
        form_layout.addRow(self.error_label)

        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_employee)
        save_button.setStyleSheet("background-color: #0078D7; color: white;")
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.load_departments()

    def load_departments(self):
        departments = self.database.get_departments()
        self.department_combo.addItem("")
        self.department_combo.addItems(departments)

    def load_employee_data(self):
        employee = self.database.get_employee(self.employee_id)

        if employee:
            self.last_name_edit.setText(employee[1])
            self.first_name_edit.setText(employee[2])
            self.patronymic_edit.setText(employee[3] or "")

            if employee[4]:
                date_value = QDate.fromString(str(employee[4]), "yyyy-MM-dd")
                self.birth_date_edit.setDate(date_value)

            self.position_edit.setText(employee[5] or "")

            index = self.department_combo.findText(employee[6] or "")
            if index >= 0:
                self.department_combo.setCurrentIndex(index)

            self.phone_edit.setText(employee[7] or "")
            self.email_edit.setText(employee[8] or "")

            if employee[9]:
                date_value = QDate.fromString(str(employee[9]), "yyyy-MM-dd")
                self.hire_date_edit.setDate(date_value)

            self.salary_edit.setText(str(employee[10]) if employee[10] else "")

            status_text = STATUS_MAP.get(employee[11], "Активен")
            index = self.status_combo.findText(status_text)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)

    def save_employee(self):
        last_name = self.last_name_edit.text().strip()
        first_name = self.first_name_edit.text().strip()
        patronymic = self.patronymic_edit.text().strip() or None
        birth_date = self.birth_date_edit.date().toString("yyyy-MM-dd")
        position = self.position_edit.text().strip() or None
        department = self.department_combo.currentText() or None
        phone = self.phone_edit.text().strip() or None
        email = self.email_edit.text().strip().lower() or None
        hire_date = self.hire_date_edit.date().toString("yyyy-MM-dd")
        salary_text = self.salary_edit.text().strip()
        status = STATUS_REV[self.status_combo.currentText()]

        is_valid, message = validate_name(last_name, "Фамилия")
        if not is_valid:
            self.error_label.setText(message)
            self.error_label.setVisible(True)
            return

        is_valid, message = validate_name(first_name, "Имя")
        if not is_valid:
            self.error_label.setText(message)
            self.error_label.setVisible(True)
            return

        is_valid, message = validate_birth_date(self.birth_date_edit)
        if not is_valid:
            self.error_label.setText(message)
            self.error_label.setVisible(True)
            return

        is_valid, message = validate_salary(salary_text)
        if not is_valid:
            self.error_label.setText(message)
            self.error_label.setVisible(True)
            return

        if not position:
            self.error_label.setText("Должность обязательна")
            self.error_label.setVisible(True)
            return

        salary = float(salary_text)

        data = (
            last_name, first_name, patronymic, birth_date, position,
            department, phone, email, hire_date, salary, status
        )

        try:
            if self.employee_id:
                self.database.update_employee(self.employee_id, data)
            else:
                self.database.add_employee(data)

            self.accept()
        except Exception as e:
            self.error_label.setText(f"Ошибка: {str(e)}")
            self.error_label.setVisible(True)


class VacationDialog(QDialog):
    def __init__(self, parent, employee_id):
        super().__init__(parent)
        self.database = parent.database
        self.employee_id = employee_id
        self.setWindowTitle("Добавление отпуска")
        self.setModal(True)
        self.setFixedSize(400, 250)
        self.setStyleSheet(STYLESHEET)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())
        form_layout.addRow("Дата начала:", self.start_date_edit)

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate().addDays(14))
        form_layout.addRow("Дата окончания:", self.end_date_edit)

        self.vacation_type_combo = QComboBox()
        self.vacation_type_combo.addItems(["Ежегодный", "Дополнительный", "Без содержания", "Учебный"])
        form_layout.addRow("Тип отпуска:", self.vacation_type_combo)

        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_vacation)
        save_button.setStyleSheet("background-color: #0078D7; color: white;")
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def save_vacation(self):
        start_date = self.start_date_edit.date()
        end_date = self.end_date_edit.date()

        if start_date > end_date:
            QMessageBox.warning(self, "Ошибка", "Дата окончания не может быть раньше даты начала")
            return

        start_date_str = start_date.toString("yyyy-MM-dd")
        end_date_str = end_date.toString("yyyy-MM-dd")
        vacation_type = self.vacation_type_combo.currentText()

        self.database.add_vacation(self.employee_id, start_date_str, end_date_str, vacation_type)
        self.accept()


class FilterWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.is_visible = False
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.filter_group = QGroupBox("Фильтры")
        self.filter_group.setVisible(False)
        self.filter_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                color: #ffffff;
                background-color: #2d2d2d;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #0078D7;
            }
        """)

        filter_layout = QVBoxLayout()

        row1_layout = QHBoxLayout()
        row1_layout.addWidget(QLabel("Статус:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("Все статусы", None)
        self.status_filter.addItem("Активен", "active")
        self.status_filter.addItem("В отпуске", "on_vacation")
        self.status_filter.addItem("На больничном", "sick_leave")
        self.status_filter.addItem("Уволен", "fired")
        self.status_filter.currentIndexChanged.connect(self.apply_filters)
        row1_layout.addWidget(self.status_filter)

        row1_layout.addWidget(QLabel("Отдел:"))
        self.department_filter = QComboBox()
        self.department_filter.addItem("Все отделы", None)
        self.department_filter.currentIndexChanged.connect(self.apply_filters)
        row1_layout.addWidget(self.department_filter)
        filter_layout.addLayout(row1_layout)

        row2_layout = QHBoxLayout()
        row2_layout.addWidget(QLabel("Поиск:"))
        self.search_filter = QLineEdit()
        self.search_filter.setPlaceholderText("Фамилия, имя, должность...")
        self.search_filter.textChanged.connect(self.apply_filters)
        row2_layout.addWidget(self.search_filter)
        filter_layout.addLayout(row2_layout)

        buttons_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Применить фильтры")
        self.apply_btn.clicked.connect(self.apply_filters)
        self.clear_btn = QPushButton("Сбросить фильтры")
        self.clear_btn.clicked.connect(self.clear_filters)
        self.export_csv_btn = QPushButton("Экспорт в CSV")
        self.export_csv_btn.clicked.connect(self.export_to_csv)

        buttons_layout.addWidget(self.apply_btn)
        buttons_layout.addWidget(self.clear_btn)
        buttons_layout.addWidget(self.export_csv_btn)
        buttons_layout.addStretch()

        filter_layout.addLayout(buttons_layout)
        self.filter_group.setLayout(filter_layout)
        main_layout.addWidget(self.filter_group)

        self.setLayout(main_layout)

    def load_departments(self):
        if self.main_window and self.main_window.database:
            self.department_filter.clear()
            self.department_filter.addItem("Все отделы", None)
            departments = self.main_window.database.get_departments()
            for dept in departments:
                if dept:
                    self.department_filter.addItem(dept, dept)

    def toggle_visibility(self):
        self.is_visible = not self.is_visible
        self.filter_group.setVisible(self.is_visible)
        return self.is_visible

    def get_filters(self):
        filters = {}
        status = self.status_filter.currentData()
        if status:
            filters['status'] = status

        department = self.department_filter.currentData()
        if department:
            filters['department'] = department

        search = self.search_filter.text().strip()
        if search:
            filters['search'] = search

        return filters

    def apply_filters(self):
        if self.main_window:
            self.main_window.load_employees()

    def clear_filters(self):
        self.status_filter.setCurrentIndex(0)
        self.department_filter.setCurrentIndex(0)
        self.search_filter.clear()
        self.apply_filters()

    def export_to_csv(self):
        if not self.main_window:
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self, "Экспорт в CSV", "employees.csv",
            "CSV files (*.csv);;All files (*.*)"
        )

        if file_name:
            try:
                filters = self.get_filters()
                csv_data = self.main_window.database.export_to_csv(filters)

                with open(file_name, 'w', encoding='utf-8-sig') as f:
                    f.write(csv_data)

                QMessageBox.information(self, "Успех", f"Данные экспортированы в {file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта: {str(e)}")


class HRApp(QMainWindow):
    def __init__(self, database, user):
        super().__init__()
        self.database = database
        self.user = user
        self.filter_visible = False
        self.filter_widget = None
        self.setWindowTitle(f"Система кадрового учета - {user['full_name']}")
        self.setGeometry(100, 100, 1400, 800)
        self.setStyleSheet(STYLESHEET)
        self.init_ui()
        self.load_employees()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Добавить")
        self.add_button.clicked.connect(self.add_employee)
        button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Редактировать")
        self.edit_button.clicked.connect(self.edit_employee)
        button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Удалить")
        self.delete_button.clicked.connect(self.delete_employee)
        button_layout.addWidget(self.delete_button)

        self.vacation_button = QPushButton("Отпуск")
        self.vacation_button.clicked.connect(self.add_vacation)
        button_layout.addWidget(self.vacation_button)

        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.clicked.connect(self.load_employees)
        button_layout.addWidget(self.refresh_button)

        self.stats_button = QPushButton("Статистика")
        self.stats_button.clicked.connect(self.show_statistics)
        button_layout.addWidget(self.stats_button)

        self.filter_toggle_btn = QPushButton("Фильтры")
        self.filter_toggle_btn.setCheckable(True)
        self.filter_toggle_btn.clicked.connect(self.toggle_filters)
        button_layout.addWidget(self.filter_toggle_btn)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.filter_widget = FilterWidget(self)
        main_layout.addWidget(self.filter_widget)

        self.employee_table = QTableWidget()
        self.employee_table.setColumnCount(11)
        self.employee_table.setHorizontalHeaderLabels([
            "ID", "Фамилия", "Имя", "Отчество", "Возраст",
            "Должность", "Отдел", "Телефон", "Email", "Дата приема", "Статус"
        ])
        self.employee_table.horizontalHeader().setStretchLastSection(True)
        self.employee_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.employee_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.employee_table.doubleClicked.connect(self.view_details)
        self.employee_table.setAlternatingRowColors(True)
        main_layout.addWidget(self.employee_table)

        self.status_label = QLabel("Готов")
        self.status_label.setStyleSheet("font-weight: bold; color: #0078D7;")
        main_layout.addWidget(self.status_label)

        self.filter_widget.load_departments()
        self.update_statistics()

    def toggle_filters(self):
        self.filter_visible = self.filter_widget.toggle_visibility()
        if self.filter_visible:
            self.filter_toggle_btn.setText("Скрыть фильтры")
            self.filter_toggle_btn.setStyleSheet("background-color: #0078D7; color: white;")
        else:
            self.filter_toggle_btn.setText("Фильтры")
            self.filter_toggle_btn.setStyleSheet("")
            self.filter_widget.clear_filters()

    def load_employees(self):
        filters = self.filter_widget.get_filters() if self.filter_visible else None
        employees = self.database.get_employees()
        self.update_table(employees)

    def update_table(self, employees):
        self.employee_table.setRowCount(len(employees))

        today = date.today()

        for row, employee in enumerate(employees):
            self.employee_table.setItem(row, 0, QTableWidgetItem(str(employee[0])))
            self.employee_table.setItem(row, 1, QTableWidgetItem(employee[1]))
            self.employee_table.setItem(row, 2, QTableWidgetItem(employee[2]))
            self.employee_table.setItem(row, 3, QTableWidgetItem(employee[3] or ""))

            if employee[4]:
                birth_date = employee[4]
                age = today.year - birth_date.year - (
                    (today.month, today.day) < (birth_date.month, birth_date.day)
                )
                self.employee_table.setItem(row, 4, QTableWidgetItem(str(age)))
            else:
                self.employee_table.setItem(row, 4, QTableWidgetItem(""))

            self.employee_table.setItem(row, 5, QTableWidgetItem(employee[5] or ""))
            self.employee_table.setItem(row, 6, QTableWidgetItem(employee[6] or ""))
            self.employee_table.setItem(row, 7, QTableWidgetItem(employee[7] or ""))
            self.employee_table.setItem(row, 8, QTableWidgetItem(employee[8] or ""))
            self.employee_table.setItem(row, 9, QTableWidgetItem(str(employee[9]) if employee[9] else ""))

            status_text = STATUS_MAP.get(employee[11], employee[11])
            status_item = QTableWidgetItem(status_text)

            colors = COLOR_MAP.get(employee[11], (30, 30, 30, 255, 255, 255))
            background_color = QColor(colors[0], colors[1], colors[2])
            text_color = QColor(colors[3], colors[4], colors[5])

            for column in range(self.employee_table.columnCount()):
                item = self.employee_table.item(row, column)
                if item:
                    item.setBackground(QBrush(background_color))
                    item.setForeground(QBrush(QColor(255, 255, 255)))

            status_item.setForeground(text_color)
            status_item.setBackground(QBrush(background_color))
            self.employee_table.setItem(row, 10, status_item)

        self.employee_table.resizeColumnsToContents()
        self.update_statistics()

    def update_statistics(self):
        stats = self.database.get_statistics()
        visible_rows = self.employee_table.rowCount()

        self.status_label.setText(
            f"{self.user['full_name']} | "
            f"Отображается: {visible_rows} | "
            f"Всего: {stats['total']} | "
            f"Активны: {stats['active']} | "
            f"В отпуске: {stats['on_vacation']} | "
            f"На больничном: {stats['sick_leave']} | "
            f"Уволены: {stats['fired']}"
        )

    def get_current_employee_id(self):
        current_row = self.employee_table.currentRow()
        if current_row >= 0:
            return int(self.employee_table.item(current_row, 0).text())
        return None

    def add_employee(self):
        dialog = EmployeeDialog(self)
        if dialog.exec():
            self.load_employees()
            self.filter_widget.load_departments()

    def edit_employee(self):
        employee_id = self.get_current_employee_id()
        if not employee_id:
            QMessageBox.warning(self, "Ошибка", "Выберите сотрудника")
            return

        dialog = EmployeeDialog(self, employee_id)
        if dialog.exec():
            self.load_employees()
            self.filter_widget.load_departments()

    def delete_employee(self):
        employee_id = self.get_current_employee_id()
        if not employee_id:
            QMessageBox.warning(self, "Ошибка", "Выберите сотрудника")
            return

        reply = QMessageBox.question(
            self, "Удаление", "Удалить выбранного сотрудника?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.database.delete_employee(employee_id)
            self.load_employees()
            self.filter_widget.load_departments()

    def add_vacation(self):
        employee_id = self.get_current_employee_id()
        if not employee_id:
            QMessageBox.warning(self, "Ошибка", "Выберите сотрудника")
            return

        dialog = VacationDialog(self, employee_id)
        if dialog.exec():
            self.load_employees()

    def view_details(self, index):
        row = index.row()
        employee_id = int(self.employee_table.item(row, 0).text())
        employee = self.database.get_employee(employee_id)

        if not employee:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Информация - {employee[1]} {employee[2]}")
        dialog.setMinimumWidth(500)
        dialog.setStyleSheet(STYLESHEET)

        layout = QVBoxLayout()
        tabs = QTabWidget()

        basic_tab = QWidget()
        basic_layout = QFormLayout(basic_tab)

        age = ""
        if employee[4]:
            today = date.today()
            birth = employee[4]
            age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

        info_data = [
            ("Фамилия:", employee[1]),
            ("Имя:", employee[2]),
            ("Отчество:", employee[3] or "—"),
            ("Дата рождения:", str(employee[4]) if employee[4] else "—"),
            ("Возраст:", f"{age} лет" if age else "—"),
            ("Должность:", employee[5] or "—"),
            ("Отдел:", employee[6] or "—"),
            ("Телефон:", employee[7] or "—"),
            ("Email:", employee[8] or "—"),
            ("Дата приема:", str(employee[9]) if employee[9] else "—"),
            ("Зарплата:", f"{employee[10]:,.2f} руб." if employee[10] else "—"),
            ("Статус:", STATUS_MAP.get(employee[11], employee[11]))
        ]

        for label, value in info_data:
            label_widget = QLabel(label)
            label_widget.setStyleSheet("font-weight: bold; color: #0078D7;")
            value_widget = QLabel(str(value))
            basic_layout.addRow(label_widget, value_widget)

        tabs.addTab(basic_tab, "Основная информация")

        vacation_tab = QWidget()
        vacation_layout = QVBoxLayout(vacation_tab)

        vacation_table = QTableWidget()
        vacation_table.setColumnCount(3)
        vacation_table.setHorizontalHeaderLabels(["Начало", "Окончание", "Тип"])

        vacations = self.database.get_vacations(employee_id)
        vacation_table.setRowCount(len(vacations))

        for vacation_row, vacation in enumerate(vacations):
            vacation_table.setItem(vacation_row, 0, QTableWidgetItem(str(vacation[2])))
            vacation_table.setItem(vacation_row, 1, QTableWidgetItem(str(vacation[3])))
            vacation_table.setItem(vacation_row, 2, QTableWidgetItem(vacation[4] or "—"))

        vacation_layout.addWidget(vacation_table)
        tabs.addTab(vacation_tab, "Отпуска")

        layout.addWidget(tabs)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.setLayout(layout)
        dialog.exec()

    def show_statistics(self):
        stats = self.database.get_statistics()
        QMessageBox.information(
            self, "Статистика",
            f"Всего сотрудников: {stats['total']}\n"
            f"Активных: {stats['active']}\n"
            f"В отпуске: {stats['on_vacation']}\n"
            f"На больничном: {stats['sick_leave']}\n"
            f"Уволенных: {stats['fired']}"
        )

    def closeEvent(self, event):
        self.database.close()
        event.accept()


def main():
    application = QApplication(sys.argv)
    application.setStyle('Windows')

    database = Database()

    login_dialog = LoginDialog(database)
    if login_dialog.exec() != QDialog.Accepted:
        sys.exit(0)

    user = login_dialog.authenticated_user
    main_window = HRApp(database, user)
    main_window.show()

    sys.exit(application.exec())


if __name__ == '__main__':
    main()