import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
    QDateEdit, QMessageBox, QLabel, QDialog, QFormLayout, QGroupBox,
    QHeaderView, QTimeEdit
)
from PyQt5.QtGui import QColor, QPalette, QFont, QPixmap
from PyQt5.QtCore import Qt, QDate, QTime
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2


class Database:
    def __init__(self):
        self.conn = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                dbname="db2991_17",
                user="st2991",
                password="pwd2991",
                host="172.20.7.53",
                port="5432"
            )
            return True
        except psycopg2.Error as e:
            print(f"Ошибка подключения: {e}")
            return False

    def register_user(self, username, password, role, **kwargs):
        table_map = {
            "athlete": ("athletes", "id_athlete"),
            "trainer": ("trainers", "id_trainer"),
            "judge": ("judges", "id_judge"),
            "organizer": ("organizers", "id_organizer")
        }

        if role not in table_map:
            QMessageBox.warning(None, "Ошибка", "Неверная роль пользователя")
            return None

        table, id_field = table_map[role]

        check_query = f"SELECT username FROM sportsorganizations.{table} WHERE username = %s"

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(check_query, (username,))
                if cursor.fetchone():
                    QMessageBox.warning(None, "Ошибка", "Пользователь с таким логином уже существует")
                    return None

                password_hash = generate_password_hash(password)
                query = f"""
                INSERT INTO sportsorganizations.{table} 
                (username, passwordhash, firstname, lastname) 
                VALUES (%s, %s, %s, %s) RETURNING {id_field}
                """

                cursor.execute(query, (username, password_hash,
                                       kwargs.get('firstname'),
                                       kwargs.get('lastname')))
                user_id = cursor.fetchone()[0]
                self.conn.commit()
                return {'id': user_id, 'username': username, 'role': role}

        except psycopg2.Error as e:
            print(f"Ошибка регистрации: {e}")
            self.conn.rollback()
            if "unique constraint" in str(e).lower():
                QMessageBox.warning(None, "Ошибка", "Пользователь с таким логином уже существует")
            else:
                QMessageBox.warning(None, "Ошибка БД", f"Ошибка при регистрации: {e}")
            return None

    def authenticate(self, username, password):
        tables = [
            ("athletes", "id_athlete", "athlete"),
            ("trainers", "id_trainer", "trainer"),
            ("judges", "id_judge", "judge"),
            ("organizers", "id_organizer", "organizer")
        ]

        for table, id_field, role in tables:
            query = f"""
            SELECT {id_field}, passwordhash FROM sportsorganizations.{table} 
            WHERE username = %s
            """
            result = self.execute(query, (username,), fetch=True)

            if result and check_password_hash(result[0][1], password):
                return {'id': result[0][0], 'username': username, 'role': role}

        return None

    def execute(self, query, params=None, fetch=False):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                if fetch:
                    return cursor.fetchall()
                self.conn.commit()
                return True
        except psycopg2.Error as e:
            print(f"Ошибка выполнения запроса: {e}")
            self.conn.rollback()
            return False


def setup_style(app):
    app.setStyle("Fusion")

    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)

    app.setPalette(dark_palette)
    app.setStyleSheet("""
        QPushButton {
            background-color: #2a82da;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: #3a92ea;
        }
        QPushButton:pressed {
            background-color: #1a72ca;
        }
        QLineEdit, QComboBox, QDateEdit, QTimeEdit {
            background-color: #454545;
            color: white;
            border: 1px solid #555;
            border-radius: 4px;
            padding: 5px;
        }
        QLabel {
            color: white;
        }
        QGroupBox {
            border: 1px solid #555;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 15px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px;
        }
        QTabWidget::pane {
            border: 1px solid #444;
            top: -1px;
        }
        QTabBar::tab {
            background: #444;
            color: white;
            padding: 8px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background: #2a82da;
        }
        QHeaderView::section {
            background-color: #2a82da;
            color: white;
            padding: 5px;
        }
        QTableWidget {
            gridline-color: #555;
        }
    """)


class AuthWindow(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.user = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Авторизация")
        self.setFixedSize(500, 400)

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setSpacing(20)

        title = QLabel("Спортивные организации")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)

        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setPixmap(QPixmap(":/icons/sports.png").scaled(100, 100, Qt.KeepAspectRatio))

        form_widget = QWidget()
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(30, 20, 30, 20)

        form_widget.setStyleSheet("""
            QWidget {
                background-color: #353535;
                border-radius: 8px;
            }
        """)

        self.username = QLineEdit(placeholderText="Введите логин")
        self.password = QLineEdit(placeholderText="Введите пароль", echoMode=QLineEdit.Password)

        button_layout = QHBoxLayout()
        self.login_btn = QPushButton("Войти")
        self.login_btn.setStyleSheet("background-color: #2a82da;")
        self.register_btn = QPushButton("Регистрация")
        self.register_btn.setStyleSheet("background-color: #5a5a5a;")

        button_layout.addWidget(self.login_btn)
        button_layout.addWidget(self.register_btn)

        form_layout.addRow("Логин:", self.username)
        form_layout.addRow("Пароль:", self.password)
        form_layout.addRow(button_layout)

        form_widget.setLayout(form_layout)

        main_layout.addWidget(title)
        main_layout.addWidget(icon_label)
        main_layout.addWidget(form_widget)

        self.login_btn.clicked.connect(self.login)
        self.register_btn.clicked.connect(self.show_register)

        self.setLayout(main_layout)

    def login(self):
        username = self.username.text()
        password = self.password.text()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return

        self.user = self.db.authenticate(username, password)
        if self.user:
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")

    def show_register(self):
        dialog = RegisterDialog(self.db)
        if dialog.exec_():
            self.username.setText(dialog.username.text())
            self.password.clear()
            QMessageBox.information(self, "Успех", "Регистрация прошла успешно")


class RegisterDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Регистрация")
        self.setFixedSize(500, 450)

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setSpacing(15)

        title = QLabel("Регистрация нового пользователя")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)

        form_widget = QWidget()
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(30, 20, 30, 20)

        form_widget.setStyleSheet("""
            QWidget {
                background-color: #353535;
                border-radius: 8px;
            }
        """)

        self.username = QLineEdit(placeholderText="Придумайте логин")
        self.password = QLineEdit(placeholderText="Придумайте пароль", echoMode=QLineEdit.Password)
        self.firstname = QLineEdit(placeholderText="Ваше имя")
        self.lastname = QLineEdit(placeholderText="Ваша фамилия")
        self.role = QComboBox()
        self.role.addItems(["Спортсмен", "Тренер", "Судья", "Организатор"])

        button_layout = QHBoxLayout()
        self.register_btn = QPushButton("Зарегистрироваться")
        self.register_btn.setStyleSheet("background-color: #2a82da;")
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setStyleSheet("background-color: #5a5a5a;")

        button_layout.addWidget(self.register_btn)
        button_layout.addWidget(self.cancel_btn)

        form_layout.addRow("Логин:", self.username)
        form_layout.addRow("Пароль:", self.password)
        form_layout.addRow("Имя:", self.firstname)
        form_layout.addRow("Фамилия:", self.lastname)
        form_layout.addRow("Роль:", self.role)
        form_layout.addRow(button_layout)

        form_widget.setLayout(form_layout)

        main_layout.addWidget(title)
        main_layout.addWidget(form_widget)

        self.register_btn.clicked.connect(self.register)
        self.cancel_btn.clicked.connect(self.reject)

        self.setLayout(main_layout)

    def register(self):
        role_mapping = {
            "Спортсмен": "athlete",
            "Тренер": "trainer",
            "Судья": "judge",
            "Организатор": "organizer"
        }

        selected_role = self.role.currentText()
        if selected_role not in role_mapping:
            QMessageBox.warning(self, "Ошибка", "Выбрана недопустимая роль")
            return

        data = {
            'username': self.username.text(),
            'password': self.password.text(),
            'firstname': self.firstname.text(),
            'lastname': self.lastname.text(),
            'role': role_mapping[selected_role]
        }

        if not all(data.values()):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return

        result = self.db.register_user(**data)
        if result:
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось зарегистрировать пользователя")


class BaseTab(QWidget):
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.current_id = None
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

    def setup_common_ui(self, table_columns):
        self.table = QTableWidget()
        self.table.setColumnCount(len(table_columns))
        self.table.setHorizontalHeaderLabels(table_columns)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.form_group = QGroupBox("Добавить/Изменить")
        self.form_group.setVisible(self.user['role'] == 'organizer')

        self.buttons_widget = QWidget()
        buttons_layout = QHBoxLayout()

        self.add_button = QPushButton("Добавить")
        self.update_button = QPushButton("Изменить")
        self.delete_button = QPushButton("Удалить")
        self.delete_button.setStyleSheet("background-color: #e74c3c;")

        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.update_button)
        buttons_layout.addWidget(self.delete_button)

        self.update_button.setVisible(self.user['role'] == 'organizer')
        self.buttons_widget.setLayout(buttons_layout)
        self.buttons_widget.setVisible(self.user['role'] == 'organizer')

        self.layout.addWidget(self.table)
        self.layout.addWidget(self.form_group)
        self.layout.addWidget(self.buttons_widget)

    def toggle_edit_mode(self, edit_mode):
        if hasattr(self, 'add_button'):
            self.add_button.setEnabled(not edit_mode)
        if hasattr(self, 'update_button'):
            self.update_button.setEnabled(edit_mode)
        if hasattr(self, 'delete_button'):
            self.delete_button.setEnabled(edit_mode)

    def clear_form(self):
        for widget in self.findChildren(QLineEdit):
            widget.clear()
        for widget in self.findChildren(QComboBox):
            widget.setCurrentIndex(0)
        for widget in self.findChildren(QDateEdit):
            widget.setDate(QDate.currentDate())
        self.current_id = None
        self.toggle_edit_mode(False)


class AthletesTab(BaseTab):
    def init_ui(self):
        super().init_ui()
        self.setup_common_ui([
            "ID", "Имя", "Фамилия", "Пол", "Телефон",
            "Дата рождения", "Разряд", "Вид спорта", "Действия"
        ])

        form_layout = QFormLayout()

        self.firstname = QLineEdit()
        self.lastname = QLineEdit()
        self.gender = QComboBox()
        self.gender.addItems(["", "М", "Ж"])
        self.phone = QLineEdit()
        self.birthdate = QDateEdit(calendarPopup=True)
        self.birthdate.setDisplayFormat("dd.MM.yyyy")
        self.rank = QLineEdit()
        self.sport_type = QLineEdit()

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        self.add_button = QPushButton("Добавить")
        self.update_button = QPushButton("Изменить")
        self.delete_button = QPushButton("Удалить")
        self.delete_button.setStyleSheet("background-color: #e74c3c;")
        self.clear_button = QPushButton("Очистить")

        buttons.addWidget(self.add_button, stretch=1)
        buttons.addWidget(self.update_button, stretch=1)
        buttons.addWidget(self.delete_button, stretch=1)
        buttons.addWidget(self.clear_button, stretch=1)

        form_layout.addRow("Имя:", self.firstname)
        form_layout.addRow("Фамилия:", self.lastname)
        form_layout.addRow("Пол:", self.gender)
        form_layout.addRow("Телефон:", self.phone)
        form_layout.addRow("Дата рождения:", self.birthdate)
        form_layout.addRow("Разряд:", self.rank)
        form_layout.addRow("Вид спорта:", self.sport_type)

        self.form_group.setMinimumWidth(600)
        self.form_group.setLayout(form_layout)
        self.buttons_widget.setLayout(buttons)

        self.add_button.clicked.connect(self.add_athlete)
        self.update_button.clicked.connect(self.update_athlete)
        self.delete_button.clicked.connect(self.delete_athlete_by_id)
        self.clear_button.clicked.connect(self.clear_form)
        self.table.cellDoubleClicked.connect(self.on_table_double_click)

        if self.user['role'] == 'athlete':
            self.load_data(only_current_user=True)
            self.setup_athlete_edit_mode()
        else:
            self.load_data()

    def setup_athlete_edit_mode(self):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and int(item.text()) == self.user['id']:
                for col in range(self.table.columnCount()):
                    if self.table.cellWidget(row, col):
                        self.table.removeCellWidget(row, col)
                break

    def on_table_double_click(self, row, col):
        if self.user['role'] != 'organizer':
            return

    def load_data(self, only_current_user=False):
        if only_current_user or self.user['role'] == 'athlete':
            query = """
            SELECT id_athlete, firstname, lastname, gender, phone_number, 
                   birth_date, sport_rank, sport_type
            FROM sportsorganizations.athletes 
            WHERE id_athlete = %s
            """
            params = (self.user['id'],)
        else:
            query = """
            SELECT id_athlete, firstname, lastname, gender, phone_number, 
                   birth_date, sport_rank, sport_type
            FROM sportsorganizations.athletes
            """
            params = None

        result = self.db.execute(query, params, fetch=True)
        if result:
            self.table.setRowCount(len(result))
            for row_idx, row in enumerate(result):
                for col_idx, value in enumerate(row):
                    if col_idx == 5:
                        value = value.strftime("%d.%m.%Y") if value else ""
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    self.table.setItem(row_idx, col_idx, item)

                if self.user['role'] == 'organizer':
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout()
                    actions_layout.setContentsMargins(0, 0, 0, 0)

                    edit_btn = QPushButton("Изменить")
                    edit_btn.clicked.connect(lambda _, r=row_idx: self.edit_athlete(r, 0))

                    delete_btn = QPushButton("Удалить")
                    delete_btn.setStyleSheet("background-color: #e74c3c;")
                    delete_btn.clicked.connect(lambda _, r=row_idx: self.delete_row(r))

                    actions_layout.addWidget(edit_btn)
                    actions_layout.addWidget(delete_btn)
                    actions_widget.setLayout(actions_layout)

                    self.table.setCellWidget(row_idx, 8, actions_widget)

    def add_athlete(self):
        query = """
        INSERT INTO sportsorganizations.athletes 
        (firstname, lastname, gender, phone_number, birth_date, sport_rank, sport_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            self.firstname.text(),
            self.lastname.text(),
            self.gender.currentText() if self.gender.currentText() else None,
            self.phone.text() if self.phone.text() else None,
            self.birthdate.date().toString("yyyy-MM-dd"),
            self.rank.text() if self.rank.text() else None,
            self.sport_type.text() if self.sport_type.text() else None
        )

        if self.db.execute(query, params):
            QMessageBox.information(self, "Успех", "Спортсмен добавлен")
            self.load_data()
            self.clear_form()

    def edit_athlete(self, row, col):
        self.current_id = int(self.table.item(row, 0).text())

        self.firstname.setText(self.table.item(row, 1).text())
        self.lastname.setText(self.table.item(row, 2).text())

        gender = self.table.item(row, 3).text()
        index = self.gender.findText(gender)
        self.gender.setCurrentIndex(index if index != -1 else 0)

        self.phone.setText(self.table.item(row, 4).text())

        birthdate = self.table.item(row, 5).text()
        if birthdate:
            date = QDate.fromString(birthdate, "dd.MM.yyyy")
            self.birthdate.setDate(date)

        self.rank.setText(self.table.item(row, 6).text())
        self.sport_type.setText(self.table.item(row, 7).text())

        self.toggle_edit_mode(True)

    def update_athlete(self):
        if not self.current_id:
            return

        query = """
        UPDATE sportsorganizations.athletes 
        SET firstname = %s, lastname = %s, gender = %s, phone_number = %s, 
            birth_date = %s, sport_rank = %s, sport_type = %s
        WHERE id_athlete = %s
        """
        params = (
            self.firstname.text(),
            self.lastname.text(),
            self.gender.currentText() if self.gender.currentText() else None,
            self.phone.text() if self.phone.text() else None,
            self.birthdate.date().toString("yyyy-MM-dd"),
            self.rank.text() if self.rank.text() else None,
            self.sport_type.text() if self.sport_type.text() else None,
            self.current_id
        )

        if self.db.execute(query, params):
            QMessageBox.information(self, "Успех", "Данные обновлены")
            self.load_data()
            self.clear_form()

    def delete_row(self, row):
        athlete_id = int(self.table.item(row, 0).text())
        self.delete_athlete_by_id(athlete_id)

    def delete_athlete_by_id(self, athlete_id):
        reply = QMessageBox.question(
            self, 'Подтверждение',
            'Вы уверены, что хотите удалить этого спортсмена?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            query = "DELETE FROM sportsorganizations.athletes WHERE id_athlete = %s"
            if self.db.execute(query, (athlete_id,)):
                QMessageBox.information(self, "Успех", "Спортсмен удален")
                self.load_data()
                self.clear_form()


class TrainersTab(BaseTab):
    def init_ui(self):
        super().init_ui()
        self.setup_common_ui([
            "ID", "Имя", "Фамилия", "Телефон", "Вид спорта",
            "Категория", "Дата рождения", "Действия"
        ])

        form_layout = QFormLayout()

        self.firstname = QLineEdit()
        self.lastname = QLineEdit()
        self.phone = QLineEdit()
        self.sport_type = QComboBox()
        self.sport_type.addItems(["Футбол", "Хоккей", "Баскетбол", "Плавание", "Другой"])
        self.category = QComboBox()
        self.category.addItems(["1 категория", "2 категория", "Высшая категория"])
        self.birthdate = QDateEdit(calendarPopup=True)
        self.birthdate.setDisplayFormat("dd.MM.yyyy")

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        self.add_button = QPushButton("Добавить")
        self.update_button = QPushButton("Изменить")
        self.delete_button = QPushButton("Удалить")
        self.delete_button.setStyleSheet("background-color: #e74c3c;")
        self.clear_button = QPushButton("Очистить")

        buttons.addWidget(self.add_button, stretch=1)
        buttons.addWidget(self.update_button, stretch=1)
        buttons.addWidget(self.delete_button, stretch=1)
        buttons.addWidget(self.clear_button, stretch=1)

        form_layout.addRow("Имя:", self.firstname)
        form_layout.addRow("Фамилия:", self.lastname)
        form_layout.addRow("Телефон:", self.phone)
        form_layout.addRow("Вид спорта:", self.sport_type)
        form_layout.addRow("Категория:", self.category)
        form_layout.addRow("Дата рождения:", self.birthdate)

        self.form_group.setMinimumWidth(600)
        self.form_group.setLayout(form_layout)
        self.buttons_widget.setLayout(buttons)

        self.add_button.clicked.connect(self.add_trainer)
        self.update_button.clicked.connect(self.update_trainer)
        self.delete_button.clicked.connect(self.delete_trainer_by_id)
        self.clear_button.clicked.connect(self.clear_form)
        self.table.cellDoubleClicked.connect(self.on_table_double_click)

        if self.user['role'] == 'trainer':
            self.load_data(only_current_user=True)
            self.setup_trainer_edit_mode()
        else:
            self.load_data()

    def setup_trainer_edit_mode(self):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and int(item.text()) == self.user['id']:
                for col in range(self.table.columnCount()):
                    if self.table.cellWidget(row, col):
                        self.table.removeCellWidget(row, col)
                break

    def on_table_double_click(self, row, col):
        if self.user['role'] != 'organizer':
            return

    def load_data(self, only_current_user=False):
        if only_current_user or self.user['role'] == 'trainer':
            query = """
            SELECT id_trainer, firstname, lastname, phone_number, 
                   sport_type, category, birth_date
            FROM sportsorganizations.trainers 
            WHERE id_trainer = %s
            """
            params = (self.user['id'],)
        else:
            query = """
            SELECT id_trainer, firstname, lastname, phone_number, 
                   sport_type, category, birth_date
            FROM sportsorganizations.trainers
            """
            params = None

        result = self.db.execute(query, params, fetch=True)
        if result:
            self.table.setRowCount(len(result))
            for row_idx, row in enumerate(result):
                for col_idx, value in enumerate(row):
                    if col_idx == 6:
                        value = value.strftime("%d.%m.%Y") if value else ""
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    self.table.setItem(row_idx, col_idx, item)

                if self.user['role'] == 'organizer':
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout()
                    actions_layout.setContentsMargins(0, 0, 0, 0)

                    edit_btn = QPushButton("Изменить")
                    edit_btn.clicked.connect(lambda _, r=row_idx: self.edit_trainer(r, 0))

                    delete_btn = QPushButton("Удалить")
                    delete_btn.setStyleSheet("background-color: #e74c3c;")
                    delete_btn.clicked.connect(lambda _, r=row_idx: self.delete_row(r))

                    actions_layout.addWidget(edit_btn)
                    actions_layout.addWidget(delete_btn)
                    actions_widget.setLayout(actions_layout)

                    self.table.setCellWidget(row_idx, 7, actions_widget)

    def add_trainer(self):
        query = """
        INSERT INTO sportsorganizations.trainers 
        (firstname, lastname, phone_number, sport_type, category, birth_date)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (
            self.firstname.text(),
            self.lastname.text(),
            self.phone.text(),
            self.sport_type.currentText(),
            self.category.currentText(),
            self.birthdate.date().toString("yyyy-MM-dd")
        )

        if self.db.execute(query, params):
            QMessageBox.information(self, "Успех", "Тренер добавлен")
            self.load_data()
            self.clear_form()

    def edit_trainer(self, row, col):
        self.current_id = int(self.table.item(row, 0).text())

        self.firstname.setText(self.table.item(row, 1).text())
        self.lastname.setText(self.table.item(row, 2).text())
        self.phone.setText(self.table.item(row, 3).text())

        sport_type = self.table.item(row, 4).text()
        index = self.sport_type.findText(sport_type)
        self.sport_type.setCurrentIndex(index if index != -1 else 0)

        category = self.table.item(row, 5).text()
        index = self.category.findText(category)
        self.category.setCurrentIndex(index if index != -1 else 0)

        birthdate = self.table.item(row, 6).text()
        if birthdate:
            date = QDate.fromString(birthdate, "dd.MM.yyyy")
            self.birthdate.setDate(date)

        self.toggle_edit_mode(True)

    def update_trainer(self):
        if not self.current_id:
            return

        query = """
        UPDATE sportsorganizations.trainers 
        SET firstname = %s, lastname = %s, phone_number = %s, 
            sport_type = %s, category = %s, birth_date = %s
        WHERE id_trainer = %s
        """
        params = (
            self.firstname.text(),
            self.lastname.text(),
            self.phone.text(),
            self.sport_type.currentText(),
            self.category.currentText(),
            self.birthdate.date().toString("yyyy-MM-dd"),
            self.current_id
        )

        if self.db.execute(query, params):
            QMessageBox.information(self, "Успех", "Данные тренера обновлены")
            self.load_data()
            self.clear_form()

    def delete_row(self, row):
        trainer_id = int(self.table.item(row, 0).text())
        self.delete_trainer_by_id(trainer_id)

    def delete_trainer_by_id(self, trainer_id):
        reply = QMessageBox.question(
            self, 'Подтверждение',
            'Вы уверены, что хотите удалить этого тренера?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            query = "DELETE FROM sportsorganizations.trainers WHERE id_trainer = %s"
            if self.db.execute(query, (trainer_id,)):
                QMessageBox.information(self, "Успех", "Тренер удален")
                self.load_data()
                self.clear_form()


class JudgesTab(BaseTab):
    def init_ui(self):
        super().init_ui()
        self.setup_common_ui([
            "ID", "Имя", "Фамилия", "Телефон", "Категория",
            "Дата рождения", "Спортсмен", "Медаль", "Действия"
        ])

        form_layout = QFormLayout()

        self.firstname = QLineEdit()
        self.lastname = QLineEdit()
        self.phone = QLineEdit()
        self.category = QComboBox()
        self.category.addItems(["Национальная", "Международная", "Главный судья"])
        self.birthdate = QDateEdit(calendarPopup=True)
        self.birthdate.setDisplayFormat("dd.MM.yyyy")
        self.athlete_id = QLineEdit()
        self.medal_id = QLineEdit()

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        self.add_button = QPushButton("Добавить")
        self.update_button = QPushButton("Изменить")
        self.delete_button = QPushButton("Удалить")
        self.delete_button.setStyleSheet("background-color: #e74c3c;")
        self.clear_button = QPushButton("Очистить")

        buttons.addWidget(self.add_button, stretch=1)
        buttons.addWidget(self.update_button, stretch=1)
        buttons.addWidget(self.delete_button, stretch=1)
        buttons.addWidget(self.clear_button, stretch=1)

        form_layout.addRow("Имя:", self.firstname)
        form_layout.addRow("Фамилия:", self.lastname)
        form_layout.addRow("Телефон:", self.phone)
        form_layout.addRow("Категория:", self.category)
        form_layout.addRow("Дата рождения:", self.birthdate)
        form_layout.addRow("ID спортсмена:", self.athlete_id)
        form_layout.addRow("ID медали:", self.medal_id)

        self.form_group.setMinimumWidth(600)
        self.form_group.setLayout(form_layout)
        self.buttons_widget.setLayout(buttons)

        self.add_button.clicked.connect(self.add_judge)
        self.update_button.clicked.connect(self.update_judge)
        self.delete_button.clicked.connect(self.delete_judge_by_id)
        self.clear_button.clicked.connect(self.clear_form)
        self.table.cellDoubleClicked.connect(self.on_table_double_click)

        if self.user['role'] == 'judge':
            self.load_data(only_current_user=True)
            self.setup_judge_edit_mode()
        else:
            self.load_data()

    def setup_judge_edit_mode(self):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and int(item.text()) == self.user['id']:
                for col in range(self.table.columnCount()):
                    if self.table.cellWidget(row, col):
                        self.table.removeCellWidget(row, col)
                break

    def on_table_double_click(self, row, col):
        if self.user['role'] != 'organizer':
            return

    def load_data(self, only_current_user=False):
        if only_current_user or self.user['role'] == 'judge':
            query = """
            SELECT j.id_judge, j.firstname, j.lastname, j.phone_number, 
                   j.category, j.birth_date, 
                   a.firstname || ' ' || a.lastname as athlete,
                   m.material || ' (' || m.color || ')' as medal
            FROM sportsorganizations.judges j
            LEFT JOIN sportsorganizations.athletes a ON j.id_athlete = a.id_athlete
            LEFT JOIN sportsorganizations.medals m ON j.id_medal = m.id_medal
            WHERE j.id_judge = %s
            """
            params = (self.user['id'],)
        else:
            query = """
            SELECT j.id_judge, j.firstname, j.lastname, j.phone_number, 
                   j.category, j.birth_date, 
                   a.firstname || ' ' || a.lastname as athlete,
                   m.material || ' (' || m.color || ')' as medal
            FROM sportsorganizations.judges j
            LEFT JOIN sportsorganizations.athletes a ON j.id_athlete = a.id_athlete
            LEFT JOIN sportsorganizations.medals m ON j.id_medal = m.id_medal
            """
            params = None

        result = self.db.execute(query, params, fetch=True)
        if result:
            self.table.setRowCount(len(result))
            for row_idx, row in enumerate(result):
                for col_idx, value in enumerate(row):
                    if col_idx == 5:
                        value = value.strftime("%d.%m.%Y") if value else ""
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    self.table.setItem(row_idx, col_idx, item)

                if self.user['role'] == 'organizer':
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout()
                    actions_layout.setContentsMargins(0, 0, 0, 0)

                    edit_btn = QPushButton("Изменить")
                    edit_btn.clicked.connect(lambda _, r=row_idx: self.edit_judge(r, 0))

                    delete_btn = QPushButton("Удалить")
                    delete_btn.setStyleSheet("background-color: #e74c3c;")
                    delete_btn.clicked.connect(lambda _, r=row_idx: self.delete_row(r))

                    actions_layout.addWidget(edit_btn)
                    actions_layout.addWidget(delete_btn)
                    actions_widget.setLayout(actions_layout)

                    self.table.setCellWidget(row_idx, 8, actions_widget)

    def add_judge(self):
        query = """
        INSERT INTO sportsorganizations.judges 
        (firstname, lastname, phone_number, category, birth_date, id_athlete, id_medal)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        try:
            athlete_id = int(self.athlete_id.text()) if self.athlete_id.text() else None
            medal_id = int(self.medal_id.text()) if self.medal_id.text() else None
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "ID спортсмена и медали должны быть числами")
            return

        params = (
            self.firstname.text(),
            self.lastname.text(),
            self.phone.text(),
            self.category.currentText(),
            self.birthdate.date().toString("yyyy-MM-dd"),
            athlete_id,
            medal_id
        )

        if self.db.execute(query, params):
            QMessageBox.information(self, "Успех", "Судья добавлен")
            self.load_data()
            self.clear_form()

    def edit_judge(self, row, col):
        self.current_id = int(self.table.item(row, 0).text())

        self.firstname.setText(self.table.item(row, 1).text())
        self.lastname.setText(self.table.item(row, 2).text())
        self.phone.setText(self.table.item(row, 3).text())

        category = self.table.item(row, 4).text()
        index = self.category.findText(category)
        self.category.setCurrentIndex(index if index != -1 else 0)

        birthdate = self.table.item(row, 5).text()
        if birthdate:
            date = QDate.fromString(birthdate, "dd.MM.yyyy")
            self.birthdate.setDate(date)

        self.toggle_edit_mode(True)

    def update_judge(self):
        if not self.current_id:
            return

        query = """
        UPDATE sportsorganizations.judges 
        SET firstname = %s, lastname = %s, phone_number = %s, 
            category = %s, birth_date = %s, id_athlete = %s, id_medal = %s
        WHERE id_judge = %s
        """
        try:
            athlete_id = int(self.athlete_id.text()) if self.athlete_id.text() else None
            medal_id = int(self.medal_id.text()) if self.medal_id.text() else None
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "ID спортсмена и медали должны быть числами")
            return

        params = (
            self.firstname.text(),
            self.lastname.text(),
            self.phone.text(),
            self.category.currentText(),
            self.birthdate.date().toString("yyyy-MM-dd"),
            athlete_id,
            medal_id,
            self.current_id
        )

        if self.db.execute(query, params):
            QMessageBox.information(self, "Успех", "Данные судьи обновлены")
            self.load_data()
            self.clear_form()

    def delete_row(self, row):
        judge_id = int(self.table.item(row, 0).text())
        self.delete_judge_by_id(judge_id)

    def delete_judge_by_id(self, judge_id):
        reply = QMessageBox.question(
            self, 'Подтверждение',
            'Вы уверены, что хотите удалить этого судью?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            query = "DELETE FROM sportsorganizations.judges WHERE id_judge = %s"
            if self.db.execute(query, (judge_id,)):
                QMessageBox.information(self, "Успех", "Судья удален")
                self.load_data()
                self.clear_form()

class OrganizersTab(BaseTab):
    def init_ui(self):
        super().init_ui()
        self.setup_common_ui([
            "ID", "Имя", "Фамилия", "Телефон", "Email",
            "Дата рождения", "Место", "Инвентарь", "Действия"
        ])

        form_layout = QFormLayout()

        self.firstname = QLineEdit()
        self.lastname = QLineEdit()
        self.phone = QLineEdit()
        self.email = QLineEdit()
        self.birthdate = QDateEdit(calendarPopup=True)
        self.birthdate.setDisplayFormat("dd.MM.yyyy")
        self.venue = QLineEdit()
        self.inventory = QLineEdit()

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        self.add_button = QPushButton("Добавить")
        self.update_button = QPushButton("Изменить")
        self.delete_button = QPushButton("Удалить")
        self.delete_button.setStyleSheet("background-color: #e74c3c;")
        self.clear_button = QPushButton("Очистить")

        buttons.addWidget(self.add_button, stretch=1)
        buttons.addWidget(self.update_button, stretch=1)
        buttons.addWidget(self.delete_button, stretch=1)
        buttons.addWidget(self.clear_button, stretch=1)

        form_layout.addRow("Имя:", self.firstname)
        form_layout.addRow("Фамилия:", self.lastname)
        form_layout.addRow("Телефон:", self.phone)
        form_layout.addRow("Email:", self.email)
        form_layout.addRow("Дата рождения:", self.birthdate)
        form_layout.addRow("Место:", self.venue)
        form_layout.addRow("Инвентарь:", self.inventory)

        self.form_group.setMinimumWidth(600)
        self.form_group.setLayout(form_layout)
        self.buttons_widget.setLayout(buttons)

        self.add_button.clicked.connect(self.add_organizer)
        self.update_button.clicked.connect(self.update_organizer)
        self.delete_button.clicked.connect(self.delete_organizer_by_id)
        self.clear_button.clicked.connect(self.clear_form)
        self.table.cellDoubleClicked.connect(self.on_table_double_click)

        if self.user['role'] == 'organizer':
            self.load_data(only_current_user=True)
            self.setup_organizer_edit_mode()
        else:
            self.load_data()

    def setup_organizer_edit_mode(self):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and int(item.text()) == self.user['id']:
                edit_btn = QPushButton("Изменить")
                edit_btn.clicked.connect(lambda _, r=row: self.edit_organizer(r, 0))

                for col in range(self.table.columnCount()):
                    if self.table.cellWidget(row, col):
                        self.table.removeCellWidget(row, col)

                actions_widget = QWidget()
                actions_layout = QHBoxLayout()
                actions_layout.setContentsMargins(0, 0, 0, 0)
                actions_layout.addWidget(edit_btn)
                actions_widget.setLayout(actions_layout)
                self.table.setCellWidget(row, 8, actions_widget)
                break

    def on_table_double_click(self, row, col):
        if self.user['role'] == 'organizer':
            item = self.table.item(row, 0)
            if item and int(item.text()) == self.user['id']:
                self.edit_organizer(row, col)

    def load_data(self, only_current_user=False):
        if only_current_user or self.user['role'] == 'organizer':
            query = """
            SELECT o.id_organizer, o.firstname, o.lastname, o.phone_number, 
                   o.email, o.birth_date, 
                   v.name as venue, 
                   i.product_name as inventory
            FROM sportsorganizations.organizers o
            LEFT JOIN sportsorganizations.venues v ON o.id_venue = v.id_venue
            LEFT JOIN sportsorganizations.sports_inventories i ON o.id_inventory = i.id_inventory
            WHERE o.id_organizer = %s
            """
            params = (self.user['id'],)
        else:
            query = """
            SELECT o.id_organizer, o.firstname, o.lastname, o.phone_number, 
                   o.email, o.birth_date, 
                   v.name as venue, 
                   i.product_name as inventory
            FROM sportsorganizations.organizers o
            LEFT JOIN sportsorganizations.venues v ON o.id_venue = v.id_venue
            LEFT JOIN sportsorganizations.sports_inventories i ON o.id_inventory = i.id_inventory
            """
            params = None

        result = self.db.execute(query, params, fetch=True)
        if result:
            self.table.setRowCount(len(result))
            for row_idx, row in enumerate(result):
                for col_idx, value in enumerate(row):
                    if col_idx == 5:
                        value = value.strftime("%d.%m.%Y") if value else ""
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    self.table.setItem(row_idx, col_idx, item)

                if self.user['role'] == 'organizer':
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout()
                    actions_layout.setContentsMargins(0, 0, 0, 0)

                    edit_btn = QPushButton("Изменить")
                    edit_btn.clicked.connect(lambda _, r=row_idx: self.edit_organizer(r, 0))

                    delete_btn = QPushButton("Удалить")
                    delete_btn.setStyleSheet("background-color: #e74c3c;")
                    delete_btn.clicked.connect(lambda _, r=row_idx: self.delete_row(r))

                    actions_layout.addWidget(edit_btn)
                    actions_layout.addWidget(delete_btn)
                    actions_widget.setLayout(actions_layout)

                    self.table.setCellWidget(row_idx, 8, actions_widget)

    def add_organizer(self):
        query = """
        INSERT INTO sportsorganizations.organizers 
        (firstname, lastname, phone_number, email, birth_date)
        VALUES (%s, %s, %s, %s, %s)
        """
        params = (
            self.firstname.text(),
            self.lastname.text(),
            self.phone.text(),
            self.email.text(),
            self.birthdate.date().toString("yyyy-MM-dd")
        )

        if self.db.execute(query, params):
            QMessageBox.information(self, "Успех", "Организатор добавлен")
            self.load_data()
            self.clear_form()

    def edit_organizer(self, row, col):
        self.current_id = int(self.table.item(row, 0).text())

        self.firstname.setText(self.table.item(row, 1).text())
        self.lastname.setText(self.table.item(row, 2).text())
        self.phone.setText(self.table.item(row, 3).text())
        self.email.setText(self.table.item(row, 4).text())

        birthdate = self.table.item(row, 5).text()
        if birthdate:
            date = QDate.fromString(birthdate, "dd.MM.yyyy")
            self.birthdate.setDate(date)

        self.venue.setText(self.table.item(row, 6).text())
        self.inventory.setText(self.table.item(row, 7).text())

        self.toggle_edit_mode(True)

    def update_organizer(self):
        if not self.current_id:
            return

        query = """
        UPDATE sportsorganizations.organizers 
        SET firstname = %s, lastname = %s, phone_number = %s, 
            email = %s, birth_date = %s
        WHERE id_organizer = %s
        """
        params = (
            self.firstname.text(),
            self.lastname.text(),
            self.phone.text(),
            self.email.text(),
            self.birthdate.date().toString("yyyy-MM-dd"),
            self.current_id
        )

        if self.db.execute(query, params):
            QMessageBox.information(self, "Успех", "Данные организатора обновлены")
            self.load_data()
            self.clear_form()

    def delete_row(self, row):
        organizer_id = int(self.table.item(row, 0).text())
        self.delete_organizer_by_id(organizer_id)

    def delete_organizer_by_id(self, organizer_id):
        reply = QMessageBox.question(
            self, 'Подтверждение',
            'Вы уверены, что хотите удалить этого организатора?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            query = "DELETE FROM sportsorganizations.organizers WHERE id_organizer = %s"
            if self.db.execute(query, (organizer_id,)):
                QMessageBox.information(self, "Успех", "Организатор удален")
                self.load_data()
                self.clear_form()


class MedalsTab(BaseTab):
    def init_ui(self):
        super().init_ui()
        self.setup_common_ui([
            "ID", "Материал", "Цвет", "Вес (г)", "Количество", "Действия"
        ])

        form_layout = QFormLayout()

        self.material = QComboBox()
        self.material.addItems(["Золото", "Серебро", "Бронза", "Другой"])
        self.color = QLineEdit()
        self.weight = QLineEdit()
        self.quantity = QLineEdit()

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        self.add_button = QPushButton("Добавить")
        self.update_button = QPushButton("Изменить")
        self.delete_button = QPushButton("Удалить")
        self.delete_button.setStyleSheet("background-color: #e74c3c;")
        self.clear_button = QPushButton("Очистить")

        buttons.addWidget(self.add_button, stretch=1)
        buttons.addWidget(self.update_button, stretch=1)
        buttons.addWidget(self.delete_button, stretch=1)
        buttons.addWidget(self.clear_button, stretch=1)

        form_layout.addRow("Материал:", self.material)
        form_layout.addRow("Цвет:", self.color)
        form_layout.addRow("Вес (г):", self.weight)
        form_layout.addRow("Количество:", self.quantity)

        self.form_group.setMinimumWidth(600)
        self.form_group.setLayout(form_layout)
        self.buttons_widget.setLayout(buttons)

        self.add_button.clicked.connect(self.add_medal)
        self.update_button.clicked.connect(self.update_medal)
        self.delete_button.clicked.connect(self.delete_medal_by_id)
        self.clear_button.clicked.connect(self.clear_form)
        self.table.cellDoubleClicked.connect(self.on_table_double_click)

        if self.user['role'] not in ['judge', 'organizer']:
            self.form_group.hide()
            for btn in [self.add_button, self.update_button, self.delete_button]:
                btn.hide()

        self.load_data()

    def on_table_double_click(self, row, col):
        if self.user['role'] in ['judge', 'organizer']:
            self.edit_medal(row, col)

    def load_data(self):
        query = """
        SELECT id_medal, material, color, weight, quantity
        FROM sportsorganizations.medals
        """
        result = self.db.execute(query, fetch=True)

        if result:
            self.table.setRowCount(len(result))
            for row_idx, row in enumerate(result):
                for col_idx, value in enumerate(row):
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    self.table.setItem(row_idx, col_idx, item)

                if self.user['role'] in ['judge', 'organizer']:
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout()
                    actions_layout.setContentsMargins(0, 0, 0, 0)

                    edit_btn = QPushButton("Изменить")
                    edit_btn.clicked.connect(lambda _, r=row_idx: self.edit_medal(r, 0))

                    delete_btn = QPushButton("Удалить")
                    delete_btn.setStyleSheet("background-color: #e74c3c;")
                    delete_btn.clicked.connect(lambda _, r=row_idx: self.delete_row(r))

                    actions_layout.addWidget(edit_btn)
                    actions_layout.addWidget(delete_btn)
                    actions_widget.setLayout(actions_layout)

                    self.table.setCellWidget(row_idx, 5, actions_widget)

    def add_medal(self):
        query = """
        INSERT INTO sportsorganizations.medals 
        (material, color, weight, quantity)
        VALUES (%s, %s, %s, %s)
        """
        try:
            weight = float(self.weight.text())
            quantity = int(self.quantity.text())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Вес и количество должны быть числами")
            return

        params = (
            self.material.currentText(),
            self.color.text(),
            weight,
            quantity
        )

        if self.db.execute(query, params):
            QMessageBox.information(self, "Успех", "Медаль добавлена")
            self.load_data()
            self.clear_form()

    def edit_medal(self, row, col):
        self.current_id = int(self.table.item(row, 0).text())

        material = self.table.item(row, 1).text()
        index = self.material.findText(material)
        self.material.setCurrentIndex(index if index != -1 else 0)

        self.color.setText(self.table.item(row, 2).text())
        self.weight.setText(self.table.item(row, 3).text())
        self.quantity.setText(self.table.item(row, 4).text())

        self.toggle_edit_mode(True)

    def update_medal(self):
        if not self.current_id:
            return

        query = """
        UPDATE sportsorganizations.medals 
        SET material = %s, color = %s, weight = %s, quantity = %s
        WHERE id_medal = %s
        """
        try:
            weight = float(self.weight.text())
            quantity = int(self.quantity.text())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Вес и количество должны быть числами")
            return

        params = (
            self.material.currentText(),
            self.color.text(),
            weight,
            quantity,
            self.current_id
        )

        if self.db.execute(query, params):
            QMessageBox.information(self, "Успех", "Данные медали обновлены")
            self.load_data()
            self.clear_form()

    def delete_row(self, row):
        medal_id = int(self.table.item(row, 0).text())
        self.delete_medal_by_id(medal_id)

    def delete_medal_by_id(self, medal_id):
        reply = QMessageBox.question(
            self, 'Подтверждение',
            'Вы уверены, что хотите удалить эту медаль?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            query = "DELETE FROM sportsorganizations.medals WHERE id_medal = %s"
            if self.db.execute(query, (medal_id,)):
                QMessageBox.information(self, "Успех", "Медаль удалена")
                self.load_data()
                self.clear_form()


class MainWindow(QMainWindow):
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"Спортивные организации ({self.user['role']})")
        self.setGeometry(100, 100, 1200, 800)

        self.tabs = QTabWidget()

        self.tabs.addTab(AthletesTab(self.db, self.user), "Спортсмены")

        if self.user['role'] in ['trainer', 'organizer']:
            self.tabs.addTab(TrainersTab(self.db, self.user), "Тренеры")

        if self.user['role'] in ['judge', 'organizer']:
            self.tabs.addTab(JudgesTab(self.db, self.user), "Судьи")
            self.tabs.addTab(MedalsTab(self.db, self.user), "Медали")

        if self.user['role'] == 'organizer':
            self.tabs.addTab(OrganizersTab(self.db, self.user), "Организаторы")

        self.setCentralWidget(self.tabs)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    setup_style(app)

    db = Database()
    if not db.connect():
        sys.exit(1)

    auth = AuthWindow(db)
    if auth.exec_():
        window = MainWindow(db, auth.user)
        window.show()
        sys.exit(app.exec_())
