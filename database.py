import sqlite3
import os

# Define the base directory for storing database and profile pictures
# This ensures the database and profile pictures are stored relative to the script location.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, 'messenger.db') # Database file path

class DatabaseManager:
    """
    Handles all database operations for the messenger application.
    Uses SQLite for data storage.
    """
    def __init__(self):
        """
        Initializes the database connection and creates necessary tables if they don't exist.
        """
        self.conn = None
        self.connect()
        self.create_tables()

    def connect(self):
        """
        Establishes a connection to the SQLite database.
        If a connection already exists, it will be closed first.
        """
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
            # Users table: id, username, password, phone, profile_pic_path
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    phone TEXT UNIQUE NOT NULL,
                    profile_pic_path TEXT
                )
            ''')
            # Messages table: id, sender_id, receiver_id, message_text, timestamp
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
        """
        Registers a new user in the database.
        Returns True on success, False if username or phone already exists, or on other errors.
        """
        try:
            # Check if username or phone already exists
            self.cursor.execute("SELECT id FROM users WHERE username = ? OR phone = ?", (username, phone))
            if self.cursor.fetchone():
                return False, "نام کاربری یا شماره تلفن قبلاً استفاده شده است." # Username or phone already taken
            
            self.cursor.execute("INSERT INTO users (username, password, phone) VALUES (?, ?, ?)",
                                (username, password, phone))
            self.conn.commit()
            print(f"User '{username}' registered successfully.")
            return True, "ثبت نام با موفقیت انجام شد." # Registration successful
        except sqlite3.Error as e:
            print(f"Error registering user: {e}")
            return False, f"خطا در ثبت نام: {e}" # Error during registration

    def authenticate_user(self, username, password):
        """
        Authenticates a user based on username and password.
        Returns the user's ID if authentication is successful, otherwise None.
        """
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
        """
        Retrieves user information by ID, username, or phone number.
        Returns a dictionary of user data if found, otherwise None.
        """
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
                # Check if new username is already taken by another user
                self.cursor.execute("SELECT id FROM users WHERE username = ? AND id != ?", (new_username, user_id))
                if self.cursor.fetchone():
                    return False, "نام کاربری جدید قبلاً توسط کاربر دیگری استفاده شده است." # New username already taken
                update_fields.append("username = ?")
                params.append(new_username)
            
            if new_password:
                update_fields.append("password = ?")
                params.append(new_password)
            
            if new_phone:
                # Check if new phone is already taken by another user
                self.cursor.execute("SELECT id FROM users WHERE phone = ? AND id != ?", (new_phone, user_id))
                if self.cursor.fetchone():
                    return False, "شماره تلفن جدید قبلاً توسط کاربر دیگری استفاده شده است." # New phone already taken
                update_fields.append("phone = ?")
                params.append(new_phone)
            
            if new_profile_pic_path is not None: # Allow setting to None (e.g., if user removes pic)
                update_fields.append("profile_pic_path = ?")
                params.append(new_profile_pic_path)

            if not update_fields:
                return False, "هیچ اطلاعاتی برای به روز رسانی ارائه نشده است." # No data to update

            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
            params.append(user_id)

            self.cursor.execute(query, tuple(params))
            self.conn.commit()
            print(f"User ID {user_id} updated successfully.")
            return True, "اطلاعات با موفقیت به روز رسانی شد." # Information updated successfully
        except sqlite3.Error as e:
            print(f"Error updating user info: {e}")
            return False, f"خطا در به روز رسانی اطلاعات: {e}" # Error updating information

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
        """
        Retrieves all messages between two users, ordered by timestamp.
        Returns a list of dictionaries, each representing a message.
        """
        try:
            # Messages sent from user1 to user2 OR from user2 to user1
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
        """
        Closes the database connection.
        """
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

# Example usage (for testing the database manager independently)
if __name__ == "__main__":
    db_manager = DatabaseManager()

    # Test registration
    print("\n--- Testing Registration ---")
    success, msg = db_manager.register_user("roham", "12345", "09123456789")
    print(f"Registration roham: {msg}")
    success, msg = db_manager.register_user("parsas", "54321", "09129876543")
    print(f"Registration parsa: {msg}")
    success, msg = db_manager.register_user("roham", "password", "09121112233") # Should fail (duplicate username)
    print(f"Registration roham (duplicate username): {msg}")
    success, msg = db_manager.register_user("arian", "pass", "09123456789") # Should fail (duplicate phone)
    print(f"Registration arian (duplicate phone): {msg}")

    # Test authentication
    print("\n--- Testing Authentication ---")
    user_roham = db_manager.authenticate_user("roham", "12345")
    if user_roham:
        print(f"Authenticated Roham: {user_roham}")
    else:
        print("Roham authentication failed.")
    
    user_invalid = db_manager.authenticate_user("roham", "wrongpass")
    if user_invalid:
        print(f"Authenticated Invalid User: {user_invalid}")
    else:
        print("Invalid user authentication failed.")

    # Test get user info
    print("\n--- Testing Get User Info ---")
    if user_roham:
        roham_info_by_id = db_manager.get_user_info(user_id=user_roham['id'])
        print(f"Roham info by ID: {roham_info_by_id}")
        roham_info_by_username = db_manager.get_user_info(username="roham")
        print(f"Roham info by username: {roham_info_by_username}")

    # Test update user info
    print("\n--- Testing Update User Info ---")
    if user_roham:
        success, msg = db_manager.update_user_info(user_roham['id'], new_username="roham_new", new_phone="09120000000")
        print(f"Update Roham (username and phone): {msg}")
        roham_updated_info = db_manager.get_user_info(user_id=user_roham['id'])
        print(f"Roham updated info: {roham_updated_info}")

        # Try to update with existing username/phone
        user_parsas = db_manager.authenticate_user("parsas", "54321")
        if user_parsas:
            success, msg = db_manager.update_user_info(user_roham['id'], new_username="parsas") # Should fail
            print(f"Update Roham (username to parsas): {msg}")
            success, msg = db_manager.update_user_info(user_roham['id'], new_phone="09129876543") # Should fail
            print(f"Update Roham (phone to parsas's phone): {msg}")

    # Test messages (need at least two users)
    print("\n--- Testing Messages ---")
    user_roham_reauth = db_manager.authenticate_user("roham_new", "12345") # Re-authenticate after username change
    user_parsas = db_manager.authenticate_user("parsas", "54321")

    if user_roham_reauth and user_parsas:
        db_manager.save_message(user_roham_reauth['id'], user_parsas['id'], "سلام پارسا، چه خبر؟")
        db_manager.save_message(user_parsas['id'], user_roham_reauth['id'], "سلام روهام، خوبم، تو چطوری؟")
        db_manager.save_message(user_roham_reauth['id'], user_parsas['id'], "من دارم روی پروژه پایان ترم کار میکنم.")

        chat_history = db_manager.get_messages(user_roham_reauth['id'], user_parsas['id'])
        print("\nChat History between Roham and Parsa:")
        for msg in chat_history:
            sender_info = db_manager.get_user_info(user_id=msg['sender_id'])
            receiver_info = db_manager.get_user_info(user_id=msg['receiver_id'])
            print(f"[{msg['timestamp']}] {sender_info['username']} -> {receiver_info['username']}: {msg['message_text']}")

    db_manager.close()
