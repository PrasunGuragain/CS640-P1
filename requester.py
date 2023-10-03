import socket

def main():
    print("In main")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('localhost', 5001))
    
    data, sender_address = sock.recvfrom(1024)
    
    print("Current data: ", data)

print("Before main")
main()