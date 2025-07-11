import sqlite3
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, 'messenger.db') 

class DatabaseManager:
    def __init__(self):
        self.conn = None
        self.connect()
        self.create_tables()

    def connect(self):
        if self.conn:
            self.conn.close()
        try:
            self.conn = sqlite3.connect(DB_NAME)
            self.cursor = self.conn.cursor()
            print(f"Connected to database: {DB_NAME}")
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")

    def create_tables(self):
        """
        Creates the 'users' and 'messages' tables if they do not already exist.
        - 'users' table stores user registration information.
        - 'messages' table stores chat messages between users.
        """
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    phone TEXT UNIQUE NOT NULL,
                    profile_pic_path TEXT
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER NOT NULL,
                    receiver_id INTEGER NOT NULL,
                    message_text TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sender_id) REFERENCES users(id),
                    FOREIGN KEY (receiver_id) REFERENCES users(id)
                )
            ''')
            self.conn.commit()
            print("Tables created successfully or already exist.")
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")

    def message_exists(self, sender_id, receiver_id, message_text, timestamp):
        self.cursor.execute("""
            SELECT 1 FROM messages 
            WHERE sender_id = ? AND receiver_id = ? 
            AND message_text = ? AND timestamp = ?
        """, (sender_id, receiver_id, message_text, timestamp))
        return self.cursor.fetchone() is not None


    def register_user(self, username, password, phone):
        try:
            self.cursor.execute("SELECT id FROM users WHERE username = ? OR phone = ?", (username, phone))
            if self.cursor.fetchone():
                return False, "نام کاربری یا شماره تلفن قبلاً استفاده شده است." 
            
            self.cursor.execute("INSERT INTO users (username, password, phone) VALUES (?, ?, ?)",
                                (username, password, phone))
            self.conn.commit()
            print(f"User '{username}' registered successfully.")
            return True, "ثبت نام با موفقیت انجام شد." 
        except sqlite3.Error as e:
            print(f"Error registering user: {e}")
            return False, f"خطا در ثبت نام: {e}" 

    def authenticate_user(self, username, password):
        try:
            self.cursor.execute("SELECT id, username, phone, profile_pic_path FROM users WHERE username = ? AND password = ?",
                                (username, password))
            user_data = self.cursor.fetchone()
            if user_data:
                user_id, username, phone, profile_pic_path = user_data
                print(f"User '{username}' authenticated successfully. ID: {user_id}")
                return {"id": user_id, "username": username, "phone": phone, "profile_pic_path": profile_pic_path}
            else:
                print("Authentication failed: Invalid username or password.")
                return None
        except sqlite3.Error as e:
            print(f"Error authenticating user: {e}")
            return None

    def get_user_info(self, user_id=None, username=None, phone=None):
        try:
            if user_id:
                self.cursor.execute("SELECT id, username, phone, profile_pic_path FROM users WHERE id = ?", (user_id,))
            elif username:
                self.cursor.execute("SELECT id, username, phone, profile_pic_path FROM users WHERE username = ?", (username,))
            elif phone:
                self.cursor.execute("SELECT id, username, phone, profile_pic_path FROM users WHERE phone = ?", (phone,))
            else:
                return None

            user_data = self.cursor.fetchone()
            if user_data:
                return {"id": user_data[0], "username": user_data[1], "phone": user_data[2], "profile_pic_path": user_data[3]}
            else:
                return None
        except sqlite3.Error as e:
            print(f"Error getting user info: {e}")
            return None

    def update_user_info(self, user_id, new_username=None, new_password=None, new_phone=None, new_profile_pic_path=None):
        """
        Updates user information.
        Returns True on success, False if new username/phone already exists or on other errors.
        """
        try:
            update_fields = []
            params = []

            if new_username:
                self.cursor.execute("SELECT id FROM users WHERE username = ? AND id != ?", (new_username, user_id))
                if self.cursor.fetchone():
                    return False, "نام کاربری جدید قبلاً توسط کاربر دیگری استفاده شده است." 
                update_fields.append("username = ?")
                params.append(new_username)
            
            if new_password:
                update_fields.append("password = ?")
                params.append(new_password)
            
            if new_phone:

                self.cursor.execute("SELECT id FROM users WHERE phone = ? AND id != ?", (new_phone, user_id))
                if self.cursor.fetchone():
                    return False, "شماره تلفن جدید قبلاً توسط کاربر دیگری استفاده شده است." 
                update_fields.append("phone = ?")
                params.append(new_phone)
            
            if new_profile_pic_path is not None: 
                update_fields.append("profile_pic_path = ?")
                params.append(new_profile_pic_path)

            if not update_fields:
                return False, "هیچ اطلاعاتی برای به روز رسانی ارائه نشده است." 
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
            params.append(user_id)

            self.cursor.execute(query, tuple(params))
            self.conn.commit()
            print(f"User ID {user_id} updated successfully.")
            return True, "اطلاعات با موفقیت به روز رسانی شد." 
        except sqlite3.Error as e:
            print(f"Error updating user info: {e}")
            return False, f"خطا در به روز رسانی اطلاعات: {e}" 

    def save_message(self, sender_id, receiver_id, message_text, timestamp=None):
        try:
            if timestamp:
                self.cursor.execute('''
                    INSERT INTO messages (sender_id, receiver_id, message_text, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (sender_id, receiver_id, message_text, timestamp))
            else:
                self.cursor.execute('''
                    INSERT INTO messages (sender_id, receiver_id, message_text)
                    VALUES (?, ?, ?)
                ''', (sender_id, receiver_id, message_text))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving message: {e}")
            return False
        
        
    def get_messages(self, user1_id, user2_id):
        try:
            self.cursor.execute("""
                SELECT sender_id, receiver_id, message_text, timestamp
                FROM messages
                WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
                ORDER BY timestamp
            """, (user1_id, user2_id, user2_id, user1_id))
            messages = []
            for row in self.cursor.fetchall():
                messages.append({
                    "sender_id": row[0],
                    "receiver_id": row[1],
                    "message_text": row[2],
                    "timestamp": row[3]
                })
            return messages
        except sqlite3.Error as e:
            print(f"Error getting messages: {e}")
            return []

    def close(self):
        if self.conn:
            self.conn.close()
            print("Database connection closed.")



