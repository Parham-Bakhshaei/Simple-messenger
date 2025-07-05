import socket
import json
from PyQt6.QtCore import QThread, pyqtSignal

class ClientThread(QThread):
    message_received = pyqtSignal(dict)  # Signal to emit received messages
    
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.client_socket = None
        self.running = False
        
    def run(self):
        self.running = True
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(('localhost', 5555))
            
            # Send login message
            login_message = {
                'type': 'login',
                'username': self.username
            }
            self.client_socket.send(json.dumps(login_message).encode('utf-8'))
            
            while self.running:
                try:
                    data = self.client_socket.recv(1024).decode('utf-8')
                    if not data:
                        break
                    
                    try:
                        message = json.loads(data)
                        if message['type'] == 'message':
                            self.message_received.emit(message)
                    except json.JSONDecodeError:
                        print("پیام نامعتبر از سرور دریافت شد")
                        
                except ConnectionResetError:
                    print("ارتباط با سرور قطع شد")
                    break
                
        except Exception as e:
            print(f"خطا در اتصال به سرور: {e}")
        finally:
            if self.client_socket:
                self.client_socket.close()
    
    def send_message(self, message_text, receiver):
        if self.client_socket and self.running:
            message = {
                'type': 'message',
                'receiver': receiver,
                'message': message_text
            }
            try:
                self.client_socket.send(json.dumps(message).encode('utf-8'))
            except Exception as e:
                print(f"خطا در ارسال پیام: {e}")
    
    def stop_client(self):
        self.running = False
        if self.client_socket:
            self.client_socket.close()