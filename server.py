import socket
import threading
import json
from datetime import datetime
import sqlite3
from queue import Queue

class Server:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen()
        
        self.clients = {}  # {username: {'socket': socket, 'address': address}}
        self.message_queue = Queue()
        
        self.db_conn = sqlite3.connect('messenger.db', check_same_thread=False)
        self.init_db()
        
        print(f"سرور در حال اجرا روی {self.host}:{self.port}...")
        
        # Start queue processing thread
        threading.Thread(target=self.process_message_queue, daemon=True).start()

    def init_db(self):
        cursor = self.db_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                receiver TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.db_conn.commit()

    def save_message(self, sender, receiver, message):
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO messages (sender, receiver, message)
                VALUES (?, ?, ?)
            ''', (sender, receiver, message))
            self.db_conn.commit()
            return True
        except Exception as e:
            print(f"خطا در ذخیره پیام: {e}")
            return False

    def broadcast(self, sender, receiver, message):
        # Save to database first
        self.save_message(sender, receiver, message)
        
        # Prepare message data
        message_data = {
            'type': 'message',
            'sender': sender,
            'receiver': receiver,
            'message': message,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add to queue for processing
        self.message_queue.put(message_data)

    def process_message_queue(self):
        while True:
            message_data = self.message_queue.get()
            
            # Send to receiver if online
            if message_data['receiver'] in self.clients:
                receiver_socket = self.clients[message_data['receiver']]['socket']
                try:
                    receiver_socket.send(json.dumps(message_data).encode('utf-8'))
                except:
                    print(f"ارسال پیام به {message_data['receiver']} ناموفق بود")
            
            # Also send back to sender for their own display
            if message_data['sender'] in self.clients:
                sender_socket = self.clients[message_data['sender']]['socket']
                try:
                    sender_socket.send(json.dumps(message_data).encode('utf-8'))
                except:
                    print(f"ارسال پیام به {message_data['sender']} ناموفق بود")
            
            self.message_queue.task_done()

    def handle_client(self, client_socket, address):
        username = None
        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                try:
                    message = json.loads(data)
                    
                    if message['type'] == 'login':
                        username = message['username']
                        self.clients[username] = {'socket': client_socket, 'address': address}
                        print(f"{username} متصل شد")
                        
                        # Send login success
                        response = {'type': 'login_success', 'message': 'با موفقیت وارد شدید'}
                        client_socket.send(json.dumps(response).encode('utf-8'))
                        
                    elif message['type'] == 'message':
                        if username and 'receiver' in message and 'message' in message:
                            self.broadcast(username, message['receiver'], message['message'])
                    
                except json.JSONDecodeError:
                    print("پیام نامعتبر دریافت شد")
                    
        except ConnectionResetError:
            print("ارتباط با کلاینت قطع شد")
        finally:
            if username and username in self.clients:
                del self.clients[username]
                print(f"{username} قطع شد")
            client_socket.close()

    def run(self):
        try:
            while True:
                client_socket, address = self.server.accept()
                thread = threading.Thread(target=self.handle_client, args=(client_socket, address))
                thread.start()
        except KeyboardInterrupt:
            print("در حال خاموش کردن سرور...")
            self.server.close()
            self.db_conn.close()

if __name__ == "__main__":
    server = Server()
    server.run()