import socket
import json
from PyQt6.QtCore import QThread, pyqtSignal

class ClientThread(QThread):
    message_received = pyqtSignal(dict)  
    
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
                        print("Bad request")
                        
                except ConnectionResetError:
                    print("Disconnected")
                    break
                
        except Exception as e:
            print(f"Error {e}")
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
            self.client_socket.send(json.dumps(message).encode('utf-8'))

    
    def stop_client(self):
        self.running = False
        if self.client_socket:
            self.client_socket.close()