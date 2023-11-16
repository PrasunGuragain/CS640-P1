import socket
import sys
import struct
import random
import time
from queue import Queue

# this list will have a list that contains [packet, delay_time_started]
delayed_packets = []

def parse_request_packet():
    pass

def parse_packet(packet):
    priority = struct.unpack('B', packet[:1])[0]
    src_ip_address = socket.inet_ntoa(struct.unpack('4s', packet[1:5])[0])
    src_port = struct.unpack('H', packet[5:7])[0]
    dest_ip_address = socket.inet_ntoa(struct.unpack('4s', packet[7:11])[0])
    dest_port = struct.unpack('H', packet[11:13])[0]
    length = struct.unpack('I', packet[13:17])[0]

    # payload
    packet_type = struct.unpack('c', packet[17:18])[0]
    sequence_number = struct.unpack('I', packet[18:22])[0]
    # TODO: it is not reading payload_length correctly
    #payload_length = struct.unpack('I', packet[22:26])
    payload = packet[26:]
    payload_length = len(payload)

    return priority, src_ip_address, src_port, dest_ip_address, dest_port, length, packet_type, sequence_number, payload_length, payload

def log_event(log, message):
    with open(log, 'a') as file:
        file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
        
def send_helper():
     # 4. If a packet is currently being delayed and the delay has not expired, goto Step 1.
     
    # if a packet is currently being delayed
    if delayed_packets != []:
        for delayed in delayed_packets:
            # if delay has expired
            if time.time() - delayed[1] > delay / 1000:
                                        
                # send packet to next hop, drop if loss
                
                # get the packet infos
                current_packet = delayed[0]
                priority, src_ip_address, src_port, dest_ip_address, dest_port, length, packet_type, sequence_number, payload_length, payload = parse_packet(packet[0])
                
                next_hop_key = forwarding_table[(dest_ip_address, str(dest_port))][0]
                delay = forwarding_table[(dest_ip_address, str(dest_port))][1]
                loss_probability = forwarding_table[(dest_ip_address, str(dest_port))][2]
                
                # 7. Otherwise, send the packet to the proper next hop.
                if random.random() * 100 > loss_probability:
                    sock.sendto(current_packet, next_hop_key)
                    delayed_packets.remove(delayed)
                    
                    return
                else:
                    # 6. When the delay expires, randomly determine whether to drop the packet
                    message = "loss event occurred"
                    log_event(log, message)
                    
                    # remove packet from priority queue
                    priority_list[priority].get()
                    
                    return
    else:
        # 5. If no packet is currently being delayed
        
        # select the packet at the front of the queue with highest priority
        for priority in priority_list.keys():
            if not priority_list[priority].empty():
                highest_priority_packet = priority_list[priority].queue[0]
                
                # remove that packet from the queue
                priority_list[priority].get()
                
                # delay it
                delayed_packets.append( [highest_priority_packet, time.time()])
                
                break
        
'''
def send():
    for priority in priority_list.keys():
        if not priority_list[priority].empty():
            # get the next item in queue without removing it
            packet = priority_list[priority].queue[0]
            priority, src_ip_address, src_port, dest_ip_address, dest_port, length, packet_type, sequence_number, payload_length, payload = parse_packet(packet[0])

            # find next hop in fowarding table for dest_ip_address, dest_port
            next_hop_key = forwarding_table[(dest_ip_address, str(dest_port))][0]
            delay = forwarding_table[(dest_ip_address, str(dest_port))][1]
            loss_probability = forwarding_table[(dest_ip_address, str(dest_port))][2]

            # delay send

            # 4. If a packet is currently being delayed and the delay has not expired, goto Step 1.
            
            # if a packet is currently being delayed
            if delayed_packets != []:
                for delayed in delayed_packets:
                    
                    # if delay has expired
                    if time.time() - delayed[1] > delay / 1000:
                                                
                        # send packet to next hop, drop if loss
                        
                        # 7. Otherwise, send the packet to the proper next hop.
                        if random.random() * 100 > loss_probability:
                            sock.sendto(delayed[0], next_hop_key)
                            delayed_packets.remove(delayed)
                            return
                        else:
                            # 6. When the delay expires, randomly determine whether to drop the packet
                            message = "loss event occurred"
                            log_event(log, message)
                            
                            # remove packet from priority queue
                            priority_list[priority].get()
                            
                            return
            else:
                # 5. If no packet is currently being delayed, select the packet at the front of the queue with highest priority, remove that packet from the queue and delay it
                delayed_packets.append( [packet, time.time()])             
'''    

def routing(priority, src_ip_address, src_port, dest_ip_address, dest_port, length, packet_type, sequence_number, payload_length, payload, sock, log, filename,packet):
    dest_found = False
    
    # 2 Once you receive a packet, decide whether packet is to be forwarded by consulting the forwarding table
    if (dest_ip_address,str(dest_port)) in forwarding_table:
        
        # if packet is valid ie destination is found in fowarding table, then add it to priority queue
        get_current_time = time.time()
        packet_value = (packet, get_current_time)
        
        # This queue size is specified on the command line of the emulator startup. 
        # If a queue is full, the packet is dropped and this event is logged
        if priority_list[priority].full():
            message = "queue full"
            log_event(log, message)
        else:
            priority_list[priority].put(packet_value)
        
        # send(next_hop, delay, loss_probability, sock, log)
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
    filename = sys.argv[f + 1]
else:
    print("Filename argument (-f) is missing.")
    sys.exit(1)

# Log
if '-l' in sys.argv:
    l = sys.argv.index('-l')
    log = sys.argv[l + 1]
else:
    print("Log argument (-l) is missing.")
    sys.exit(1)

            
# Create a socket for the requester
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', port))

# set socket to non-blocking
sock.setblocking(False)

emulator_hostname = socket.gethostbyname(socket.gethostname())

# create a forwarding table: {(destination, d_port): [(next_hop, next_port), delay, loss_probability]}
forwarding_table = {}
with open(filename, 'r') as file:
    for line in file:
        columns = line.strip().split()
        emulator, e_port = columns[0:2]
        destination, d_port = columns[2:4]
        next_hop, next_port = columns[4:6]
        delay = columns[6]
        loss_probability = columns[7]
        
        if (emulator_hostname == emulator) and (str(port) == e_port):
            forwarding_table[(destination, d_port)] = [(next_hop, next_port), float(delay), float(loss_probability)]

priority_list = {1: Queue(maxsize = queue_size), 2: Queue(maxsize = queue_size), 3: Queue(maxsize = queue_size)}

while True:
    
    # Receive a packet
    try:
        # Receive packet from network in a non-blocking way. This means that you should not wait/get blocked in the recvfrom function until you get a packet. Check if you have received a packet; If not jump to 4,
        try:
            packet, addr = sock.recvfrom(5000)

            # Parse the packet
            priority, src_ip_address, src_port, dest_ip_address, dest_port, length, packet_type, sequence_number, payload_length, payload = parse_packet(packet)
            
            # setting up priority queues, decide where it is to be forwarded
            routing(priority, src_ip_address, src_port, dest_ip_address, dest_port, length, packet_type, sequence_number, payload_length, payload, sock, log, filename,packet)
            
            send_helper()
            
            '''
            for key, value in forwarding_table.items():
                destination, d_port = key
                next_hop, next_port = value[0]
                delay = value[1]
                loss_probability = value[2]
            
            # get all the values from the forwarding table
            next_hop_key = forwarding_table[(dest_ip_address, str(dest_port))][0]
            delay = forwarding_table[(dest_ip_address, str(dest_port))][1]
            loss_probability = forwarding_table[(dest_ip_address, str(dest_port))][2]
            '''
        except BlockingIOError:
            # Have not received a packet, 2.3 Forwarding Summary step 4
            # Check if there are delayed packets
            send_helper()
            
            '''
            if delayed_packets:
                current_time = time.time()
                
                # Check if a packet 
            next_hop_key = forwarding_table[(dest_ip_address, str(dest_port))][0]
            delay = forwarding_table[(dest_ip_address, str(dest_port))][1]
            loss_probability = forwarding_table[(dest_ip_address, str(dest_port))][2]
            
            send(next_hop_key, delay, loss_probability, log, packet)
            '''
            
    except KeyboardInterrupt:
            socket.close()
            sys.exit(0)
