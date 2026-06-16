from PySide6.QtGui import QColor

STATUS_MAP = {
    'active': 'Активен',
    'on_vacation': 'В отпуске',
    'sick_leave': 'На больничном',
    'fired': 'Уволен'
}

STATUS_REV = {v: k for k, v in STATUS_MAP.items()}

COLOR_MAP = {
    'active': (220, 240, 255, 0, 80, 150),
    'on_vacation': (200, 235, 255, 0, 100, 180),
    'sick_leave': (255, 245, 220, 150, 100, 50),
    'fired': (255, 220, 220, 180, 50, 50)
}

STYLESHEET = """
QMainWindow, QDialog {
    background-color: #f5f8fa;
}

QLabel {
    color: #2c3e50;
    font-weight: 500;
}

QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {
    padding: 8px 12px;
    border: 1px solid #d0d7de;
    border-radius: 4px;
    background-color: #ffffff;
    color: #2c3e50;
    font-size: 13px;
}

QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #4a90d9;
    background-color: #fafcff;
}

QLineEdit:hover, QComboBox:hover, QDateEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover {
    border-color: #6aafee;
}

QPushButton {
    padding: 8px 18px;
    border-radius: 4px;
    font-weight: bold;
    font-size: 13px;
    background-color: #e8edf2;
    color: #2c3e50;
    border: 1px solid #d0d7de;
}

QPushButton:hover {
    background-color: #d5dde6;
    border-color: #b0b8c0;
}

QPushButton:pressed {
    background-color: #c5cdd6;
}

QPushButton#primaryButton {
    background-color: #4a90d9;
    color: white;
    border: none;
}

QPushButton#primaryButton:hover {
    background-color: #3a7bc8;
}

QPushButton#primaryButton:pressed {
    background-color: #2a6ab8;
}

QPushButton#dangerButton {
    background-color: #e74c3c;
    color: white;
    border: none;
}

QPushButton#dangerButton:hover {
    background-color: #c0392b;
}

QTableWidget {
    background-color: #ffffff;
    color: #2c3e50;
    gridline-color: #e1e8ef;
    border: 1px solid #d0d7de;
    border-radius: 4px;
    selection-background-color: #d4e4fc;
    selection-color: #2c3e50;
    alternate-background-color: #f8fafc;
}

QTableWidget::item {
    padding: 6px;
}

QTableWidget::item:selected {
    background-color: #d4e4fc;
    color: #2c3e50;
}

QHeaderView::section {
    background-color: #e8edf2;
    color: #2c3e50;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #4a90d9;
    font-weight: bold;
    font-size: 13px;
}

QHeaderView::section:hover {
    background-color: #d5dde6;
}

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

QTabWidget::pane {
    border: 1px solid #d0d7de;
    border-radius: 4px;
    background-color: #ffffff;
}

QTabBar::tab {
    background-color: #e8edf2;
    color: #2c3e50;
    padding: 8px 20px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    border: 1px solid #d0d7de;
    border-bottom: none;
    margin-right: 2px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #4a90d9;
    border-bottom: 2px solid #4a90d9;
}

QTabBar::tab:hover:!selected {
    background-color: #d5dde6;
}

QStatusBar {
    background-color: #e8edf2;
    color: #2c3e50;
    border-top: 1px solid #d0d7de;
    padding: 4px;
}

QStatusBar QLabel {
    color: #2c3e50;
}

QScrollBar:vertical {
    border: none;
    background-color: #e8edf2;
    width: 10px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #d0d7de;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #b0b8c0;
}

QScrollBar:horizontal {
    border: none;
    background-color: #e8edf2;
    height: 10px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background-color: #d0d7de;
    border-radius: 4px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #b0b8c0;
}

QMenuBar {
    background-color: #e8edf2;
    color: #2c3e50;
    border-bottom: 1px solid #d0d7de;
}

QMenuBar::item:selected {
    background-color: #d4e4fc;
    border-radius: 4px;
}

QMenu {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 4px;
    color: #2c3e50;
}

QMenu::item:selected {
    background-color: #d4e4fc;
}

QMenu::separator {
    height: 1px;
    background-color: #d0d7de;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    width: 10px;
    height: 6px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 4px;
    color: #2c3e50;
    selection-background-color: #d4e4fc;
    selection-color: #2c3e50;
}

QMessageBox {
    background-color: #f8fafc;
}

QMessageBox QPushButton {
    min-width: 80px;
}

QCheckBox, QRadioButton {
    color: #2c3e50;
    spacing: 8px;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #d0d7de;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #4a90d9;
    border-color: #4a90d9;
}

QRadioButton::indicator:checked {
    background-color: #4a90d9;
    border-color: #4a90d9;
}

QProgressBar {
    border: 1px solid #d0d7de;
    border-radius: 4px;
    background-color: #f8fafc;
    text-align: center;
    color: #2c3e50;
}

QProgressBar::chunk {
    background-color: #4a90d9;
    border-radius: 3px;
}

QToolTip {
    background-color: #ffffff;
    color: #2c3e50;
    border: 1px solid #d0d7de;
    border-radius: 4px;
    padding: 6px;
    font-size: 12px;
}

QLineEdit#searchField {
    border: 1px solid #d0d7de;
    border-radius: 20px;
    padding: 8px 16px;
    background-color: #ffffff;
}

QLineEdit#searchField:focus {
    border-color: #4a90d9;
    background-color: #fafcff;
}

QSpinBox, QDoubleSpinBox {
    padding-right: 16px;
}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    border: none;
    background-color: #e8edf2;
    width: 16px;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #d4e4fc;
}

QDateEdit {
    padding-right: 16px;
}

QDateEdit::drop-down {
    border: none;
    width: 20px;
}
"""