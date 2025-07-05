from datetime import datetime
import sys
import os
import shutil
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QStackedWidget, QFileDialog, QScrollArea,
    QFrame
)
from PyQt6.QtGui import QPixmap, QFont, QPainter, QBrush, QColor, QPalette
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QPainterPath

from database import DatabaseManager, BASE_DIR
from client import ClientThread

class CustomMessageBox(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(300, 150)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.message_label = QLabel("", self)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setFont(QFont("Inter", 10))
        self.message_label.setStyleSheet("color: #FFFFFF;")

        self.ok_button = QPushButton("باشه", self)
        self.ok_button.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 10px;
                padding: 8px 20px;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.ok_button.setFixedSize(100, 35)
        self.ok_button.clicked.connect(self.hide)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addStretch()

        layout.addWidget(self.message_label)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        if parent:
            self.move(parent.geometry().center() - self.rect().center())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor(40, 40, 60, 240)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 15, 15)

    def show_message(self, message):
        self.message_label.setText(message)
        self.show()
        self.raise_() 
        self.activateWindow() 
GLOBAL_STYLES = """
    QWidget {
        background-color: #282a36; /* Dark background */
        color: #f8f8f2; /* Light text */
        font-family: "Inter";
    }
    QLineEdit {
        background-color: #44475a; /* Darker input background */
        border: 1px solid #6272a4; /* Border color */
        border-radius: 8px;
        padding: 10px;
        color: #f8f8f2;
        font-size: 14px;
    }
    QLineEdit:focus {
        border: 1px solid #8be9fd; /* Highlight on focus */
    }
    QPushButton {
        background-color: #50fa7b; /* Green button */
        color: #282a36; /* Dark text on button */
        border-radius: 10px;
        padding: 12px 25px;
        font-size: 16px;
        font-weight: bold;
        border: none;
    }
    QPushButton:hover {
        background-color: #69ff94; /* Lighter green on hover */
    }
    QLabel {
        color: #f8f8f2;
    }
"""

class BaseWindow(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(GLOBAL_STYLES)
        self.message_box = CustomMessageBox(self)
        self.message_box.hide()  
    def show_message(self, message):
        if self.parent():
            parent_center = self.parent().geometry().center()
        else:
            parent_center = self.geometry().center()
        
        self.message_box.move(parent_center - self.message_box.rect().center())
        self.message_box.show_message(message)
class SignInWindow(BaseWindow):
    signed_in = pyqtSignal(dict) 

    def __init__(self, stacked_widget, db_manager):
        super().__init__(stacked_widget)
        self.stacked_widget = stacked_widget
        self.db_manager = db_manager
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("ورود به مسنجر")
        self.setGeometry(100, 100, 400, 300)

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setSpacing(20)

        title_label = QLabel("ورود")
        title_label.setFont(QFont("Inter", 24, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("نام کاربری")
        main_layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("رمز عبور")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        main_layout.addWidget(self.password_input)

        sign_in_button = QPushButton("ورود")
        sign_in_button.clicked.connect(self.handle_sign_in)
        main_layout.addWidget(sign_in_button)

        go_to_signup_button = QPushButton("ساخت حساب جدید")
        go_to_signup_button.setStyleSheet("""
            QPushButton {
                background-color: #6272a4; /* Purple-ish color */
                color: white;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #7a89b8;
            }
        """)
        go_to_signup_button.clicked.connect(self.go_to_signup)
        main_layout.addWidget(go_to_signup_button)

        self.setLayout(main_layout)

    def handle_sign_in(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            self.show_message("لطفاً نام کاربری و رمز عبور را وارد کنید.")
            return

        user_data = self.db_manager.authenticate_user(username, password)
        if user_data:
            self.show_message("ورود با موفقیت انجام شد!")
            self.signed_in.emit(user_data)
            self.username_input.clear()
            self.password_input.clear()
        else:
            self.show_message("نام کاربری یا رمز عبور اشتباه است.")

    def go_to_signup(self):
        self.stacked_widget.setCurrentIndex(1)


class SignUpWindow(BaseWindow):
    def __init__(self, stacked_widget, db_manager):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.db_manager = db_manager
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("ثبت نام در مسنجر")
        self.setGeometry(100, 100, 400, 400)

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setSpacing(15)

        title_label = QLabel("ثبت نام")
        title_label.setFont(QFont("Inter", 24, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("شماره تلفن")
        main_layout.addWidget(self.phone_input)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("نام کاربری")
        main_layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("رمز عبور")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        main_layout.addWidget(self.password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("تایید رمز عبور")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        main_layout.addWidget(self.confirm_password_input)

        sign_up_button = QPushButton("ثبت نام")
        sign_up_button.clicked.connect(self.handle_sign_up)
        main_layout.addWidget(sign_up_button)

        go_to_signin_button = QPushButton("ورود به حساب کاربری")
        go_to_signin_button.setStyleSheet("""
            QPushButton {
                background-color: #6272a4;
                color: white;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #7a89b8;
            }
        """)
        go_to_signin_button.clicked.connect(self.go_to_signin)
        main_layout.addWidget(go_to_signin_button)

        self.setLayout(main_layout)

    def handle_sign_up(self):
        phone = self.phone_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()

        if not (phone and username and password and confirm_password):
            self.show_message("لطفاً تمام فیلدها را پر کنید.")
            return

        if password != confirm_password:
            self.show_message("رمز عبور و تایید آن مطابقت ندارند.")
            return

        success, message = self.db_manager.register_user(username, password, phone)
        self.show_message(message)
        if success:
            self.phone_input.clear()
            self.username_input.clear()
            self.password_input.clear()
            self.confirm_password_input.clear()
            self.go_to_signin()

    def go_to_signin(self):
        self.stacked_widget.setCurrentIndex(0)


class MainWindow(BaseWindow):
    def __init__(self, stacked_widget, db_manager, current_user):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.db_manager = db_manager
        self.current_user = current_user
        self.current_chat_partner = None
        
        # ایجاد کلاینت برای ارتباط با سرور
        self.client_thread = ClientThread(current_user["username"])
        self.client_thread.message_received.connect(self.handle_received_message)
        self.client_thread.start()
        
        self.init_ui()
        self.load_contacts()

    def init_ui(self):
        self.setWindowTitle(f"مسنجر - خوش آمدید {self.current_user['username']}")
        self.setGeometry(100, 100, 900, 600)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        left_panel = QFrame()
        left_panel.setFixedWidth(250)
        left_panel.setStyleSheet("background-color: #383a59; border-right: 1px solid #44475a;")
        left_panel_layout = QVBoxLayout(left_panel)
        left_panel_layout.setContentsMargins(10, 10, 10, 10)
        left_panel_layout.setSpacing(10)

        user_profile_layout = QHBoxLayout()
        self.user_profile_pic_label = QLabel()
        self.user_profile_pic_label.setFixedSize(50, 50)
        self.user_profile_pic_label.setStyleSheet("border-radius: 25px; background-color: #6272a4;")
        self.user_profile_pic_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.load_profile_picture(self.current_user.get('profile_pic_path'))
        
        user_name_label = QLabel(self.current_user['username'])
        user_name_label.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        user_profile_layout.addWidget(self.user_profile_pic_label)
        user_profile_layout.addWidget(user_name_label)
        user_profile_layout.addStretch()

        settings_button = QPushButton("تنظیمات")
        settings_button.setFixedSize(30, 30)
        settings_button.setStyleSheet("""
            QPushButton {
                background-color: #bd93f9; /* Purple */
                border-radius: 15px;
                font-size: 10px;
                color: #282a36;
            }
            QPushButton:hover {
                background-color: #ff79c6; /* Pink */
            }
        """)
        settings_button.setText("⚙")
        settings_button.clicked.connect(self.show_settings_panel)
        user_profile_layout.addWidget(settings_button)

        add_contact_button = QPushButton("افزودن")
        add_contact_button.setFixedSize(30, 30)
        add_contact_button.setStyleSheet("""
            QPushButton {
                background-color: #ffb86c; /* Orange */
                border-radius: 15px;
                font-size: 10px;
                color: #282a36;
            }
            QPushButton:hover {
                background-color: #ff9248;
            }
        """)
        add_contact_button.setText("➕")
        add_contact_button.clicked.connect(self.show_add_contact_panel)
        user_profile_layout.addWidget(add_contact_button)

        left_panel_layout.addLayout(user_profile_layout)
        #left_panel_layout.addSeparator()

        self.contacts_list_widget = QWidget()
        self.contacts_list_layout = QVBoxLayout(self.contacts_list_widget)
        self.contacts_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.contacts_list_layout.setContentsMargins(0, 0, 0, 0)
        self.contacts_list_layout.setSpacing(5)

        contacts_scroll_area = QScrollArea()
        contacts_scroll_area.setWidgetResizable(True)
        contacts_scroll_area.setWidget(self.contacts_list_widget)
        contacts_scroll_area.setStyleSheet("border: none;")
        left_panel_layout.addWidget(contacts_scroll_area)

        main_layout.addWidget(left_panel)

        self.right_panel = QStackedWidget()
        self.right_panel.setStyleSheet("background-color: #44475a;")
        main_layout.addWidget(self.right_panel)

        welcome_page = QLabel("یک چت را انتخاب کنید یا مخاطب جدید اضافه کنید.")
        welcome_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_page.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        welcome_page.setStyleSheet("color: #6272a4;")
        self.right_panel.addWidget(welcome_page)

        self.chat_page = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_page)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)
        self.chat_layout.setSpacing(5)

        self.chat_partner_label = QLabel("انتخاب نشده")
        self.chat_partner_label.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        self.chat_partner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chat_partner_label.setStyleSheet("padding-bottom: 10px; border-bottom: 1px solid #6272a4;")
        self.chat_layout.addWidget(self.chat_partner_label)

        self.message_display_area = QScrollArea()
        self.message_display_area.setWidgetResizable(True)
        self.message_content_widget = QWidget()
        self.message_content_layout = QVBoxLayout(self.message_content_widget)
        self.message_content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.message_content_layout.setContentsMargins(0, 0, 0, 0)
        self.message_display_area.setWidget(self.message_content_widget)
        self.message_display_area.setStyleSheet("border: none;")
        self.chat_layout.addWidget(self.message_display_area)

        message_input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("پیام خود را بنویسید...")
        self.message_input.returnPressed.connect(self.send_message)
        message_input_layout.addWidget(self.message_input)

        send_button = QPushButton("ارسال")
        send_button.setFixedSize(80, 40)
        send_button.clicked.connect(self.send_message)
        message_input_layout.addWidget(send_button)
        self.chat_layout.addLayout(message_input_layout)

        self.right_panel.addWidget(self.chat_page)

        self.add_contact_panel = QWidget()
        add_contact_layout = QVBoxLayout(self.add_contact_panel)
        add_contact_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        add_contact_layout.setSpacing(15)

        add_contact_title = QLabel("افزودن مخاطب جدید")
        add_contact_title.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        add_contact_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        add_contact_layout.addWidget(add_contact_title)

        self.add_contact_username_input = QLineEdit()
        self.add_contact_username_input.setPlaceholderText("نام کاربری مخاطب")
        add_contact_layout.addWidget(self.add_contact_username_input)

        self.add_contact_phone_input = QLineEdit()
        self.add_contact_phone_input.setPlaceholderText("شماره تلفن مخاطب")
        add_contact_layout.addWidget(self.add_contact_phone_input)

        add_contact_button_final = QPushButton("افزودن")
        add_contact_button_final.clicked.connect(self.add_contact_to_list)
        add_contact_layout.addWidget(add_contact_button_final)

        self.right_panel.addWidget(self.add_contact_panel)

        self.profile_panel = QWidget()
        profile_layout = QVBoxLayout(self.profile_panel)
        profile_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        profile_layout.setSpacing(15)

        profile_title = QLabel("پروفایل من")
        profile_title.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        profile_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        profile_layout.addWidget(profile_title)

        self.profile_pic_display = QLabel()
        self.profile_pic_display.setFixedSize(120, 120)
        self.profile_pic_display.setStyleSheet("border-radius: 60px; background-color: #6272a4;")
        self.profile_pic_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.load_profile_picture_full(self.current_user.get('profile_pic_path'))
        profile_layout.addWidget(self.profile_pic_display, alignment=Qt.AlignmentFlag.AlignCenter)

        self.profile_username_label = QLabel(f"نام کاربری: {self.current_user['username']}")
        self.profile_username_label.setFont(QFont("Inter", 14))
        self.profile_username_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        profile_layout.addWidget(self.profile_username_label)

        self.profile_phone_label = QLabel(f"شماره تلفن: {self.current_user['phone']}")
        self.profile_phone_label.setFont(QFont("Inter", 14))
        self.profile_phone_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        profile_layout.addWidget(self.profile_phone_label)

        self.right_panel.addWidget(self.profile_panel)

        self.settings_panel = QWidget()
        settings_layout = QVBoxLayout(self.settings_panel)
        settings_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        settings_layout.setSpacing(15)

        settings_title = QLabel("تنظیمات")
        settings_title.setFont(QFont("Inter", 20, QFont.Weight.Bold))
        settings_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        settings_layout.addWidget(settings_title)

        # Username
        settings_layout.addWidget(QLabel("نام کاربری جدید:"))
        self.settings_username_input = QLineEdit(self.current_user['username'])
        settings_layout.addWidget(self.settings_username_input)

        # Phone Number
        settings_layout.addWidget(QLabel("شماره تلفن جدید:"))
        self.settings_phone_input = QLineEdit(self.current_user['phone'])
        settings_layout.addWidget(self.settings_phone_input)

        # New Password
        settings_layout.addWidget(QLabel("رمز عبور جدید:"))
        self.settings_new_password_input = QLineEdit()
        self.settings_new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        settings_layout.addWidget(self.settings_new_password_input)

        # Confirm New Password
        settings_layout.addWidget(QLabel("تایید رمز عبور جدید:"))
        self.settings_confirm_new_password_input = QLineEdit()
        self.settings_confirm_new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        settings_layout.addWidget(self.settings_confirm_new_password_input)

        change_pic_button = QPushButton("تغییر عکس پروفایل")
        change_pic_button.clicked.connect(self.choose_image)
        settings_layout.addWidget(change_pic_button)

        save_changes_button = QPushButton("ذخیره تغییرات")
        save_changes_button.clicked.connect(self.save_settings_changes)
        settings_layout.addWidget(save_changes_button)

        self.right_panel.addWidget(self.settings_panel)


        self.setLayout(main_layout)

    def load_profile_picture(self, path):
        if path and os.path.exists(path):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                
                # Create a circular pixmap
                circle_pixmap = QPixmap(50, 50)
                circle_pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(circle_pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                path = QPainterPath()
                path.addEllipse(0, 0, 50, 50)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, scaled_pixmap)
                painter.end()
                
                self.user_profile_pic_label.setPixmap(circle_pixmap)
            else:
                self.user_profile_pic_label.setText("عکس")
        else:
            self.user_profile_pic_label.setText("عکس")

    def load_profile_picture_full(self, path):
        if path and os.path.exists(path):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                
                # Create a circular pixmap
                circle_pixmap = QPixmap(120, 120)
                circle_pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(circle_pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                path = QPainterPath()
                path.addEllipse(0, 0, 120, 120)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, scaled_pixmap)
                painter.end()
                
                self.profile_pic_display.setPixmap(circle_pixmap)
            else:
                self.profile_pic_display.setText("عکس")
        else:
            self.profile_pic_display.setText("عکس")

    def choose_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "انتخاب عکس پروفایل",
            "",
            "فایل‌های تصویری (*.png *.jpg *.jpeg)"
        )

        if file_path:
            profile_pics_dir = os.path.join(BASE_DIR, "profile_pics")
            os.makedirs(profile_pics_dir, exist_ok=True)

            file_extension = os.path.splitext(file_path)[1]
            dest_file_name = f"user_{self.current_user['id']}{file_extension}"
            dest_path = os.path.join(profile_pics_dir, dest_file_name)

            try:
                shutil.copyfile(file_path, dest_path)
                self.current_user['profile_pic_path'] = dest_path
                success, msg = self.db_manager.update_user_info(
                    self.current_user['id'],
                    new_profile_pic_path=dest_path
                )
                if success:
                    self.show_message("عکس پروفایل با موفقیت به روز شد!")
                    self.load_profile_picture(dest_path)
                    self.load_profile_picture_full(dest_path)
                else:
                    self.show_message(f"خطا در به روز رسانی عکس پروفایل در دیتابیس: {msg}")
            except Exception as e:
                self.show_message(f"خطا در کپی فایل عکس: {e}")

    def save_settings_changes(self):
        new_username = self.settings_username_input.text().strip()
        new_phone = self.settings_phone_input.text().strip()
        new_password = self.settings_new_password_input.text().strip()
        confirm_new_password = self.settings_confirm_new_password_input.text().strip()

        updates = {}
        if new_username and new_username != self.current_user['username']:
            updates['new_username'] = new_username
        if new_phone and new_phone != self.current_user['phone']:
            updates['new_phone'] = new_phone
        
        if new_password:
            if new_password != confirm_new_password:
                self.show_message("رمز عبور جدید و تایید آن مطابقت ندارند.")
                return
            updates['new_password'] = new_password
        
        if not updates:
            self.show_message("هیچ تغییری برای ذخیره وجود ندارد.")
            return

        success, message = self.db_manager.update_user_info(self.current_user['id'], **updates)
        self.show_message(message)
        if success:
            if 'new_username' in updates:
                self.current_user['username'] = updates['new_username']
                self.user_profile_pic_label.setText(self.current_user['username'])
                self.profile_username_label.setText(f"نام کاربری: {self.current_user['username']}")
            if 'new_phone' in updates:
                self.current_user['phone'] = updates['new_phone']
                self.profile_phone_label.setText(f"شماره تلفن: {self.current_user['phone']}")
            self.settings_new_password_input.clear()
            self.settings_confirm_new_password_input.clear()

            self.load_contacts()


    def load_contacts(self):
        for i in reversed(range(self.contacts_list_layout.count())):
            widget_to_remove = self.contacts_list_layout.itemAt(i).widget()
            if widget_to_remove:
                widget_to_remove.setParent(None)
        all_users = []
        try:
            self.db_manager.cursor.execute("SELECT id, username, profile_pic_path FROM users WHERE id != ?", (self.current_user['id'],))
            all_users = [{"id": row[0], "username": row[1], "profile_pic_path": row[2]} for row in self.db_manager.cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching all users for contacts: {e}")

        if not all_users:
            no_contacts_label = QLabel("مخاطبی یافت نشد.")
            no_contacts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_contacts_label.setStyleSheet("color: #6272a4; padding: 20px;")
            self.contacts_list_layout.addWidget(no_contacts_label)
            return

        for contact_data in all_users:
            self.add_contact_item_to_list(contact_data)

    def add_contact_item_to_list(self, contact_data):
        contact_frame = QFrame()
        contact_frame.setStyleSheet("""
            QFrame {
                background-color: #44475a;
                border-radius: 10px;
                padding: 5px;
            }
            QFrame:hover {
                background-color: #6272a4;
            }
        """)
        contact_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        contact_layout = QHBoxLayout(contact_frame)
        contact_layout.setContentsMargins(5, 5, 5, 5)

        contact_pic_label = QLabel()
        contact_pic_label.setFixedSize(40, 40)
        contact_pic_label.setStyleSheet("border-radius: 20px; background-color: #bd93f9;")
        contact_pic_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Load contact's profile picture
        if contact_data.get('profile_pic_path') and os.path.exists(contact_data['profile_pic_path']):
            pixmap = QPixmap(contact_data['profile_pic_path'])
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                
                circle_pixmap = QPixmap(40, 40)
                circle_pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(circle_pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                path = QPainterPath()
                path.addEllipse(0, 0, 40, 40)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, scaled_pixmap)
                painter.end()
                
                contact_pic_label.setPixmap(circle_pixmap)
            else:
                contact_pic_label.setText("عکس")
        else:
            contact_pic_label.setText("عکس")

        contact_name_label = QLabel(contact_data['username'])
        contact_name_label.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        contact_name_label.setStyleSheet("color: #f8f8f2;")

        contact_layout.addWidget(contact_pic_label)
        contact_layout.addWidget(contact_name_label)
        contact_layout.addStretch()

        contact_frame.mousePressEvent = lambda event, cd=contact_data: self.open_chat(cd)
        self.contacts_list_layout.addWidget(contact_frame)

    def add_contact_to_list(self):
        username = self.add_contact_username_input.text().strip()
        phone = self.add_contact_phone_input.text().strip()

        if not username and not phone:
            self.show_message("لطفاً نام کاربری یا شماره تلفن مخاطب را وارد کنید.")
            return

        contact_info = None
        if username:
            contact_info = self.db_manager.get_user_info(username=username)
        if not contact_info and phone:
            contact_info = self.db_manager.get_user_info(phone=phone)

        if contact_info and contact_info['id'] != self.current_user['id']:
            for i in range(self.contacts_list_layout.count()):
                item_widget = self.contacts_list_layout.itemAt(i).widget()
                if item_widget and hasattr(item_widget, 'contact_data') and item_widget.contact_data['id'] == contact_info['id']:
                    self.show_message("این مخاطب قبلاً اضافه شده است.")
                    self.add_contact_username_input.clear()
                    self.add_contact_phone_input.clear()
                    self.right_panel.setCurrentIndex(0)
                    return

            self.add_contact_item_to_list(contact_info)
            self.show_message(f"مخاطب '{contact_info['username']}' با موفقیت اضافه شد.")
            self.add_contact_username_input.clear()
            self.add_contact_phone_input.clear()
            self.right_panel.setCurrentIndex(0)
        else:
            self.show_message("مخاطب یافت نشد یا شما نمی‌توانید خودتان را اضافه کنید.")
    def show_add_contact_panel(self):
        self.right_panel.setCurrentIndex(2)

    def show_profile_panel(self):
        self.profile_username_label.setText(f"نام کاربری: {self.current_user['username']}")
        self.profile_phone_label.setText(f"شماره تلفن: {self.current_user['phone']}")
        self.load_profile_picture_full(self.current_user.get('profile_pic_path'))
        self.right_panel.setCurrentIndex(3)

    def show_settings_panel(self):
        self.settings_username_input.setText(self.current_user['username'])
        self.settings_phone_input.setText(self.current_user['phone'])
        self.settings_new_password_input.clear()
        self.settings_confirm_new_password_input.clear()
        self.right_panel.setCurrentIndex(4)

    def open_chat(self, contact_data):
        """
        Opens the chat window for the selected contact.
        """
        self.clear_chat_messages()
        self.current_chat_partner = contact_data
        self.chat_partner_label.setText(f"چت با {contact_data['username']}")
        self.right_panel.setCurrentIndex(1)
        self.load_chat_history()

    def clear_chat_messages(self):
        for i in reversed(range(self.message_content_layout.count())):
            item = self.message_content_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                for j in reversed(range(item.layout().count())):
                    sub_item = item.layout().itemAt(j)
                    if sub_item.widget():
                        sub_item.widget().deleteLater()
                item.layout().deleteLater()
    def load_chat_history(self):
        for i in reversed(range(self.message_content_layout.count())):
            widget_to_remove = self.message_content_layout.itemAt(i).widget()
            if widget_to_remove:
                widget_to_remove.setParent(None)

        if not self.current_chat_partner:
            return

        messages = self.db_manager.get_messages(self.current_user['id'], self.current_chat_partner['id'])

        if not messages:
            no_messages_label = QLabel("هنوز پیامی در این چت وجود ندارد.")
            no_messages_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_messages_label.setStyleSheet("color: #6272a4; padding: 20px;")
            self.message_content_layout.addWidget(no_messages_label)
            return

        for msg in messages:
            is_sender = (msg['sender_id'] == self.current_user['id'])
            self.display_message(msg['message_text'], is_sender, msg['timestamp'])

        self.message_display_area.verticalScrollBar().rangeChanged.connect(
            lambda min_val, max_val: self.message_display_area.verticalScrollBar().setValue(max_val)
        )


    def display_message(self, message_text, is_sender, timestamp):
        message_bubble = QLabel(message_text)
        message_bubble.setWordWrap(True)
        message_bubble.setFont(QFont("Inter", 11))
        message_bubble.setContentsMargins(10, 5, 10, 5)
        message_bubble.setMinimumWidth(100)

        if is_sender:
            message_bubble.setStyleSheet("""
                background-color: #50fa7b; /* Green for sender */
                color: #282a36;
                border-radius: 10px;
                padding: 8px;
                margin-left: 50px; /* Align right */
            """)
            message_bubble.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            h_layout = QHBoxLayout()
            h_layout.addStretch()
            h_layout.addWidget(message_bubble)
        else:
            message_bubble.setStyleSheet("""
                background-color: #6272a4; /* Purple-ish for receiver */
                color: #f8f8f2;
                border-radius: 10px;
                padding: 8px;
                margin-right: 50px; /* Align left */
            """)
            message_bubble.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            h_layout = QHBoxLayout()
            h_layout.addWidget(message_bubble)
            h_layout.addStretch()
        
        self.message_content_layout.addLayout(h_layout)

        timestamp_label = QLabel(timestamp.split('.')[0])
        timestamp_label.setFont(QFont("Inter", 8))
        timestamp_label.setStyleSheet("color: #999999;")
        if is_sender:
            timestamp_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            timestamp_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.message_content_layout.addWidget(timestamp_label)

    def handle_received_message(self, message_data):
        # بررسی آیا پیام مربوط به چت فعلی است
        if (self.current_chat_partner and 
            ((message_data['sender'] == self.current_chat_partner['username'] and 
              message_data['receiver'] == self.current_user['username']) or
             (message_data['sender'] == self.current_user['username'] and 
              message_data['receiver'] == self.current_chat_partner['username']))):
            
            is_sender = (message_data['sender'] == self.current_user['username'])
            self.display_message(message_data['message'], is_sender, message_data['timestamp'])
        
        # ذخیره پیام در دیتابیس
        sender_info = self.db_manager.get_user_info(username=message_data['sender'])
        receiver_info = self.db_manager.get_user_info(username=message_data['receiver'])
        
        if sender_info and receiver_info:
            self.db_manager.save_message(
                sender_info['id'],
                receiver_info['id'],
                message_data['message'],
                message_data['timestamp']
            )

    def send_message(self):
        message_text = self.message_input.text().strip()
        if not message_text or not self.current_chat_partner:
            return
        
        # فقط یک بار پیام را نمایش دهید (قبل از ارسال به سرور)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.message_input.clear()
        
        # ارسال پیام به سرور
        self.client_thread.send_message(message_text, self.current_chat_partner['username'])
        
    def closeEvent(self, event):
        # توقف کلاینت هنگام بسته شدن پنجره
        self.client_thread.stop_client()
        event.accept()

class MessengerApp(QApplication):
    def __init__(self, sys_argv):
        super().__init__(sys_argv)
        self.db_manager = DatabaseManager()  # Initialize database manager
        self.setup_ui()

    def setup_ui(self):
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setWindowTitle("مسنجر")
        self.stacked_widget.setMinimumSize(400, 300)

        self.sign_in_window = SignInWindow(self.stacked_widget, self.db_manager)
        self.sign_up_window = SignUpWindow(self.stacked_widget, self.db_manager)

        self.stacked_widget.addWidget(self.sign_in_window)
        self.stacked_widget.addWidget(self.sign_up_window)

        # Connect the signal to the slot
        self.sign_in_window.signed_in.connect(self.show_main_window)

        self.stacked_widget.show()
    def show_main_window(self, user_data):
        # اگر ویجت اصلی از قبل وجود دارد، آن را پاک کنید
        if hasattr(self, 'main_window'):
            self.main_window.deleteLater()

        # ایجاد ویجت اصلی جدید
        self.main_window = MainWindow(self.stacked_widget, self.db_manager, user_data)
        
        # افزودن ویجت به QStackedWidget و نمایش آن
        self.stacked_widget.addWidget(self.main_window)
        self.stacked_widget.setCurrentWidget(self.main_window)
        
        # تنظیم اندازه پنجره برای صفحه اصلی
        self.stacked_widget.setMinimumSize(900, 600)
        self.stacked_widget.resize(900, 600)  # تنظیم اندازه اولیه
    def shutdown(self):
        self.db_manager.close()
        print("Application shutting down. Database connection closed.")


if __name__ == "__main__":
    app = MessengerApp(sys.argv)
    sys.exit(app.exec())
