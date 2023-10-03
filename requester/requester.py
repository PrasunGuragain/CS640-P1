import socket

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('localhost', 5001))
    
    data, sender_address = sock.socket.recvfrom(1024)
    
    print("Current data: ", data)