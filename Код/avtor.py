import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, 
    QLineEdit, QMessageBox, QVBoxLayout, QHBoxLayout
)
from PyQt5.QtCore import Qt

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
        self.pushButton_login.setStyleSheet("font-size: 20pt;")
        
        self.pushButton_login.clicked.connect(self.check_login)
        
        self.lineEdit_password.returnPressed.connect(self.check_login)
        self.lineEdit_login.returnPressed.connect(self.check_login)
        
    def check_login(self):
        login = self.lineEdit_login.text()
        password = self.lineEdit_password.text()
        
        if login == self.valid_login and password == self.valid_password:
            QMessageBox.information(
                self, 
                "Успех", 
                "Авторизация прошла успешно!",
                QMessageBox.Ok
            )
            
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())