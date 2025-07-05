import socket
import threading

clients = {}

def handle_client(client_socket, addr):
    client_id = client_socket.recv(1024).decode('utf-8')
    clients[client_id] = client_socket
    print(f"[NEW CONNECTION] {client_id} connected from {addr}")
    
    broadcast(f"Server: {client_id} joined the chat!", None)
    
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break
                
            print(f"[{client_id}] {message}")
            broadcast(f"{client_id}: {message}", client_socket)
        except:
            break
            
    del clients[client_id]
    client_socket.close()
    broadcast(f"Server: {client_id} left the chat!", None)
    print(f"[DISCONNECTED] {client_id} disconnected")

def broadcast(message, sender_socket):
    for client_id, socket in clients.items():
        if socket != sender_socket:
            try:
                socket.send(message.encode('utf-8'))
            except:
                del clients[client_id]

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 5555))
    server.listen()
    print("[SERVER] Server is listening on port 5555...")
    
    while True:
        client_socket, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

if __name__ == "__main__":
    start_server()