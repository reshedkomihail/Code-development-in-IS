import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, 
    QLineEdit, QMessageBox, QVBoxLayout, QHBoxLayout,
    QMainWindow
)
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    """Главное окно приложения"""
    def __init__(self, username=""):
        super().__init__()
        self.username = username
        self.initUI()
    def initUI(self):
        self.setWindowTitle("Главное окно")
        self.setGeometry(400, 400, 800, 600)
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        # Основной layout
        layout = QVBoxLayout(central_widget)   
        welcome_label = QLabel(f"Добро пожаловать, {self.username}!")
        welcome_label.setStyleSheet("font-size: 24pt; color: blue;")
        welcome_label.setAlignment(Qt.AlignCenter)
        self.logout_button.setStyleSheet("""
            QPushButton {
                font-size: 16pt;
                background-color: #f44336;
                color: white;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)  
        layout.addWidget(welcome_label)
        layout.addWidget(self.logout_button)
        layout.addStretch()

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
        # log pass
        self.valid_login = "admin"
        self.valid_password = "12345"
        
    def initUI(self):
        self.setWindowTitle("Авторизация")
        self.setGeometry(300, 300, 439, 352)
        
        self.label_login = QLabel("Логин", self)
        self.label_login.setGeometry(70, 80, 71, 31)
        self.label_login.setStyleSheet("font-size: 14pt;")
        
        self.label_password = QLabel("Пароль", self)
        self.label_password.setGeometry(70, 130, 71, 31)
        self.label_password.setStyleSheet("font-size: 14pt;")
        
        self.lineEdit_login = QLineEdit(self)
        self.lineEdit_login.setGeometry(160, 80, 121, 31)
        
        self.lineEdit_password = QLineEdit(self)
        self.lineEdit_password.setGeometry(160, 130, 121, 31)
        self.lineEdit_password.setEchoMode(QLineEdit.Password)
        
        self.pushButton_login = QPushButton("Войти", self)
        self.pushButton_login.setGeometry(140, 240, 141, 61)
        self.pushButton_login.setStyleSheet("""
            QPushButton {
                font-size: 20pt;
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.pushButton_login.clicked.connect(self.check_login)
        
        self.lineEdit_password.returnPressed.connect(self.check_login)
        self.lineEdit_login.returnPressed.connect(self.check_login)
        
        # Добавляем кнопку для сброса (опционально)
        self.reset_button = QPushButton("Сбросить", self)
        self.reset_button.setGeometry(300, 240, 80, 31)
        self.reset_button.clicked.connect(self.reset_fields)
        
    def check_login(self):
        login = self.lineEdit_login.text()
        password = self.lineEdit_password.text()
        
        if login == self.valid_login and password == self.valid_password:
            QMessageBox.information(
                self, 
                "Успех", 
                "Авторизация прошла успешно!\nОткрывается главное окно...",
                QMessageBox.Ok
            )
            
            # Создаем главное окно
            self.main_window = MainWindow(username=login)
            # Подключаем сигнал выхода
            self.main_window.logout_button.clicked.connect(self.show_login)
            # Показываем главное окно
            self.main_window.show()
            # Скрываем окно авторизации
            self.hide()
        else:
            QMessageBox.warning(
                self, 
                "Ошибка", 
                "Неверный логин или пароль!",
                QMessageBox.Ok
            )
            self.lineEdit_login.clear()
            self.lineEdit_password.clear()
            self.lineEdit_login.setFocus()
    def show_login(self):
        """Возврат к окну авторизации"""
        self.main_window.close()
        self.show()
        self.reset_fields()
    
    def reset_fields(self):
        """Сброс полей ввода"""
        self.lineEdit_login.clear()
        self.lineEdit_password.clear()
        self.lineEdit_login.setFocus()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Устанавливаем стиль для всего приложения
    app.setStyle('Fusion')
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
