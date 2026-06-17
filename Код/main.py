import sys
import re
from datetime import date, datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QDialog, QFormLayout, QDateEdit, QComboBox, QMessageBox,
    QGroupBox, QHeaderView, QTabWidget, QMenu,
    QFileDialog, QSpinBox, QDoubleSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, QDate, QRegularExpression
from PySide6.QtGui import QColor, QRegularExpressionValidator, QAction, QBrush, QFont

from styles import STATUS_MAP, STATUS_REV, COLOR_MAP, STYLESHEET
from database import Database


def format_date(date_str):
    """Форматирует дату из YYYY-MM-DD в ДД.ММ.ГГГГ"""
    if not date_str:
        return "—"
    try:
        date_obj = datetime.strptime(str(date_str), "%Y-%m-%d")
        return date_obj.strftime("%d.%m.%Y")
    except:
        return str(date_str)


def validate_name(name, field_name):
    if len(name.strip()) < 2:
        return False, f"{field_name} должен содержать минимум 2 символа"
    if not re.match(r'^[а-яёА-ЯЁa-zA-Z\-\'\s]+$', name):
        return False, f"{field_name} может содержать только буквы"
    return True, ""


def validate_patronymic(patronymic):
    if not patronymic:
        return True, ""
    
    patronymic = patronymic.strip()
    if len(patronymic) < 2:
        return False, "Отчество должно содержать минимум 2 символа"
    if not re.match(r'^[а-яёА-ЯЁa-zA-Z\-\'\s]+$', patronymic):
        return False, "Отчество может содержать только буквы"
    return True, ""


def validate_birth_date(date_edit):
    qdate = date_edit.date()
    birth_date = qdate.toPython()
    today = date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

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


def validate_phone(phone_text):
    if not phone_text:
        return True, ""
    
    phone_text = str(phone_text).strip()
    if not phone_text:
        return True, ""
    
    clean_phone = re.sub(r'[\s\-\(\)]', '', phone_text)
    
    patterns = [
        r'^\+7\d{10}$',
        r'^8\d{10}$',
        r'^7\d{10}$',
        r'^\d{10}$'
    ]
    
    for pattern in patterns:
        if re.match(pattern, clean_phone):
            return True, ""
    
    return False, "Неверный формат телефона. Используйте +7XXXXXXXXXX или 8XXXXXXXXXX"


def validate_email(email_text):
    if not email_text:
        return True, ""
    
    email_text = str(email_text).strip()
    if not email_text:
        return True, ""
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if re.match(pattern, email_text):
        return True, ""
    
    return False, "Неверный формат email. Пример: user@example.com"


class LoginDialog(QDialog):
    def __init__(self, database):
        super().__init__()
        self.database = database
        self.authenticated_user = None
        self.setWindowTitle("Авторизация")
        self.setFixedSize(450, 350)
        self.setStyleSheet(STYLESHEET)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        title_label = QLabel("Система кадрового учета")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            color: #4a90d9;
            padding: 10px;
        """)
        layout.addWidget(title_label)

        subtitle_label = QLabel("Вход в систему")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("font-size: 14px; color: #6aafee; margin-bottom: 10px;")
        layout.addWidget(subtitle_label)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Введите логин")
        self.username_edit.setStyleSheet("padding: 10px; font-size: 14px;")

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Введите пароль")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setStyleSheet("padding: 10px; font-size: 14px;")
        self.password_edit.returnPressed.connect(self.login)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.addRow("Логин:", self.username_edit)
        form_layout.addRow("Пароль:", self.password_edit)
        layout.addLayout(form_layout)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)

        login_button = QPushButton("Войти")
        login_button.setObjectName("primaryButton")
        login_button.clicked.connect(self.login)
        login_button.setStyleSheet("""
            QPushButton {
                padding: 12px;
                font-size: 16px;
                border-radius: 4px;
            }
        """)
        layout.addWidget(login_button)

        layout.addStretch()
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
        self.setMinimumWidth(550)
        self.setStyleSheet(STYLESHEET)
        self.init_ui()

        if employee_id:
            self.load_employee_data()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.last_name_edit = QLineEdit()
        self.last_name_edit.setPlaceholderText("Иванов")
        form_layout.addRow("Фамилия *:", self.last_name_edit)

        self.first_name_edit = QLineEdit()
        self.first_name_edit.setPlaceholderText("Иван")
        form_layout.addRow("Имя *:", self.first_name_edit)

        self.patronymic_edit = QLineEdit()
        self.patronymic_edit.setPlaceholderText("Иванович")
        self.patronymic_edit.setToolTip("Необязательное поле. Только буквы, минимум 2 символа")
        form_layout.addRow("Отчество:", self.patronymic_edit)

        self.birth_date_edit = QDateEdit()
        self.birth_date_edit.setCalendarPopup(True)
        self.birth_date_edit.setDate(QDate.currentDate().addYears(-30))
        form_layout.addRow("Дата рождения *:", self.birth_date_edit)

        self.position_edit = QLineEdit()
        self.position_edit.setPlaceholderText("Инженер")
        form_layout.addRow("Должность *:", self.position_edit)

        self.department_combo = QComboBox()
        self.department_combo.setEditable(True)
        form_layout.addRow("Отдел:", self.department_combo)

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("+7 (999) 123-45-67")
        self.phone_edit.setToolTip("Формат: +7XXXXXXXXXX или 8XXXXXXXXXX")
        form_layout.addRow("Телефон:", self.phone_edit)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("ivanov@example.com")
        self.email_edit.setToolTip("Формат: user@example.com")
        form_layout.addRow("Email:", self.email_edit)

        self.hire_date_edit = QDateEdit()
        self.hire_date_edit.setCalendarPopup(True)
        self.hire_date_edit.setDate(QDate.currentDate())
        form_layout.addRow("Дата приема *:", self.hire_date_edit)

        self.salary_edit = QLineEdit()
        self.salary_edit.setPlaceholderText("50000")
        form_layout.addRow("Зарплата *:", self.salary_edit)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Активен", "В отпуске", "На больничном", "Уволен"])
        form_layout.addRow("Статус:", self.status_combo)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        self.error_label.setVisible(False)
        form_layout.addRow(self.error_label)

        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        save_button = QPushButton("Сохранить")
        save_button.setObjectName("primaryButton")
        save_button.clicked.connect(self.save_employee)
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

        is_valid, message = validate_patronymic(patronymic)
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

        is_valid, message = validate_phone(phone)
        if not is_valid:
            self.error_label.setText(message)
            self.error_label.setVisible(True)
            return

        is_valid, message = validate_email(email)
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
    def __init__(self, parent, employee_id, vacation_id=None):
        super().__init__(parent)
        self.database = parent.database
        self.employee_id = employee_id
        self.vacation_id = vacation_id
        self.is_edit = vacation_id is not None
        
        if self.is_edit:
            self.setWindowTitle("Редактирование отпуска")
        else:
            self.setWindowTitle("Добавление отпуска")
            
        self.setModal(True)
        self.setFixedSize(500, 350)
        self.setStyleSheet(STYLESHEET)
        self.init_ui()
        
        if self.is_edit:
            self.load_vacation_data()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.setMinimumSize(150, 35)
        form_layout.addRow("Дата начала:", self.start_date_edit)

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate().addDays(14))
        self.end_date_edit.setMinimumSize(150, 35)
        form_layout.addRow("Дата окончания:", self.end_date_edit)

        self.vacation_type_combo = QComboBox()
        self.vacation_type_combo.addItems(["Ежегодный", "Дополнительный", "Без содержания", "Учебный"])
        self.vacation_type_combo.setMinimumSize(200, 35)
        form_layout.addRow("Тип отпуска:", self.vacation_type_combo)

        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        save_button = QPushButton("Сохранить")
        save_button.setObjectName("primaryButton")
        save_button.setMinimumHeight(40)
        save_button.setMinimumWidth(120)
        save_button.clicked.connect(self.save_vacation)
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("Отмена")
        cancel_button.setMinimumHeight(40)
        cancel_button.setMinimumWidth(120)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def load_vacation_data(self):
        vacation = self.database.get_vacation(self.vacation_id)
        if vacation:
            start_date = QDate.fromString(str(vacation[2]), "yyyy-MM-dd")
            end_date = QDate.fromString(str(vacation[3]), "yyyy-MM-dd")
            self.start_date_edit.setDate(start_date)
            self.end_date_edit.setDate(end_date)
            
            index = self.vacation_type_combo.findText(vacation[4] or "Ежегодный")
            if index >= 0:
                self.vacation_type_combo.setCurrentIndex(index)

    def save_vacation(self):
        start_date = self.start_date_edit.date()
        end_date = self.end_date_edit.date()

        if start_date > end_date:
            QMessageBox.warning(self, "Ошибка", "Дата окончания не может быть раньше даты начала")
            return

        start_date_str = start_date.toString("yyyy-MM-dd")
        end_date_str = end_date.toString("yyyy-MM-dd")
        vacation_type = self.vacation_type_combo.currentText()

        try:
            if self.is_edit:
                self.database.update_vacation(self.vacation_id, start_date_str, end_date_str, vacation_type)
            else:
                self.database.add_vacation(self.employee_id, start_date_str, end_date_str, vacation_type)
                self.database.execute(
                    "UPDATE employees SET status = 'on_vacation' WHERE id = ?",
                    (self.employee_id,),
                    commit=True
                )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {str(e)}")


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
                border: 1px solid #d0d7de;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                color: #2c3e50;
                background-color: #f8fafc;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #4a90d9;
                background-color: #f8fafc;
            }
        """)

        filter_layout = QVBoxLayout()
        filter_layout.setSpacing(12)

        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(15)
        
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

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.apply_btn = QPushButton("Применить")
        self.apply_btn.setObjectName("primaryButton")
        self.apply_btn.clicked.connect(self.apply_filters)
        
        self.clear_btn = QPushButton("Сбросить")
        self.clear_btn.clicked.connect(self.clear_filters)

        buttons_layout.addWidget(self.apply_btn)
        buttons_layout.addWidget(self.clear_btn)
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

        return filters

    def apply_filters(self):
        if self.main_window:
            self.main_window.load_employees()

    def clear_filters(self):
        self.status_filter.setCurrentIndex(0)
        self.department_filter.setCurrentIndex(0)
        self.apply_filters()


class HRApp(QMainWindow):
    def __init__(self, database, user):
        super().__init__()
        self.database = database
        self.user = user
        self.filter_visible = False
        self.filter_widget = None
        self.all_employees = []
        self.current_view_dialog = None
        self.setWindowTitle(f"Система кадрового учета - {user['full_name']}")
        self.setGeometry(100, 100, 1400, 800)
        self.setStyleSheet(STYLESHEET)
        self.init_ui()
        self.load_employees()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.add_button = QPushButton("Добавить")
        self.add_button.setObjectName("primaryButton")
        self.add_button.clicked.connect(self.add_employee)
        button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Редактировать")
        self.edit_button.setObjectName("primaryButton")
        self.edit_button.clicked.connect(self.edit_employee)
        button_layout.addWidget(self.edit_button)
        
        self.vacation_button = QPushButton("Отпуск")
        self.vacation_button.setObjectName("primaryButton")
        self.vacation_button.clicked.connect(self.add_vacation)
        button_layout.addWidget(self.vacation_button)

        self.delete_button = QPushButton("Удалить")
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.clicked.connect(self.delete_employee)
        button_layout.addWidget(self.delete_button)

        self.stats_button = QPushButton("Статистика")
        self.stats_button.clicked.connect(self.show_statistics)
        button_layout.addWidget(self.stats_button)

        self.filter_toggle_btn = QPushButton("Фильтры")
        self.filter_toggle_btn.setCheckable(True)
        self.filter_toggle_btn.clicked.connect(self.toggle_filters)
        button_layout.addWidget(self.filter_toggle_btn)
        
        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.setObjectName("")
        self.refresh_button.clicked.connect(self.refresh_data)
        button_layout.addWidget(self.refresh_button)

        top_layout.addLayout(button_layout)
        top_layout.addStretch()

        search_layout = QHBoxLayout()
        search_layout.setSpacing(5)
        
        search_label = QLabel("Поиск:")
        search_label.setStyleSheet("font-weight: bold; color: #4a90d9;")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по всем полям...")
        self.search_input.setFixedWidth(300)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #4a90d9;
                border-radius: 20px;
                background-color: #ffffff;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #2a6ab8;
                background-color: #f8fbff;
            }
        """)
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_input)
        
        clear_search_btn = QPushButton("")
        clear_search_btn.setFixedSize(30, 30)
        clear_search_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 16px;
                color: #888;
            }
            QPushButton:hover {
                color: #e74c3c;
            }
        """)
        clear_search_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(clear_search_btn)
        
        top_layout.addLayout(search_layout)
        main_layout.addLayout(top_layout)

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
        self.employee_table.setSortingEnabled(True)
        
        main_layout.addWidget(self.employee_table)

        self.status_label = QLabel("Готов к работе")
        self.status_label.setStyleSheet("""
            color: #2c3e50;
            font-weight: bold;
            padding: 5px;
        """)
        main_layout.addWidget(self.status_label)

        self.filter_widget.load_departments()
        self.update_statistics()

    def on_search_changed(self, text):
        search_text = text.strip().lower()
        if not search_text:
            self.update_table(self.all_employees)
            return
        
        filtered = []
        for employee in self.all_employees:
            search_string = " ".join([
                str(employee[0]),
                str(employee[1] or ""),
                str(employee[2] or ""),
                str(employee[3] or ""),
                str(employee[4] or ""),
                str(employee[5] or ""),
                str(employee[6] or ""),
                str(employee[7] or ""),
                str(employee[8] or ""),
                str(employee[9] or ""),
                str(employee[10] or ""),
                STATUS_MAP.get(employee[11], employee[11])
            ]).lower()
            
            if search_text in search_string:
                filtered.append(employee)
        
        self.update_table(filtered)

    def clear_search(self):
        self.search_input.clear()
        self.load_employees()

    def refresh_data(self):
        employees = self.database.get_employees()
        today = date.today()
        
        for employee in employees:
            if employee[11] == 'on_vacation':
                vacations = self.database.get_vacations(employee[0])
                has_active_vacation = False
                
                for vacation in vacations:
                    start = datetime.strptime(str(vacation[2]), "%Y-%m-%d").date()
                    end = datetime.strptime(str(vacation[3]), "%Y-%m-%d").date()
                    
                    if start <= today <= end:
                        has_active_vacation = True
                        break
                
                if not has_active_vacation:
                    employee_data = (
                        employee[1], employee[2], employee[3], employee[4],
                        employee[5], employee[6], employee[7], employee[8],
                        employee[9], employee[10], 'active'
                    )
                    self.database.update_employee(employee[0], employee_data)
        
        self.load_employees()
        QMessageBox.information(self, "Обновление", "Данные успешно обновлены")

    def toggle_filters(self):
        self.filter_visible = self.filter_widget.toggle_visibility()
        if self.filter_visible:
            self.filter_toggle_btn.setText("Скрыть фильтры")
            self.filter_toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4a90d9;
                    color: white;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #3a7bc8;
                }
            """)
        else:
            self.filter_toggle_btn.setText("Фильтры")
            self.filter_toggle_btn.setStyleSheet("")
            self.filter_widget.clear_filters()

    def load_employees(self):
        filters = self.filter_widget.get_filters() if self.filter_visible else {}
        
        search_text = self.search_input.text().strip()
        if search_text:
            filters['search'] = search_text
            
        status_filter = filters.get('status')
        department_filter = filters.get('department')
        search = filters.get('search')
        
        employees = self.database.get_employees(search, status_filter, department_filter)
        self.all_employees = employees
        self.update_table(employees)

    def update_table(self, employees):
        self.employee_table.setSortingEnabled(False)
        self.employee_table.setRowCount(0)
        
        if not employees:
            self.employee_table.setSortingEnabled(True)
            self.update_statistics()
            return

        today = date.today()
        self.employee_table.setRowCount(len(employees))

        for row, employee in enumerate(employees):
            self.employee_table.setItem(row, 0, QTableWidgetItem(str(employee[0])))
            self.employee_table.setItem(row, 1, QTableWidgetItem(employee[1]))
            self.employee_table.setItem(row, 2, QTableWidgetItem(employee[2]))
            self.employee_table.setItem(row, 3, QTableWidgetItem(employee[3] or ""))

            if employee[4]:
                birth_date = datetime.strptime(str(employee[4]), "%Y-%m-%d").date()
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
            self.employee_table.setItem(row, 9, QTableWidgetItem(format_date(employee[9])))
            self.employee_table.setItem(row, 10, QTableWidgetItem(STATUS_MAP.get(employee[11], employee[11])))

            colors = COLOR_MAP.get(employee[11], (200, 220, 240, 0, 0, 0))
            background_color = QColor(colors[0], colors[1], colors[2])
            text_color = QColor(colors[3], colors[4], colors[5])

            for column in range(self.employee_table.columnCount()):
                item = self.employee_table.item(row, column)
                if item:
                    item.setBackground(QBrush(background_color))
                    item.setForeground(QBrush(text_color))

        self.employee_table.resizeColumnsToContents()
        self.employee_table.setSortingEnabled(True)
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
            if self.current_view_dialog and self.current_view_dialog.isVisible():
                self.refresh_view_dialog(self.current_view_dialog)

    def view_details(self, index):
        row = index.row()
        employee_id = int(self.employee_table.item(row, 0).text())
        self.show_employee_details(employee_id)

    def show_employee_details(self, employee_id):
        employee = self.database.get_employee(employee_id)

        if not employee:
            return

        if self.current_view_dialog:
            self.current_view_dialog.close()

        dialog = QDialog(self)
        self.current_view_dialog = dialog
        dialog.setWindowTitle(f"Информация - {employee[1]} {employee[2]}")
        dialog.setMinimumWidth(1100)
        dialog.setMinimumHeight(550)
        dialog.setStyleSheet(STYLESHEET)

        layout = QVBoxLayout()
        tabs = QTabWidget()

        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        
        button_layout_top = QHBoxLayout()
        
        edit_profile_btn = QPushButton("Редактировать профиль")
        edit_profile_btn.setObjectName("primaryButton")
        edit_profile_btn.setFixedWidth(200)
        edit_profile_btn.setFixedHeight(35)
        edit_profile_btn.clicked.connect(lambda: self.edit_employee_profile(employee_id))
        button_layout_top.addWidget(edit_profile_btn)
        
        delete_profile_btn = QPushButton("Удалить сотрудника")
        delete_profile_btn.setObjectName("dangerButton")
        delete_profile_btn.setFixedWidth(200)
        delete_profile_btn.setFixedHeight(35)
        delete_profile_btn.clicked.connect(lambda: self.delete_employee_from_profile(employee_id, dialog))
        button_layout_top.addWidget(delete_profile_btn)
        
        button_layout_top.addStretch()
        basic_layout.addLayout(button_layout_top)
        
        info_layout = QFormLayout()
        info_layout.setSpacing(12)
        info_layout.setLabelAlignment(Qt.AlignRight)

        age = ""
        if employee[4]:
            today = date.today()
            birth = datetime.strptime(str(employee[4]), "%Y-%m-%d").date()
            age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

        info_data = [
            ("Фамилия:", employee[1]),
            ("Имя:", employee[2]),
            ("Отчество:", employee[3] or "—"),
            ("Дата рождения:", format_date(employee[4])),
            ("Возраст:", f"{age} лет" if age else "—"),
            ("Должность:", employee[5] or "—"),
            ("Отдел:", employee[6] or "—"),
            ("Телефон:", employee[7] or "—"),
            ("Email:", employee[8] or "—"),
            ("Дата приема:", format_date(employee[9])),
            ("Зарплата:", f"{employee[10]:,.2f} руб." if employee[10] else "—"),
            ("Статус:", STATUS_MAP.get(employee[11], employee[11]))
        ]

        for label, value in info_data:
            label_widget = QLabel(label)
            label_widget.setStyleSheet("font-weight: bold; color: #4a90d9; font-size: 12px;")
            value_widget = QLabel(str(value))
            value_widget.setStyleSheet("color: #2c3e50; font-size: 12px;")
            info_layout.addRow(label_widget, value_widget)

        basic_layout.addLayout(info_layout)
        basic_layout.addStretch()
        tabs.addTab(basic_tab, "Основная информация")

        vacation_tab = QWidget()
        vacation_layout = QVBoxLayout(vacation_tab)

        vacation_button_layout = QHBoxLayout()
        
        add_vacation_btn = QPushButton("Добавить отпуск")
        add_vacation_btn.setObjectName("primaryButton")
        add_vacation_btn.setFixedHeight(40)
        add_vacation_btn.setFixedWidth(150)
        add_vacation_btn.clicked.connect(lambda: self.add_vacation_for_employee(employee_id))
        vacation_button_layout.addWidget(add_vacation_btn)
        
        vacation_button_layout.addStretch()
        vacation_layout.addLayout(vacation_button_layout)

        vacation_table = QTableWidget()
        vacation_table.setColumnCount(4)
        vacation_table.setHorizontalHeaderLabels(["Начало", "Окончание", "Тип", "Действия"])
        
        vacation_table.setColumnWidth(0, 130)
        vacation_table.setColumnWidth(1, 130)
        vacation_table.setColumnWidth(2, 150)
        vacation_table.horizontalHeader().setStretchLastSection(True)
        vacation_table.verticalHeader().setDefaultSectionSize(50)

        vacations = self.database.get_vacations(employee_id)
        vacation_table.setRowCount(len(vacations))

        table_font = QFont("Arial", 11)
        vacation_table.setFont(table_font)

        for vacation_row, vacation in enumerate(vacations):
            vacation_table.setItem(vacation_row, 0, QTableWidgetItem(format_date(vacation[2])))
            vacation_table.setItem(vacation_row, 1, QTableWidgetItem(format_date(vacation[3])))
            vacation_table.setItem(vacation_row, 2, QTableWidgetItem(vacation[4] or "—"))
            
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 5, 5, 5)
            actions_layout.setSpacing(10)
            
            edit_btn = QPushButton("Редактировать")
            edit_btn.setObjectName("primaryButton")
            edit_btn.setFixedWidth(120)
            edit_btn.setFixedHeight(35)
            edit_btn.setFont(QFont("Arial", 10))
            edit_btn.clicked.connect(lambda checked, v_id=vacation[0]: 
                                    self.edit_vacation(employee_id, v_id))
            
            delete_btn = QPushButton("Удалить")
            delete_btn.setObjectName("dangerButton")
            delete_btn.setFixedWidth(100)
            delete_btn.setFixedHeight(35)
            delete_btn.setFont(QFont("Arial", 10))
            delete_btn.clicked.connect(lambda checked, v_id=vacation[0]: 
                                      self.delete_vacation(v_id, employee_id))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()
            
            vacation_table.setCellWidget(vacation_row, 3, actions_widget)

        vacation_layout.addWidget(vacation_table)
        tabs.addTab(vacation_tab, "Отпуска")

        layout.addWidget(tabs)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(dialog.accept)
        close_button.setObjectName("primaryButton")
        close_button.setFixedHeight(40)
        layout.addWidget(close_button)

        dialog.setLayout(layout)
        dialog.finished.connect(lambda: self.on_view_dialog_closed())
        dialog.exec()

    def on_view_dialog_closed(self):
        self.current_view_dialog = None

    def refresh_view_dialog(self, dialog):
        title = dialog.windowTitle()
        if "Информация - " in title:
            name = title.replace("Информация - ", "")
            employees = self.database.get_employees()
            for emp in employees:
                if f"{emp[1]} {emp[2]}" == name:
                    dialog.close()
                    self.show_employee_details(emp[0])
                    break

    def edit_employee_profile(self, employee_id):
        dialog = EmployeeDialog(self, employee_id)
        if dialog.exec():
            self.load_employees()
            if self.current_view_dialog:
                self.refresh_view_dialog(self.current_view_dialog)

    def delete_employee_from_profile(self, employee_id, parent_dialog):
        reply = QMessageBox.question(
            self, "Удаление сотрудника", 
            "Вы уверены, что хотите удалить этого сотрудника?\nЭто действие нельзя отменить.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.database.delete_employee(employee_id)
            parent_dialog.accept()
            self.load_employees()
            self.filter_widget.load_departments()
            self.current_view_dialog = None
            QMessageBox.information(self, "Успех", "Сотрудник успешно удален")

    def add_vacation_for_employee(self, employee_id):
        dialog = VacationDialog(self, employee_id)
        if dialog.exec():
            self.load_employees()
            if self.current_view_dialog:
                self.refresh_view_dialog(self.current_view_dialog)

    def edit_vacation(self, employee_id, vacation_id):
        dialog = VacationDialog(self, employee_id, vacation_id)
        if dialog.exec():
            self.load_employees()
            if self.current_view_dialog:
                self.refresh_view_dialog(self.current_view_dialog)

    def delete_vacation(self, vacation_id, employee_id):
        reply = QMessageBox.question(
            self, "Удаление отпуска", "Удалить запись об отпуске?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.database.delete_vacation(vacation_id)
            
            vacations = self.database.get_vacations(employee_id)
            today = date.today()
            has_active_vacation = False
            
            for vacation in vacations:
                start = datetime.strptime(str(vacation[2]), "%Y-%m-%d").date()
                end = datetime.strptime(str(vacation[3]), "%Y-%m-%d").date()
                if start <= today <= end:
                    has_active_vacation = True
                    break
            
            if not has_active_vacation:
                employee = self.database.get_employee(employee_id)
                if employee and employee[11] == 'on_vacation':
                    employee_data = (
                        employee[1], employee[2], employee[3], employee[4],
                        employee[5], employee[6], employee[7], employee[8],
                        employee[9], employee[10], 'active'
                    )
                    self.database.update_employee(employee_id, employee_data)
            
            self.load_employees()
            if self.current_view_dialog:
                self.refresh_view_dialog(self.current_view_dialog)
            QMessageBox.information(self, "Успех", "Запись об отпуске удалена")

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
    application.setStyle('Fusion')

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
