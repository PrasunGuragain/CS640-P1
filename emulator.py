import socket
import sys
import struct
import random
import time

priority_list = {"1": [], "2": [], "3": []}

def log_event(log, message):
    with open(log, 'a') as file:
        file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def send(next_hop, delay, loss_probability, log):
    if random.random() * 100 > loss_probability:
        time.sleep(delay / 1000)
        
        # send packet to next hop since no loss
        
        
    else:
        message = "loss event occurred"
        log_event(log, message)
        pass
    
def routing(priority, src_ip_address, src_port, dest_ip_address, dest_port, length, packet_type, sequence_number, payload_length, payload, sock, log):
    dest_found = False
    with open("table.txt", 'r') as file:
        for line in file:
            columns = line.strip().split()
            emulator, e_port = columns[0:2]
            destination, d_port = columns[2:4]
            next_hop, next_port = columns[4:6]
            delay = columns[6]
            loss_probability = columns[7]
            
            if dest_port == d_port:
                send(next_hop, delay, loss_probability, sock, log)
                dest_found = True
                
    if not dest_found:
        message = "no forwarding entry found"
        log_event(log, message)

            
# PARSE COMMAND LINE ARGUMENTS
    
# Port
if '-p' in sys.argv:
    p = sys.argv.index('-p')
    port = int(sys.argv[p + 1])
    if port < 2049 and port > 65536:
        print("Sender port should be in this range: 2049 < port < 65536")
        sys.exit(1)
else:
    print("Port argument (-p) is missing.")
    sys.exit(1)
    
# Queue size
if '-q' in sys.argv:
    q = sys.argv.index('-q')
    queue_size = int(sys.argv[q + 1])
else:
    print("Queue size argument (-q) is missing.")
    sys.exit(1)

# Filename
if '-f' in sys.argv:
    f = sys.argv.index('-f')
    filename = int(sys.argv[f + 1])
else:
    print("Filename argument (-f) is missing.")
    sys.exit(1)

# Log
if '-l' in sys.argv:
    l = sys.argv.index('-l')
    log = int(sys.argv[l + 1])
else:
    print("Log argument (-l) is missing.")
    sys.exit(1)

# Create a socket for the requester
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', port))

# Receive a packet
packet, addr = sock.recvfrom(5000)

priority = struct.unpack('B', packet[:1])
src_ip_address = struct.unpack('4s', packet[1:5])
src_port = struct.unpack('H', packet[5:7])
dest_ip_address = struct.unpack('4s', packet[7:11])
dest_port = struct.unpack('H', packet[11:13])
length = struct.unpack('I', packet[13:17])

# payload
packet_type = struct.unpack('c', packet[17:18])
sequence_number = struct.unpack('I', packet[18:22])
payload_length = struct.unpack('I', packet[22:26])
payload = packet[26:26 + payload_length]

# Decide where it is to be forwarded
routing(priority, src_ip_address, src_port, dest_ip_address, dest_port, length, packet_type, sequence_number, payload_length, payload, sock, log)
send()


